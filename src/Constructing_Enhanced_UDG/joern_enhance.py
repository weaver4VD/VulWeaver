from __future__ import annotations

from math import e
import re
import ast
import copy
import os
import subprocess
import sys
from typing import Any
from xmlrpc.client import boolean

import networkx as nx

from . import common
from . import joern_node
from .common import Language
import requests
from typing import List, Set, Dict, Tuple, Optional, Any
import json
from Constructing_Enhanced_UDG.code2neo4jcsv2dot import neo4jcsv_to_dot
from tqdm import tqdm
from .parallel_edges import build_call_edges_parallel, add_global_variables_to_code
from .ast_parser import ASTParser
from collections import defaultdict, deque
from Holistic_Context_Extraction.project import Method, Project
import json


JOERN_PATH = os.getenv("JOERN_PATH")

def set_joern_env(joern_path: str):
    os.environ["PATH"] = joern_path + os.pathsep + os.environ["PATH"]
    assert (
        subprocess.run(["which", "joern"], stdout=subprocess.PIPE)
        .stdout.decode()
        .strip()
        == joern_path + "/joern"
    )
    os.environ["JOERN_HOME"] = joern_path

current_dir = os.path.dirname(os.path.abspath(__file__))
_joern_scripts_dir = os.path.join(current_dir, "scripts")
class DeepSeekAPI:
    """DeepSeek API client"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        Initialize DeepSeek API client.

        Args:
            api_key: API key; if None, read from env DEEPSEEK_API_KEY
            base_url: API base URL
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided; set DEEPSEEK_API_KEY env or pass api_key")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call DeepSeek chat completion API.

        Args:
            messages: Message list, e.g. [{"role": "user", "content": "..."}]
            model: Model name
            temperature: Temperature for randomness
            max_tokens: Max tokens to generate
            stream: Whether to stream output
            **kwargs: Other arguments

        Returns:
            API response dict
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        try:
            print(f"Calling DeepSeek API, model: {model}")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            raise
    
    def _handle_stream_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle streamed response"""
        result = {"choices": [], "usage": None}
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk:
                            result['choices'].extend(chunk['choices'])
                        if 'usage' in chunk:
                            result['usage'] = chunk['usage']
                    except json.JSONDecodeError:
                        continue
        
        return result
    
    def get_models(self) -> Dict[str, Any]:
        """Get available model list"""
        url = f"{self.base_url}/v1/models"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get model list: {e}")
            raise

def set_joern_env(joern_path: str):
    os.environ["PATH"] = joern_path + os.pathsep + os.environ["PATH"]
    assert (
        subprocess.run(["which", "joern"], stdout=subprocess.PIPE)
        .stdout.decode()
        .strip()
        == joern_path + "/joern"
    )
    os.environ["JOERN_HOME"] = joern_path

def export(
    code_path: str, output_path: str, language: Language, overwrite: bool = False
):
    pdg_dir = os.path.join(output_path, "pdg")
    cfg_dir = os.path.join(output_path, "cfg")
    cpg_dir = os.path.join(output_path, "cpg")
    cpg_bin = os.path.join(output_path, "cpg.bin")
    if (
        os.path.exists(pdg_dir)
        and os.path.exists(cfg_dir)
        and os.path.exists(cpg_dir)
        and not overwrite
    ):
        cpg = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
        return cpg
    else:
        if os.path.exists(pdg_dir):
            subprocess.run(["rm", "-rf", pdg_dir])
        if os.path.exists(cfg_dir):
            subprocess.run(["rm", "-rf", cfg_dir])
        if os.path.exists(cpg_bin):
            subprocess.run(["rm", "-rf", cpg_bin])
    subprocess.run(
        ["joern-parse", "--language", language.value, os.path.abspath(code_path)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["joern-export", "--repr", "cfg", "--out", os.path.abspath(cfg_dir)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["joern-export", "--repr", "pdg", "--out", os.path.abspath(pdg_dir)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run([
        "joern-export",
        cpg_bin,
        "--repr=all",
        "--format=neo4jcsv",
        f"--out={os.path.abspath(cpg_dir)}"
    ], check=True)



def generate_callcite_prompt_reflect(func_a: str, func_list: str):
    system_prompt = """
        You are an expert in static code analysis, specializing in identifying Java reflection API usages and their real callees.
        - Input:  
        1. “Current function context”: the full Java code of a single function (provided below).  
        2. “Project function list”: a complete list of all constructors and methods in the project, given as full signatures (provided below).  
        - Task:  
        1. In the provided function context, find every invocation made via the Java Reflection API (e.g. Class.getConstructor, Constructor.newInstance, Field.get, Method.invoke, etc.).  
        2. For each such reflection call, resolve which actual function (constructor or method) is being executed.  
        3. Output a JSON array where each element is an object with two properties:  
            - `"caller"`: the reflection API call (including class and method name),  
            - `"callee"`: the exact target function signature as listed in the project function list.  
        4. Return **only** the JSON array—no additional text or commentary.
        ```
        Remember:
        - DO NOT add any Markdown format like ```json ```
        - DO NOT add any additional text outside the JSON object.
        - DO NOT include any explanations, notes, or comments outside the JSON object.
        Your output must strictly follow the JSON format provided above.
    """
        
    user_prompt = f"""
    Here are function contexts and the function name list in this project. Please infer any missing call relationship between them:

    —— Current function context: ——  
    {func_a}

    —— Project function list: ——  
    {func_list}

    Return your answer as the JSON structure specified by the system prompt.
    """

    return system_prompt, user_prompt

def generate_callcite_prompt_polymorphic(func_a: str, func_list: str, line_code:str):
    system_prompt = f"""
        You are an expert in object-oriented static analysis and polymorphic call resolution.
        - Input:  
        1. “Current function context”: the full Java code of a single function (provided below).  
        2. “Oriented function list”: an oriented function list of all constructors and methods in the project which is the polymorphic type of the current function, given as full signatures (provided below).  
        - Task:  
        1. In the provided function context, find the polymorphic call at the line {line_code}.  
        2. Resolve which actual function (constructor or method) is being executed. 
        3. If the callee is a constructor, you need to resolve the actual constructor signature.
        4. Output a JSON array where each element is an object with two properties:  
            - `"caller"`: the polymorphic call (including class and method name),  
            - `"callee"`: the exact target function signature as listed in the oriented function list.  
        5. Return **only** the JSON array—no additional text or commentary.
        ```
        Remember:
        - DO NOT add any Markdown format like ```json ```
        - DO NOT add any additional text outside the JSON object.
        - DO NOT include any explanations, notes, or comments outside the JSON object.
        Your output must strictly follow the JSON format provided above.
    """
        
    user_prompt = f"""
    Here are function contexts and the function name list in this project. Please infer any missing call relationship between them:

    —— Current function context: ——  
    {func_a}

    —— Project function list: ——  
    {func_list}

    Return your answer as the JSON structure specified by the system prompt.
    """

    return system_prompt, user_prompt

def get_callgraph(func_a: str, func_list: str, reflect: bool=True, line_code:str=None):
    """
    Call LLM to get call graph and record token usage (joern_enhance version).

    Returns:
        str: Call graph JSON string, or None on failure
    """
    from .parallel_edges import _record_token_usage
    
    if reflect:
        system_prompt, user_prompt = generate_callcite_prompt_reflect(func_a, func_list)
    else:
        system_prompt, user_prompt = generate_callcite_prompt_polymorphic(func_a, func_list, line_code)
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_client = DeepSeekAPI(api_key=api_key)
        response = api_client.chat_completion(
                messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
                ],
                model="deepseek-chat"
            )
        if 'usage' in response:
            usage = response['usage']
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            _record_token_usage(prompt_tokens, completion_tokens, total_tokens)
        callcite_json = response['choices'][0]['message']['content'].strip()
        
        return callcite_json
        
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


def get_types(cpg_dir: str):
    inherent_types = {}
    deinherent_types = {}
    if os.path.exists(os.path.join(cpg_dir, "types.json")):
        with open(os.path.join(cpg_dir, "types.json"), "r") as f:
            types = json.load(f)
    else:
        cpg_bin = os.path.abspath(os.path.join(os.path.dirname(cpg_dir), "cpg.bin"))
        script_path = os.path.join(_joern_scripts_dir, "get_types.sc")
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"joern script not found: {script_path}")
        process = subprocess.Popen(
            ["joern", "--script", script_path, "--param", f"cpgFile={cpg_bin}", "--param", "output=types.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cpg_dir,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"joern get_types failed (returncode={process.returncode})\nstderr: {stderr}\nstdout: {stdout}")
            raise RuntimeError(f"joern get_types failed: {stderr or stdout}")
        with open(os.path.join(cpg_dir, "types.json"), "r") as f:
            types = json.load(f)

    for type in types:
        if type["inheritsFromTypeFullName"] == []:
            continue
        else:
            if len(type["inheritsFromTypeFullName"]) == 1:
                if type["inheritsFromTypeFullName"][0] == "java.lang.Object":
                    continue
                else:
                    inherent_types[type["fullName"]] = type["inheritsFromTypeFullName"][0]
                try:
                    deinherent_types[type["inheritsFromTypeFullName"][0]].append(type["fullName"])
                except:
                    deinherent_types[type["inheritsFromTypeFullName"][0]] = [type["fullName"]]
            else:
                for inherit_type in type["inheritsFromTypeFullName"]:
                    if inherit_type == "java.lang.Object":
                        continue
                    else:
                        inherent_types[type["fullName"]] = inherit_type
                    try:
                        deinherent_types[inherit_type].append(type["fullName"])
                    except:
                        deinherent_types[inherit_type] = [type["fullName"]]

    return inherent_types, deinherent_types

def get_callgraph_from_joern(cpg_dir: str):
    if os.path.exists(os.path.join(cpg_dir, "callgraph.json")):
        with open(os.path.join(cpg_dir, "callgraph.json"), "r") as f:
            callgraph = json.load(f)
    else:
        cpg_bin = os.path.abspath(os.path.join(os.path.dirname(cpg_dir), "cpg.bin"))
        script_path = os.path.join(_joern_scripts_dir, "get_callgraph.sc")
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"joern script not found: {script_path}")
        process = subprocess.Popen(
            ["joern", "--script", script_path, "--param", f"cpgFile={cpg_bin}", "--param", "output=callgraph.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cpg_dir,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"joern get_callgraph failed (returncode={process.returncode})\nstderr: {stderr}\nstdout: {stdout}")
            raise RuntimeError(f"joern get_callgraph failed: {stderr or stdout}")
        with open(os.path.join(cpg_dir, "callgraph.json"), "r") as f:
            callgraph = json.load(f)
    return callgraph

def preprocess(cache_dir: str, max_workers: int) -> Dict[str, Any]:
    import gc
    from .joern import load_cpg_method_nodes
    cpg_dir = os.path.join(cache_dir, "cpg")
    csv_exists = any(f.startswith("nodes_") for f in os.listdir(cpg_dir))
    if csv_exists:
        nodes_data = load_cpg_method_nodes(cpg_dir)
        cpg_nodes_iterator = nodes_data.items()
    else:
        cpg = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
        cpg_nodes_iterator = cpg.nodes(data=True)
    call_graph = nx.MultiDiGraph()
    methods = {}
    calls = {}
    
    method_list = []
    method_name_dict = defaultdict[Any, list](list)
    methods_full_name = {}
    for node_id, node_attrs in cpg_nodes_iterator:
        label = node_attrs.get("label") or node_attrs.get("LABEL") or ""
        
        if label == "METHOD":
            method_name = node_attrs.get("NAME", "unknown_method")
            full_name = node_attrs.get("FULL_NAME", method_name)
            signature = node_attrs.get("SIGNATURE", "")
            if "<operator>" not in str(full_name):
                methods[node_id] = {
                    "name": method_name,
                    "full_name": full_name,
                    "sub_full_name": ".".join(str(full_name).split(":")[0].split(".")[:-2]) + "." + str(method_name),
                    "signature": signature,
                    "start_line": int(node_attrs.get("LINE_NUMBER", 0)),
                    "end_line": int(node_attrs.get("LINE_NUMBER_END", node_attrs.get("LINE_NUMBER", 0))),
                    "file_name": node_attrs.get("FILENAME", ""),
                    "is_external": node_attrs.get("IS_EXTERNAL", False)
                }
                if methods[node_id]["file_name"] != "<empty>":
                    methods_full_name[methods[node_id]["sub_full_name"]] = methods[node_id]
                
                method_list.append(full_name)
                call_graph.add_node(full_name, label=node_id, type="METHOD")

                if method_name == "<init>":
                    match = re.search(r'(?:^|[$.])([A-Za-z_]\w*)(?=\.<init>)', str(full_name))
                    if match:
                        method_name_dict[match.group(1)].append(methods[node_id])
                    else:
                        fname = str(node_attrs.get("FILENAME", ""))
                        method_name_dict[fname.split(".java")[0].split("/")[-1]].append(methods[node_id])
                else:
                    method_name_dict[method_name].append(methods[node_id])
    if csv_exists:
        del nodes_data
    else:
        del cpg
    gc.collect()

    for method in methods:
        if methods[method]["file_name"] == "<empty>" and methods[method]["sub_full_name"] in methods_full_name:
            full_name = methods[method]["full_name"]
            class_name = "/".join(str(full_name).split(":")[0].split(".")[:-1])
            if os.path.exists(os.path.join(cache_dir, "code", class_name + ".java")):
                methods[method]["file_name"] = os.path.join(cache_dir, "code", class_name + ".java")
                continue
            methods[method] = methods_full_name[methods[method]["sub_full_name"]].copy()
            methods[method]["full_name"] = full_name

    callgraph = get_callgraph_from_joern(cpg_dir)
    
    method_file_name = f"{cpg_dir}/method.json"
    with open(method_file_name, "w") as f:
        json.dump(methods, f, indent=4)
    
    for method_id_str, method_calls in callgraph.items():
        if method_id_str not in methods:
            continue
        for call in method_calls:
            if "lineNumber" not in call:
                continue
            if "<operator>" in str(call.get('methodFullName', '')):
                continue
            
            call_id = str(call.get('_id') or call.get('id'))
            calls[call_id] = {
                "name": str(call.get('name')),
                "callee_method_full_name": str(call.get('methodFullName')),
                "method_full_name": str(methods[method_id_str]["full_name"]),
                "line_number": str(call.get('lineNumber')),
                "start_line": str(methods[method_id_str]['start_line']),
                "end_line": str(methods[method_id_str]['end_line']),
                "file_name": str(methods[method_id_str]["file_name"]),
            }

    call_file_name = f"{cpg_dir}/call.json"
    with open(call_file_name, "w") as f:
        json.dump(calls, f, indent=4)
    if csv_exists:
        from .joern import load_cpg_edges
        edges_list = load_cpg_edges(cpg_dir)
    else:
        cpg_for_edges = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
        edges_list = list(cpg_for_edges.edges(data=True))
    
    edges_to_add, method_name_dict_updates = build_call_edges_parallel(
        edges=edges_list,
        methods=methods,
        calls=calls,
        code_dir=os.path.join(cache_dir, "code"),
        max_workers=max_workers,
        chunk=512,
    )

    for method_name, m_list in method_name_dict_updates.items():
        method_name_dict[method_name].extend(m_list)

    with open(os.path.join(cpg_dir, "method_name_dict.json"), "w") as f:
        json.dump(dict(method_name_dict), f, indent=4)

    for u, v, line in edges_to_add:
        if call_graph.has_node(u) and call_graph.has_node(v) and u != v:
            call_graph.add_edge(u, v, label=line)
    
    dot_output = generate_dot_format(call_graph)
    output_file = os.path.join(cache_dir, "call_graph.dot")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dot_output)
    del call_graph
    del methods
    del methods_full_name
    del method_name_dict
    gc.collect()

    return calls


def generate_dot_format(graph):
    """Generate DOT format for NetworkX graph"""
    
    def escape_dot_string(s):
        """Escape special characters in DOT format string"""
        if not s:
            return ""
        s = str(s).replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s
    
    lines = ["digraph CallGraph {", "    rankdir=TB;", "    node [shape=box, style=rounded];", ""]
    for node in graph.nodes:
        node_data = graph.nodes[node]
        node_id = node_data.get('label', node)
        signature = node_data.get('signature', '')
        escaped_node = escape_dot_string(node)
        escaped_node_id = escape_dot_string(node_id)
        if signature:
            clean_sig = escape_dot_string(signature[:50])
            lines.append(f'    "{escaped_node}" [label="{escaped_node_id}\\n{clean_sig}"];')
        else:
            lines.append(f'    "{escaped_node}" [label="{escaped_node_id}"];')
    
    lines.append("")
    for src, dst, data in graph.edges(data=True):
        edge_label = data.get('label', '')
        escaped_src = escape_dot_string(src)
        escaped_dst = escape_dot_string(dst)
        escaped_label = escape_dot_string(edge_label)
        lines.append(f'    "{escaped_src}" -> "{escaped_dst}" [label="{escaped_label}"];')
    
    lines.append("}")
    return "\n".join(lines)


def joern_script_run(cpgFile: str, script_path: str, output_path: str):
    process = subprocess.Popen(
        [
            "joern",
            "--script",
            script_path,
            "--param",
            f"cpgFile={cpgFile}",
            "--param",
            f"outFile={output_path}",
        ],
        cwd=os.path.dirname(cpgFile),
    )
    stdout, stderr = process.communicate()

def add_global_variables(target_slicing_code_path: str, full_code_path: str, language: Language):
    target_slicing_code = ""
    with open(target_slicing_code_path, "r", encoding="utf-8", errors="ignore") as file:
        target_slicing_code += file.read() + "\n"
    
    full_code = []
    with open(full_code_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            full_code.append(line)

    new_code = add_global_variables_to_code(target_slicing_code, full_code, language)

    with open(target_slicing_code_path, "w", encoding="utf-8", errors="ignore") as file:
        file.write(new_code)


