import json
import json
import requests
import argparse
from typing import Dict, List, Optional, Any, Iterator
from datetime import datetime
import logging
import os
import pandas as pd
from tqdm import tqdm
import re
import difflib
import json
import os
from datasets import load_dataset
from tree_sitter import Language, Parser
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
C_LANGUAGE = Language(tsc.language())
CPP_LANGUAGE = Language(tscpp.language())

class DeepSeekAPI:
    """DeepSeek API client."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        Initialize the DeepSeek API client.

        Args:
            api_key: API key; if None, read from env DEEPSEEK_API_KEY.
            base_url: API base URL.
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Set DEEPSEEK_API_KEY or pass api_key.")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def extract_json(self, text: str) -> Optional[Dict]:
        return json.loads(re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip())

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call the DeepSeek chat completion API.

        Args:
            messages: Message list, e.g. [{"role": "user", "content": "..."}].
            model: Model name.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Max tokens to generate.
            stream: Whether to stream the response.
            **kwargs: Other arguments.

        Returns:
            API response dict.
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            **kwargs
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            print(f"Calling DeepSeek API, model: {model}")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            if stream:
                return self._handle_stream_response(response)
            else:
                result = response.json()
                print(f"API call succeeded, tokens used: {result.get('usage', {}).get('total_tokens', 'N/A')}")
                return result

        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}, body: {e.response.text}")
            raise
    
    def _handle_stream_response(self, response: requests.Response) -> Iterator[Dict[str, Any]]:
        """Handle stream response; yield chunks."""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse stream chunk: {e}, raw: {data}")
                        continue

    def get_models(self) -> Dict[str, Any]:
        """Get list of available models."""
        url = f"{self.base_url}/models"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get model list: {e}")
            raise

    def get_usage(self) -> Dict[str, Any]:
        """Get API usage (if supported)."""
        url = f"{self.base_url}/usage"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get usage: {e}")
            raise

def build_prompt(target_code, cve_id, cwe_id):
    system_prompt = """
    You are an expert in identifying security vulnerabilities that extracts API calls from a code snippet.
    You will be given a code snippet and you need to extract the API calls from the code snippet.
    For example, the code snippet provided below contains a CWE-22 vulnerability:
    ```cpp
    char path[256];
    sprintf(path, "%s/%s", baseDir, userInput);
    FILE* f = fopen(path, "r");
    ```
    Then the pivotal API calls for this vulnerability and the related API calls you need to respond to will be:
    ```json
    ["fopen"]
    ```
    For another example, the code snippet provided below contains a CWE-119 vulnerability:
    ```cpp
    char dest[10];
    memcpy(dest, source, length);
    ```
    Then the pivotal API calls for this vulnerability and the related API calls you need to respond to will be:
    ```json
    ["memcpy"]
    ```

    **REMEMBER:**
    - DO NOT add any Markdown format like ```json ```
    - DO NOT add any additional text outside the JSON object.
    - DO NOT include any explanations, notes, or comments outside the JSON object.
    - Your output must strictly follow the JSON format provided above.
    - Your should escape all special characters in the JSON object correctly, e.g., '"' should be escaped as '\\"'
    """
    user_prompt = f"""
    The code snippet provided contains a {cve_id} {cwe_id} vulnerability.
    Please extract the pivotal API calls from the code snippet.
    Code snippet:
    ```cpp
    {target_code}
    ```
    Return **only** the API calls list—no additional text or commentary.
    If the code snippet does not contain any API calls, return an empty list.
    """
    return system_prompt, user_prompt


def llm_based_extract_api(target_code, cve_id, cwe_id):
    system_prompt, user_prompt = build_prompt(target_code, cve_id, cwe_id)
    api_client = DeepSeekAPI(api_key=os.getenv("DEEPSEEK_API_KEY"))
    response = api_client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="deepseek-chat"
    )
    api_calls = api_client.extract_json(response['choices'][0]['message']['content'])
    return api_calls

def get_function_name(code, language_obj):
    """
    Extract function name from code using tree-sitter.
    """
    if not code:
        return ""
    parser = Parser(language_obj)
    tree = parser.parse(bytes(code, "utf8"))
    
    def find_name_node(node):
        if node.type == 'function_declarator':
            curr = node.child_by_field_name('declarator')
            while curr:
                if curr.type in ['identifier', 'field_identifier', 'destructor_name', 'operator_name']:
                    return curr
                if curr.type == 'scoped_identifier':
                    name_node = curr.child_by_field_name('name')
                    if name_node:
                        curr = name_node
                        continue
                if curr.type == 'template_method':
                    name_node = curr.child_by_field_name('name')
                    if name_node:
                        curr = name_node
                        continue
                next_node = curr.child_by_field_name('declarator')
                if not next_node: break
                curr = next_node
            return curr
            
        for child in node.children:
            res = find_name_node(child)
            if res: return res
        return None

    name_node = find_name_node(tree.root_node)
    if name_node:
        return code[name_node.start_byte:name_node.end_byte].strip()
    return ""

if __name__ == "__main__":
    print("Loading dataset...")
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(_SCRIPT_DIR, "PrimeVul", "primevul_test_paired.jsonl"), "r") as f:
        dataset = [json.loads(line) for line in f]
    with open(os.path.join(_SCRIPT_DIR, "PrimeVul", "file_info.json"), "r") as f:
        file_info = json.load(f)
    
    new_dataset = []
    for item in tqdm(dataset, total=len(dataset), desc="Processing dataset"):
        try:
            idx = item.get("idx", "")
            project_url = item.get("project_url", "")
            project_name = project_url.split("/")[-1]
            commit_id = item.get("commit_id", "")
            commit_url = item.get("commit_url", "")
            func_hash = item.get("func_hash", "")
            file_path = file_info.get(str(func_hash), {}).get("project_file_path", "")
            target_code = item.get("func", "")
            cwe = item.get("cwe", "")
            cve = item.get("cve", "")
            label = "vul" if item.get("target", "") == 1 else "fix"
            if not all([idx, project_url, project_name, commit_id, func_hash, file_path, target_code, cwe, cve]):
                continue

            if not commit_url.startswith("https://github.com/") or "/commit/" not in commit_url:
                continue
            commit_url = commit_url.split("#diff")[0]
            if label == "vul":
                commit_id = commit_id + "^"
            if file_path.endswith(".c"):
                function_name = get_function_name(target_code, C_LANGUAGE)
            else:
                function_name = get_function_name(target_code, CPP_LANGUAGE)
            target_api_name = llm_based_extract_api(target_code, cve, cwe)
            if not isinstance(target_api_name, list):
                continue
            new_item = {}
            new_item["idx"] = idx
            new_item["project_url"] = project_url
            new_item["project_name"] = project_name
            new_item["commit_url"] = commit_url
            new_item["commit_id"] = commit_id
            new_item["method_name"] = f"{file_path}#{function_name}"
            new_item["target_code"] = target_code
            new_item["CWE_id"] = cwe
            new_item["CVE_id"] = cve
            new_item["is_vulnerable"] = True if label == "vul" else False
            new_item["need_head_slicing"] = False if target_api_name else True
            new_item["target_api_name"] = target_api_name
            new_dataset.append(new_item)
        except Exception as e:
            print(f"Error {e}")
            continue
    with open(os.path.join(_SCRIPT_DIR, "primevul_test_formatted.json"), "w") as f:
        json.dump(new_dataset, f, indent=4, ensure_ascii=False)