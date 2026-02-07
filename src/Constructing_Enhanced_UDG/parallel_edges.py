from __future__ import annotations

import re
import ast
import copy
import os
import subprocess
import sys
from typing import Any
from xmlrpc.client import boolean

import networkx as nx

from . import joern_node
from .common import Language
import requests
from typing import List, Set, Dict, Tuple, Optional, Any
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
from functools import partial
import os, json, math
from tqdm import tqdm
from typing import List, Dict, Optional, Any
import requests
from .ast_parser import ASTParser
import fcntl
import threading


_methods = _calls = _inherent_types = _deinherent_types = None
_method_list = _code_dir = None
_visited = None


_token_stats_lock = threading.Lock()
_token_stats_file = None  
_token_stats = {
    'total_prompt_tokens': 0,
    'total_completion_tokens': 0,
    'total_tokens': 0,
    'call_count': 0
}

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

def get_import(target_ast_parser: ASTParser, full_ast_parser: ASTParser):
    import_decl_nodes = full_ast_parser.get_import_declaration()
    import_declaration = {}
    import_names = set()
    for node in import_decl_nodes:
        for child_node in node.children:
            if child_node.type == "scoped_identifier":
                scoped_identifier = child_node
                name_node = scoped_identifier.child_by_field_name("name")
                if name_node:
                    start_row, _ = node.start_point

                    import_line_code = node.text.decode("utf-8")
                    import_name = name_node.text.decode("utf-8")
                    import_declaration[import_name] = (start_row + 1, import_line_code)
                    import_names.add(import_name)

    result = set()

    type_names = target_ast_parser._all_type_name(target_ast_parser.root)
    for type_name in type_names:
        if type_name in import_names:
            result.add(import_declaration[type_name])

    object_names = target_ast_parser._all_java_object_name()
    for object_name in object_names:
        if object_name in import_names:
            result.add(import_declaration[object_name])
    return result

def get_class_head(ast_parser: ASTParser, language: Language):
    if language == Language.JAVA:
        class_nodes = ast_parser.get_class_declaration()
    else:
        return None

    for node in class_nodes:
        start_row, _ = node.start_point
        end_row, _ = node.end_point

        
        class_code = node.text.decode("utf-8")
        body_code = node.child_by_field_name("body").text.decode("utf-8")

        class_head = class_code.replace(body_code, "").strip() + " {"
        
        return class_head, start_row + 1, end_row + 1
    
    return None

def get_package_declaration(ast_parser: ASTParser, language: Language):
    if language == Language.JAVA:
        package_nodes = ast_parser.get_package_declaration_java()
    else:
        package_nodes = ast_parser.get_package_declaration_cpp()

    for node in package_nodes:
        start_row, _ = node.start_point

        
        package_decl = node.text.decode("utf-8")
        
        return package_decl, start_row + 1
    
    return None, None


def add_global_variables_to_code(target_slicing_code:str, full_code:list[str], language: Language):
        
    ast_parser = ASTParser(target_slicing_code, language)
    full_ast_parser = ASTParser("".join(full_code), language)
    target_package_decl, _ = get_package_declaration(ast_parser, language)
    package_decl, package_row = get_package_declaration(full_ast_parser, language)

    new_code = ""

    if target_package_decl == package_decl:
        new_code += target_slicing_code.rstrip("\n") + "\n"
        return new_code

    
    local_variables = get_local_variables(ast_parser, language)
    used_variables = get_used_variables(ast_parser)
    global_variable_names, global_variables = get_global_variables(full_ast_parser, full_code)
    
    class_head_info = get_class_head(full_ast_parser, language)
    if class_head_info is None:
        return target_slicing_code
    class_head, class_row, class_end_row = class_head_info

    
    undeclared_used_variables = used_variables - local_variables
    
    global_undeclared_used_variables = global_variable_names & undeclared_used_variables

    
    all_required_global_variables = get_recursive_global_variables(
        global_undeclared_used_variables,
        global_variables,
        global_variable_names,
        full_ast_parser,
        language
    )

    if class_head:
        for class_head_line in class_head.split("\n"):
            new_code += f"{class_row}: {class_head_line}" + "\n"
            class_row += 1
        
        sorted_global_vars = sorted(
            all_required_global_variables,
            key=lambda var: global_variables[var][0] if var in global_variables else 0
        )
        for global_var in sorted_global_vars:
            
            global_var_line_number, global_var_code = global_variables[global_var]
            new_code += f"{global_var_line_number}: {global_var_code.strip(' ')}"  
        new_code += target_slicing_code.rstrip("\n") + "\n"
        new_code += f"{class_end_row}: " + "}"
    else:
        new_code += target_slicing_code.rstrip("\n") + "\n"

    new_code_ast_parser = ASTParser(new_code, language)
    import_lines = get_import(new_code_ast_parser, full_ast_parser)
    import_code = ""
    for import_line in import_lines:
        import_row, import_line_code = import_line
        import_code += f"{import_row}: {import_line_code}" + "\n"
    
    if import_code:
        new_code = import_code + new_code
    
    if package_decl:
        package_code = f"{package_row}: {package_decl}" + "\n"
        new_code = package_code + new_code

    return new_code


def get_local_variables(ast_parser: ASTParser, language: Language) -> set[str]:
    
    if language == Language.JAVA:
        local_variable_nodes = ast_parser.get_all_assign_node_java()
    else:
        local_variable_nodes = ast_parser.get_all_assign_node()
    local_variables = set()  

    
    for node in local_variable_nodes:
        
        declarator_node = node.child_by_field_name('declarator')

        while declarator_node:
            node = declarator_node
            declarator_node = node.child_by_field_name('declarator')
        
        name = node.text.decode("utf-8")
        if name:
            
            local_variables.add(name)

    return local_variables


def get_used_variables(ast_parser: ASTParser) -> set[str]:
    
    
    
    
    

    
    
    
    
    
    
    
    

    

    used_variables = set()

    identifiers = ast_parser._all_variables()

    used_variables.update(identifiers)

    return used_variables

def get_global_variables(ast_parser: ASTParser, code: list[str]):
    global_variable_nodes = ast_parser.get_all_field_declaration()

    global_variables = {}
    global_variable_names = set()

    
    for node in global_variable_nodes:
        
        declarator_node = node.child_by_field_name('declarator')

        if declarator_node:
            
            name_node = declarator_node.child_by_field_name('name')

            if name_node:
                
                start_row, start_col = name_node.start_point
                _, end_col = name_node.end_point

                
                local_variable = code[start_row][start_col:end_col].strip() 
                
                
                node_start_row, _ = node.start_point
                node_end_row, _ = node.end_point
                if node_start_row == node_end_row:
                    
                    declaration_code = code[node_start_row]
                else:
                    
                    declaration_code = "".join(code[node_start_row:node_end_row + 1])
                
                
                global_variables[local_variable] = (node_start_row + 1, declaration_code)
                global_variable_names.add(local_variable)

    return global_variable_names, global_variables


def get_global_variables_used_in_declaration(declaration_code: str, full_ast_parser: ASTParser, global_variable_names: set[str], language: Language) -> set[str]:
    """
    Analyze other globals used in a global variable declaration.

    Args:
        declaration_code: Declaration code of the global
        full_ast_parser: AST parser for full code
        global_variable_names: Set of all global variable names

    Returns:
        Set of other global names used in this declaration
    """
    
    try:
        decl_ast_parser = ASTParser(declaration_code, language)
        all_identifiers_nodes = decl_ast_parser.get_all_identifier_node()
        all_identifiers = set()
        for node in all_identifiers_nodes:
            all_identifiers.add(node.text.decode('utf-8'))
        
        return all_identifiers & global_variable_names
    except Exception as e:
        print(f"Error parsing global declaration: {e}, code: {declaration_code}")
        return set()


def get_recursive_global_variables(
    initial_variables: set[str], 
    global_variables: dict[str, tuple[int, str]], 
    global_variable_names: set[str],
    full_ast_parser: ASTParser,
    language: Language
) -> set[str]:
    """
    Recursively get globals and all their dependent globals.

    Args:
        initial_variables: Initial set of globals to add
        global_variables: Dict {name: (line_no, declaration_code)}
        global_variable_names: Set of all global names
        full_ast_parser: AST parser for full code

    Returns:
        Set of all dependent globals
    """
    result = set(initial_variables)
    to_process = set(initial_variables)
    processed = set()
    
    
    while to_process:
        current_var = to_process.pop()
        if current_var in processed or current_var not in global_variables:
            continue
        
        processed.add(current_var)
        
        
        _, declaration_code = global_variables[current_var]
        
        
        dependent_vars = get_global_variables_used_in_declaration(
            declaration_code, full_ast_parser, global_variable_names, language
        )
        
        
        for dep_var in dependent_vars:
            if dep_var not in result:
                result.add(dep_var)
                to_process.add(dep_var)
    
    return result



def add_field_access_field_variables(ast_parser: ASTParser, cache_dir: str):
    
    field_access_nodes = ast_parser.get_field_access()
    field_access = set()  

    for node in field_access_nodes:
        
        field_access_name = node.text.decode("utf-8")
        field_access.add(field_access_name)
        
    
    if field_access == set():
        return

    for var in field_access:
        object_name = var.split(".")[0]
        field_var = var.split(".")[-1]
        
    
    local_variable_nodes = ast_parser.get_all_assign_node_java()
    local_variables = {}  

    
    for node in local_variable_nodes:
        
        declarator_node = node.child_by_field_name('declarator')
        type_name = node.child_by_field_name('type').text.decode("utf-8")

        if declarator_node:
            
            name_node = declarator_node.child_by_field_name('name')
            if name_node:
                name = name_node.text.decode("utf-8")
                
                local_variables[name] = type_name
    
    target_class = ""
    if object_name in local_variables.keys():
        target_class = local_variables[object_name]
    else:
        global_variable_nodes = ast_parser.get_all_field_declaration()

        global_variables = {}

        
        for node in global_variable_nodes:
            
            declarator_node = node.child_by_field_name('declarator')
            type_name = node.child_by_field_name('type').text.decode("utf-8")

            if declarator_node:
                
                name_node = declarator_node.child_by_field_name('name')

                if name_node:
                    name = name_node.text.decode("utf-8")
                    global_variables[name] = type_name
        if object_name in global_variables:
            target_class = global_variables[object_name]
    
    if target_class:
        storage_path = os.path.join(cache_dir, "cpg/class_variable_need.json")
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        
        with open(storage_path, 'a+', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                try:
                    class_variable_data = json.load(f)
                    if not isinstance(class_variable_data, list):
                        class_variable_data = []
                except json.JSONDecodeError:
                    class_variable_data = []

                current_data = {target_class: field_var}
                class_variable_data.append(current_data)

                f.seek(0)
                f.truncate()
                json.dump(class_variable_data, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)



def generate_callcite_prompt_reflection(caller_method: str, original_callee_method: str, candidates_method_list: str, code_snippet: str, line_code:str=None):
    system_prompt = f"""
        You are an expert in Java reflection and dynamic method resolution.
        - Input:  
        1. "Caller method": the full signature of the caller method (provided below).  
        2. "Original callee method": the full signature of the callee method being invoked through reflection (provided below).  
        3. "Candidates method list": a list of all potential methods (constructors and methods) in the project that may be called via reflection, given as full signatures (provided below).  
        4. "Code snippet": the Java code snippet that performs the reflection call (provided below).
        5. "Line of code": the line in the code where the reflection call occurs (provided below).
        - Task:  
        1. In the provided code snippet, find the reflection-based call.
        2. Resolve which actual method (constructor or method) is being executed.
        3. If the callee is a constructor, you need to resolve the actual constructor signature.
        4. Output the exact callee method signature invoked by the reflection, matching one of the signatures in the candidates method list.
        5. Return **only** the callee method signature—no additional text or commentary.
    """
        
    user_prompt = f"""
    Here are the details of the reflection call and the potential callee methods in this project. Please resolve the actual callee method being invoked:

    —— Caller method: ——  
    {caller_method}

    —— Original callee method: ——  
    {original_callee_method}

    —— Candidates method list: ——  
    {candidates_method_list}

    —— Code snippet: ——  
    {code_snippet}

    —— Line of code: ——  
    {line_code}

    Return your answer as the exact callee method signature from the candidates list, without any additional text.
    """

    return system_prompt, user_prompt

def generate_callcite_prompt_polymorphic(caller_method: str, original_callee_method: str, candidates_method_list: str, code_snippet: str, line_code:str=None):
    system_prompt = f"""
        You are an expert in object-oriented static analysis and polymorphic call resolution.
        - Input:  
        1. "Caller method": the full signature of the caller method (provided below).  
        2. "Original callee method": the full signature of the callee method being invoked polymorphically (provided below).
        3. "Candidates method list": a list of all potential methods (constructors and methods) in the project that may be called polymorphically, given as full signatures (provided below).  
        4. "Code snippet": the code snippet that contains the polymorphic call (provided below).
        5. "Line of code": the line in the code where the polymorphic call occurs (provided below).
        - Task:  
        1. In the provided code, find the polymorphic method call at the given line number.
        2. Resolve which actual method (constructor or method) is being executed.
        3. If the callee is a constructor, resolve the actual constructor signature.
        4. Output the exact target method signature invoked, matching one of the signatures in the candidates method list.
        5. Return **only** the callee method signature—no additional text or commentary.
    """
        
    user_prompt = f"""
    Here are the details of the polymorphic call and the potential callee methods in this project. Please resolve the actual method being invoked:

    —— Caller method: ——  
    {caller_method}

    —— Original callee method: ——
    {original_callee_method}

    —— Candidates method list: ——  
    {candidates_method_list}

    —— Code snippet: ——
    {code_snippet}

    —— Line of code: ——  
    {line_code}

    Return your answer as the exact callee method signature from the candidates list, without any additional text.
    """

    return system_prompt, user_prompt

def generate_callcite_prompt_pointer_func(caller_method: str, original_callee_method: str, candidates_method_list: str, code_snippet: str, line_code:str=None):
    system_prompt = f"""
        You are an expert in C/C++ static analysis and function pointer resolution.
        - Input:  
        1. "Caller method": the full signature of the caller method (provided below).  
        2. "Original callee method": the full signature of the callee method being invoked through a function pointer (provided below).
        3. "Candidates method list": a list of all potential methods in the project that may be called via this function pointer, given as full signatures (provided below).
        4. "Code snippet": the source code containing the function pointer usage (provided below).
        5. "Line of code": the specific line where the call via function pointer occurs (provided below).
        - Task:  
        1. Analyze the provided code snippet and the specific line of code to understand how the function pointer is initialized, assigned, or passed.
        2. Resolve which actual function from the "Candidates method list" is being invoked at the call site.
        3. Output the exact target function signature, matching one of the signatures in the candidates list.
        4. If no candidate matches or it cannot be determined, return "None".
        5. Return **only** the function signature or "None"—no additional text, commentary, or Markdown formatting.
    """
    user_prompt = f"""
    Here are the details of the function pointer call and the potential candidates in this project. Please resolve the actual function being invoked:

    —— Caller method: ——  
    {caller_method}

    —— Original callee method: ——
    {original_callee_method}

    —— Candidates method list: ——  
    {candidates_method_list}

    —— Code snippet: ——
    {code_snippet}

    —— Line of code: ——  
    {line_code if line_code else "Not provided"}

    Based on the static analysis of the code, return the exact signature from the candidates list that is being called.
    Answer:
    """
    
    return system_prompt, user_prompt

def get_callgraph(src_method: str, dst_method: str, code_snippet: str, func_list: str, reflect: bool=True, line_code:str=None, language:Language=Language.JAVA):
    if language == Language.JAVA:
        if reflect:
            system_prompt, user_prompt = generate_callcite_prompt_reflection(src_method, dst_method, func_list, code_snippet, line_code)
        else:
            system_prompt, user_prompt = generate_callcite_prompt_polymorphic(src_method, dst_method, func_list, code_snippet, line_code)
    elif language == Language.CPP or language == Language.C:
        system_prompt, user_prompt = generate_callcite_prompt_pointer_func(src_method, dst_method, func_list, code_snippet, line_code)
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

def _record_token_usage(prompt_tokens: int, completion_tokens: int, total_tokens: int):
    global _token_stats, _token_stats_file
    
    
    if _token_stats_file:
        try:
            with open(_token_stats_file, 'a+', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    
                    f.seek(0)
                    try:
                        existing_stats = json.load(f)
                    except (json.JSONDecodeError, ValueError):
                        existing_stats = {
                            'total_prompt_tokens': 0,
                            'total_completion_tokens': 0,
                            'total_tokens': 0,
                            'call_count': 0
                        }
                    
                    
                    existing_stats['total_prompt_tokens'] += prompt_tokens
                    existing_stats['total_completion_tokens'] += completion_tokens
                    existing_stats['total_tokens'] += total_tokens
                    existing_stats['call_count'] += 1
                    
                    
                    f.seek(0)
                    f.truncate()
                    json.dump(existing_stats, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
                print(f"Failed to record token usage: {e}")
    else:
        
        with _token_stats_lock:
            _token_stats['total_prompt_tokens'] += prompt_tokens
            _token_stats['total_completion_tokens'] += completion_tokens
            _token_stats['total_tokens'] += total_tokens
            _token_stats['call_count'] += 1

def init_token_stats(stats_file: Optional[str] = None):
    global _token_stats_file, _token_stats
    
    _token_stats_file = stats_file
    if stats_file:
        
        os.makedirs(os.path.dirname(stats_file) if os.path.dirname(stats_file) else '.', exist_ok=True)
        if not os.path.exists(stats_file):
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_tokens': 0,
                    'call_count': 0
                }, f, indent=2)
    else:
        
        _token_stats = {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_tokens': 0,
            'call_count': 0
        }

def get_token_stats() -> Dict[str, int]:
    global _token_stats, _token_stats_file
    
    if _token_stats_file and os.path.exists(_token_stats_file):
        try:
            with open(_token_stats_file, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    stats = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return stats
        except Exception as e:
            print(f"Failed to read token stats: {e}")
            return _token_stats.copy()
    else:
        with _token_stats_lock:
            return _token_stats.copy()

def reset_token_stats():
    global _token_stats, _token_stats_file
    
    if _token_stats_file and os.path.exists(_token_stats_file):
        try:
            with open(_token_stats_file, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump({
                        'total_prompt_tokens': 0,
                        'total_completion_tokens': 0,
                        'total_tokens': 0,
                        'call_count': 0
                    }, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"Failed to reset token stats: {e}")
    else:
        with _token_stats_lock:
            _token_stats = {
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'total_tokens': 0,
                'call_count': 0
            }

def _safe_get_line(lines, idx):
    
    i = max(0, min(len(lines)-1, idx-1))
    return lines[i] if lines else ""

def _init_worker(methods, calls, code_dir, token_stats_file=None):
    global _methods, _calls, _code_dir, _token_stats_file
    _methods = methods
    _calls = calls
    _code_dir = code_dir
    _token_stats_file = token_stats_file

def _process_one_edge(edge):
    src, dst, edge_attrs = edge
    results = []
    method_name_dict_updates = {}  

    edge_label = edge_attrs.get("label", "")
    if edge_label != "CALL":
        return results, method_name_dict_updates

    
    src_method = None
    dst_method = None

    if src in _methods:
        src_method = _methods[src]["full_name"]
    elif src in _calls:
        src_method = _calls[src].get("method_full_name")

    if dst in _methods:
        dst_method = _methods[dst]["full_name"]
    elif dst in _calls:
        dst_method = _calls[dst].get("method_full_name")

    if dst_method:
        if src_method and dst_method and src_method != dst_method:
            line_number = ""
            if src in _calls:
                line_number = _calls[src].get("line_number", "")
            elif dst in _calls:
                line_number = _calls[dst].get("line_number", "")
            results.append((src_method, dst_method, line_number))

        if dst_method.startswith("java.lang.Class.getMethod"):
            call_info = _calls.get(src, {})
            file_name = call_info.get("file_name")
            if file_name and os.path.exists(os.path.join(_code_dir, file_name)):
                with open(os.path.join(_code_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                    code_lines = f.readlines()
                line_code = _safe_get_line(code_lines, int(call_info["line_number"]))
                regex = r'getMethod\("([^"]+)"'
                match = re.search(regex, line_code)
                if match:
                    
                    method_name = match.group(1).strip()
                    if method_name and dst in _methods:
                        
                        if method_name not in method_name_dict_updates:
                            method_name_dict_updates[method_name] = []
                        method_name_dict_updates[method_name].append(_methods[dst])

    return results, method_name_dict_updates


def _process_batch(batch):
    combined_add = []
    combined_updates = {}  
    for edge in batch:
        edges_to_add, method_name_dict_updates = _process_one_edge(edge)
        combined_add.extend(edges_to_add)
        
        for method_name, method_list in method_name_dict_updates.items():
            if method_name not in combined_updates:
                combined_updates[method_name] = []
            combined_updates[method_name].extend(method_list)
    return combined_add, combined_updates

def build_call_edges_parallel(edges, methods, calls, code_dir, max_workers=None, chunk=None):
    if not edges:
        return [], {}   

    
    if chunk is None:
        
        
        batches_per_worker = 6
        chunk = max(64, len(edges)
        chunk = min(chunk, 1024)  

    all_results_add = []
    all_method_name_dict_updates = defaultdict(list)  
    
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_init_worker,
        initargs=(methods, calls, code_dir)
    ) as ex:
        
        futures = {}
        total_batches = (len(edges) + chunk - 1)
        
        for i in range(0, len(edges), chunk):
            batch = edges[i:i+chunk]
            future = ex.submit(_process_batch, batch)
            futures[future] = i

        for fut in as_completed(futures):
            try:
                edges_to_add, method_name_dict_updates = fut.result()
                all_results_add.extend(edges_to_add)
                
                for method_name, method_list in method_name_dict_updates.items():
                    all_method_name_dict_updates[method_name].extend(method_list)
            except Exception as e:
                batch_num = futures[fut]
                print(f"Error processing batch {batch_num}: {str(e)}")
                continue

    
    all_method_name_dict_updates = dict(all_method_name_dict_updates)
    
    return all_results_add, all_method_name_dict_updates