import ast
import json
import logging
import os
import re
import requests
import subprocess
import joern
import copy
from ast_parser import ASTParser
from tree_sitter import Node
from common import Language
import networkx as nx
from collections import defaultdict
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

_SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
_GET_CALLGRAPH_SCRIPT = os.path.join(_SCRIPT_DIR, "get_callgraph.sc")

class DeepSeekAPI:
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided, please set DEEPSEEK_API_KEY environment variable or pass api_key parameter")
        
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
            logger.info(f"Calling DeepSeek API model: {model}")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def _handle_stream_response(self, response: requests.Response) -> Dict[str, Any]:
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
        url = f"{self.base_url}/v1/models"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get model list: {e}")
            raise

method_name_cache = {}
_SEMANTIC_CACHE: dict[str, tuple[defaultdict, set]] = {}
MAX_FIXPOINT_ITERS = 3
def _short_method_name_from_call_node(cpg, call_node_id: str) -> str | None:
    if call_node_id in method_name_cache:
        return method_name_cache[call_node_id]

    name = cpg.nodes[call_node_id].get("NAME")
    if name:
        method_name_cache[call_node_id] = name
        return name
    full = cpg.nodes[call_node_id].get("METHOD_FULL_NAME", "")
    idx_dot = full.rfind(".")
    idx_colon = full.find(":")
    if idx_dot != -1 and idx_colon != -1 and idx_colon > idx_dot:
        method_name_cache[call_node_id] = full[idx_dot + 1: idx_colon]
        return full[idx_dot + 1: idx_colon]
    if idx_colon != -1:
        head = full[:idx_colon]
        method_name_cache[call_node_id] = head.split(".")[-1] or None
        return head.split(".")[-1] or None
    return None

def _is_primitive(t: str) -> bool:
    if not t:
        return False
    s = t.strip().lower()
    if s.endswith("[]"):
        return False  
    return s in {"int", "short", "long", "byte", "float", "double", "char", "boolean"}

def _fallback_recursive_semantics(cpg, method_node: str) -> tuple[defaultdict, set]:
    semantic_model: defaultdict[str, set[str]] = defaultdict(set)
    return_dependency: set[str] = set()
    if not method_node:
        return semantic_model, return_dependency
    method_head = cpg.nodes[method_node].get("CODE")
    if cpg.nodes[method_node].get("NAME") == "<init>" and method_head:
        method_head = "init " + method_head
    if not method_head:
        return semantic_model, return_dependency
    try:
        ast_parser_head = ASTParser(method_head, Language.JAVA)
        method_decls = ast_parser_head.get_method_declaration() or []
        for method_decl in method_decls:
            params_node = method_decl.child_by_field_name("parameters")
            if not params_node:
                continue
            for p in params_node.children:
                if p.type == "formal_parameter":
                    name_node = p.child_by_field_name("name")
                    if name_node:
                        param_name = name_node.text.decode("utf-8")
                        semantic_model[param_name].add(param_name)
                        return_dependency.add(param_name)
    except Exception:
        pass
    return semantic_model, return_dependency


def _merge_into_cache(method_node: str, semantic_model: defaultdict, return_dependency: set) -> tuple[defaultdict, set, bool]:
    merged_model: defaultdict[str, set[str]] = defaultdict(set)
    merged_ret: set[str] = set(return_dependency)
    changed = False

    for k, v in semantic_model.items():
        merged_model[k].update(v)

    if method_node in _SEMANTIC_CACHE:
        cached_model, cached_ret = _SEMANTIC_CACHE[method_node]
        for k, v in cached_model.items():
            before = len(merged_model[k])
            merged_model[k].update(v)
            if len(merged_model[k]) > before:
                changed = True
        before_ret = len(merged_ret)
        merged_ret.update(cached_ret)
        if len(merged_ret) > before_ret:
            changed = True
    else:
        changed = True

    _SEMANTIC_CACHE[method_node] = (copy.deepcopy(merged_model), set(merged_ret))
    return merged_model, merged_ret, changed

def _extract_var_name_from_left(left_node: Node, ast_parser: ASTParser) -> str:
    if left_node.type == "identifier":
        return left_node.text.decode("utf-8")
    elif left_node.type == "array_access":
        base_name = ast_parser._extract_array_base_name(left_node)
        if base_name:
            return base_name
        text = left_node.text.decode("utf-8")
        idx = text.find("[")
        if idx != -1:
            return text[:idx].strip()
        return text
    elif left_node.type == "field_access":
        full = ast_parser._full_this_field_access(left_node)
        if full:
            return full
        obj = left_node
        while obj and obj.type == "field_access":
            obj = obj.child_by_field_name("object")
        if obj and obj.type == "identifier":
            return obj.text.decode("utf-8")
    return left_node.text.decode("utf-8")

def get_global_variables(ast_parser: ASTParser):

    global_variable_nodes = ast_parser._all_field_declaration(ast_parser.root.children[0].child_by_field_name("body"))

    global_variable_names = set()

    for node in global_variable_nodes:
        declarator_node = node.child_by_field_name('declarator')

        if declarator_node:
            name_node = declarator_node.child_by_field_name('name')

            if name_node:
                local_variable = name_node.text.decode("utf-8")
                global_variable_names.add(local_variable)

    return global_variable_names

def _get_class_and_method_variables(
    cpg,
    method_node: str,
    all_code: str,
    result_lines: list[str]
) -> tuple[set[str], set[str]]:
    method_full_name = cpg.nodes[method_node].get("FULL_NAME", "")
    match = re.search(r"(?:^|[$.])([A-Za-z_]\w*)(?=\.[^.]+:)", method_full_name)
    target_class_name = match.group(1) if match else ""
    
    global_variables = set()
    local_variables = set()
    
    if not target_class_name:
        return global_variables, local_variables
    
    all_code_ast_parser = ASTParser("".join(all_code), Language.JAVA)
    all_class_node = all_code_ast_parser.get_class_declaration()
    target_class_node = None
    
    for class_node in all_class_node:
        if class_node.child_by_field_name("name").text.decode("utf-8") == target_class_name:
            target_class_node = class_node
            break
    
    if target_class_node is not None:
        target_class_code = target_class_node.text.decode("utf-8")
        target_class_ast_parser = ASTParser(target_class_code, Language.JAVA)
        global_variables = get_global_variables(target_class_ast_parser)
        local_variables = _get_local_variables_in_method(result_lines)
    
    return global_variables, local_variables

def _normalize_global_variables_with_this(
    cpg,
    params: list[str],
    method_node: str,
    all_code: str,
    result_lines: list[str],
    semantic_model: dict,
    return_dependency: set
) -> None:
    global_variables, local_variables = _get_class_and_method_variables(
        cpg, method_node, all_code, result_lines
    )
    if local_variables:
        for key, vals in semantic_model.copy().items():
            if key in global_variables and key not in params and f"this.{key}" not in local_variables:
                this_key = "this." + key
                semantic_model[this_key] = semantic_model[key]
                del semantic_model[key]
            else:
                this_key = key
            for val in vals:
                if val in global_variables and val not in params and f"this.{val}" not in local_variables:
                    key_val = "this." + val
                    semantic_model[this_key].add(key_val)
                    semantic_model[this_key].remove(val)


def _map_formal_to_actual_params(
    tmp_semantic_model: dict,
    tmp_ret_depend: set,
    formal_params_list: list,
    actual_params_dict: dict,
    semantic_model: defaultdict
) -> tuple[dict, set]:
    formal_to_actual_map = {}
    for pos, formal_param in enumerate(formal_params_list):
        if pos in actual_params_dict and actual_params_dict[pos]:
            actual_params = actual_params_dict[pos]
            if actual_params:
                formal_to_actual_map[formal_param] = actual_params
    
    mapped_semantic_model = defaultdict(set)
    for key, vals in tmp_semantic_model.items():
        mapped_keys = formal_to_actual_map.get(key, key)
        if isinstance(mapped_keys, str):
            mapped_keys = [mapped_keys]
        for mapped_key in mapped_keys:  
            if mapped_key in semantic_model:
                continue
            mapped_vals = set()
            for val in vals:
                mapped_vals_1 = formal_to_actual_map.get(val, val)
                if isinstance(mapped_vals_1, str):
                    mapped_vals_1 = [mapped_vals_1]
                for mapped_val in mapped_vals_1:
                    if mapped_val in semantic_model:
                        for map_val in semantic_model[mapped_val]:
                            mapped_vals.add(map_val)
                    else:
                        mapped_vals.add(mapped_val)
            mapped_semantic_model[mapped_key].update(mapped_vals)

    mapped_ret_depend = set()
    for ret_param in tmp_ret_depend:
        mapped_ret_params = formal_to_actual_map.get(ret_param, ret_param)
        if isinstance(mapped_ret_params, str):
            mapped_ret_params = [mapped_ret_params]
        for mapped_ret_param in mapped_ret_params:
            if mapped_ret_param in semantic_model:
                for map_val in semantic_model[mapped_ret_param]:
                    mapped_ret_depend.add(map_val)
            else:
                mapped_ret_depend.add(mapped_ret_param)
    return mapped_semantic_model, mapped_ret_depend

def _merge_semantic_model_from_call(
    tmp_semantic_model: dict,
    tmp_ret_depend: set,
    semantic_model: defaultdict,
    m_actual_params: dict,
    m_formal_params: list,
    m_params_type: list,
    node_method_name: str,
    object_callee_name_dict: dict,
    var_name: str = None
):
    for key, vals in tmp_semantic_model.items():
        if m_formal_params and key in m_formal_params:
            pos = m_formal_params.index(key)
            if pos in m_actual_params and m_actual_params[pos] is not None and (pos < len(m_params_type) and _is_primitive(m_params_type[pos])):
                actual_keys = m_actual_params[pos]
            else:
                continue
            for val in list(vals):
                if m_formal_params and val in m_formal_params:
                    pos = m_formal_params.index(val)
                    if pos in m_actual_params and m_actual_params[pos] is not None:
                        actual_vals = m_actual_params[pos]
                        for actual_key in actual_keys:
                            for actual_val in actual_vals:
                                if semantic_model[actual_val] and semantic_model[actual_val] != set():
                                    semantic_model[actual_key].add(actual_val)
                                    semantic_model[actual_key].update(semantic_model[actual_val])
                                else:
                                    semantic_model[actual_key].add(actual_val)
                elif "this." in val:
                    for actual_key in actual_keys:
                        if node_method_name in object_callee_name_dict:
                            val = object_callee_name_dict[node_method_name]
                            if semantic_model[val] and semantic_model[val] != set():
                                semantic_model[actual_key].add(val)
                                semantic_model[actual_key].update(semantic_model[val])
                            else:
                                semantic_model[actual_key].add(val)
        
        elif "this." in key:
            if node_method_name in object_callee_name_dict:
                key = object_callee_name_dict[node_method_name]
                for val in list(vals):
                    if m_formal_params and val in m_formal_params:
                        pos = m_formal_params.index(val)
                        if pos in m_actual_params and m_actual_params[pos] is not None:
                            actual_vals = m_actual_params[pos]
                            for actual_val in actual_vals:
                                if semantic_model[actual_val] and semantic_model[actual_val] != set():
                                    semantic_model[key].add(actual_val)
                                    semantic_model[key].update(semantic_model[actual_val])
                                else:
                                    semantic_model[key].add(actual_val)
                    elif "this." in val:
                        if node_method_name in object_callee_name_dict:
                            val = object_callee_name_dict[node_method_name]
                            if semantic_model[val] and semantic_model[val] != set():
                                semantic_model[key].add(val)
                                semantic_model[key].update(semantic_model[val])
                            else:
                                semantic_model[key].add(val)
            else:
                key = "this."
                for val in list(vals):
                    if m_formal_params and val in m_formal_params:
                        pos = m_formal_params.index(val)
                        if pos in m_actual_params and m_actual_params[pos] is not None:
                            actual_vals = m_actual_params[pos]
                            for actual_val in actual_vals:
                                if semantic_model[actual_val] and semantic_model[actual_val] != set():
                                    semantic_model[key].add(actual_val)
                                    semantic_model[key].update(semantic_model[actual_val])
                                else:
                                    semantic_model[key].add(actual_val)
                    elif "this." in val:
                        if node_method_name in object_callee_name_dict:
                            val = object_callee_name_dict[node_method_name]
                            if semantic_model[val] and semantic_model[val] != set():
                                semantic_model[key].add(val)
                                semantic_model[key].update(semantic_model[val])
                            else:
                                semantic_model[key].add(val)
    if var_name:
        for p in tmp_ret_depend:
            if m_formal_params and p in m_formal_params:
                pos = m_formal_params.index(p)
                if pos in m_actual_params and m_actual_params[pos] is not None:
                    actual_ps = m_actual_params[pos]
                    for actual_p in actual_ps:
                        if semantic_model[actual_p] and semantic_model[actual_p] != set():
                            semantic_model[var_name].add(actual_p)
                            semantic_model[var_name].update(semantic_model[actual_p])
                        else:
                            semantic_model[var_name].add(actual_p)
            elif "this." in p:
                if node_method_name in object_callee_name_dict:
                    p = object_callee_name_dict[node_method_name]
                    if semantic_model[p] and semantic_model[p] != set():
                        semantic_model[var_name].add(p)
                        semantic_model[var_name].update(semantic_model[p])
                    else:
                        semantic_model[var_name].add(p)

def process_enhanced_for_loop(target_lines: list[str], semantic_model: defaultdict[str, set[str]]) -> int:
    """
    Locate the first enhanced-for statement in the provided lines, link the iterator
    variable to its backing collection, and process simple assignment semantics inside
    the loop body so downstream lines can reuse the propagated dependencies.

    Returns the number of lines consumed by the enhanced-for construct so the caller
    can advance to the first line after the loop body.
    """
    if not target_lines:
        return 0

    snippet_lines: list[str] = []
    parser: ASTParser | None = None
    enhanced_node: Node | None = None

    for line in target_lines:
        snippet_lines.append(line)
        joined = "\n".join(snippet_lines)
        try:
            parser = ASTParser(joined, Language.JAVA)
        except Exception:
            continue
        nodes = parser.get_enhanced_for_statment()
        if nodes:
            enhanced_node = nodes[0]
            if enhanced_node.end_point[0] + 1 > len(snippet_lines):
                continue
            break

    if parser is None or enhanced_node is None:
        return 0

    lines_consumed = max(1, min(len(snippet_lines), enhanced_node.end_point[0] + 1))

    name_node = enhanced_node.child_by_field_name("name")
    value_node = enhanced_node.child_by_field_name("value")
    body_node = enhanced_node.child_by_field_name("body")

    if name_node is None or value_node is None:
        return lines_consumed

    if name_node.type != "identifier":
        return lines_consumed
    iter_var = name_node.text.decode("utf-8")
    if not iter_var:
        return lines_consumed

    deps_from_collection = parser._all_rhs_identifiers_with_this(value_node)
    if not deps_from_collection:
        text = value_node.text.decode("utf-8").strip()
        if text:
            deps_from_collection = {text}

    for dep in deps_from_collection:
        if dep == iter_var:
            continue
        semantic_model[iter_var].add(dep)
        semantic_model[iter_var].update(semantic_model[dep])

    if body_node is None:
        return lines_consumed

    body_text = body_node.text.decode("utf-8")
    body_lines = body_text.splitlines()
    if body_lines and body_lines[0].strip().startswith("{"):
        body_lines = body_lines[1:]
    if body_lines and body_lines[-1].strip().startswith("}"):
        body_lines = body_lines[:-1]

    rel_idx = 0
    while rel_idx < len(body_lines):
        raw_line = body_lines[rel_idx]
        stripped = raw_line.strip()
        if not stripped:
            rel_idx += 1
            continue
        try:
            line_parser = ASTParser(stripped, Language.JAVA)
        except Exception:
            rel_idx += 1
            continue
        assign_nodes = line_parser.get_assignment_expression()
        for assign_node in assign_nodes:
            left = assign_node.child_by_field_name("left")
            right = assign_node.child_by_field_name("right")
            if left is None or right is None:
                continue

            var_name = _extract_var_name_from_left(left, line_parser)
            all_ids_in_rhs = line_parser._all_identifier_texts(right)
            callee_ids = line_parser._callee_identifier_texts(right)
            object_creation_expression = line_parser._object_creation_expression_texts(right)
            callee_ids.extend(object_creation_expression)

            diff = [
                item
                for item in all_ids_in_rhs
                if item not in callee_ids or callee_ids.count(item) < all_ids_in_rhs.count(item)
            ]
            rhs_var_ids = set(diff)
            rhs_var_ids.discard(var_name)

            for ident in rhs_var_ids:
                semantic_model[var_name].add(ident)
                semantic_model[var_name].update(semantic_model[ident])
        local_var_nodes = line_parser.get_all_assign_node_java()
        for decl in local_var_nodes:
            declarator = decl.child_by_field_name("declarator")
            left = declarator.child_by_field_name("name") if declarator else None
            right = declarator.child_by_field_name("value") if declarator else None
            if left is None or right is None:
                continue

            var_name = _extract_var_name_from_left(left, line_parser)
            all_ids_in_rhs = line_parser._all_identifier_texts(right)
            callee_ids = line_parser._callee_identifier_texts(right)
            object_creation_expression = line_parser._object_creation_expression_texts(right)
            callee_ids.extend(object_creation_expression)

            diff = [
                item
                for item in all_ids_in_rhs
                if item not in callee_ids or callee_ids.count(item) < all_ids_in_rhs.count(item)
            ]
            rhs_var_ids = set(diff)
            rhs_var_ids.discard(var_name)

            for ident in rhs_var_ids:
                semantic_model[var_name].add(ident)
                semantic_model[var_name].update(semantic_model[ident])
        inv_nodes = line_parser.get_method_invocation()
        method_names_on_line: set[str] = set()
        for inv in inv_nodes:
            method_names_on_line |= line_parser._callee_names(inv)
        if method_names_on_line:
            for name in method_names_on_line:
                semantic_model[iter_var].add(name)
        return_nodes = line_parser.get_return_statement()
        for ret_node in return_nodes:
            value_node = ret_node.child_by_field_name("value")
            if value_node is None:
                continue
            ids = line_parser._all_rhs_identifiers_with_this(value_node)
            for ident in ids:
                semantic_model[iter_var].add(ident)
                semantic_model[iter_var].update(semantic_model[ident])
        rel_idx += 1

    iterator_deps = set(semantic_model[iter_var])
    if iterator_deps:
        for key, vals in semantic_model.items():
            if key == iter_var:
                continue
            if iter_var in vals:
                vals.update(iterator_deps)
    return lines_consumed

def _get_local_variables_in_method(result_lines: list[str]) -> set:
    local_variables = set()
    result_lines_ast_parser = ASTParser("".join(result_lines), Language.JAVA)
    method_declarations = result_lines_ast_parser.get_method_declaration()
    
    body_node = next((method_declaration.child_by_field_name("body") for method_declaration in method_declarations), None)
    if body_node:
        local_var_declarations = result_lines_ast_parser.get_all_assign_node_java()
        for var_decl in local_var_declarations:
            declarator_node = var_decl.child_by_field_name("declarator")
            if declarator_node:
                name_node = declarator_node.child_by_field_name("name")
                if name_node:
                    var_name = name_node.text.decode("utf-8")
                    local_variables.add(var_name)
    
    return local_variables


def get_func_param_edge(
        code_path,
        cpg, node,
        call_edges,
        call_edges_reverse,
        call_dict,
        formal_params,
        actual_params,
        params_type,
        annotation_interface_param_depend: dict,
        annotation_interface_param_ret_depend: dict,
        IS_METHOD: bool = False,
        visited: set[tuple]=None
    ):

    if visited is None:
        visited = set()

    if IS_METHOD:
        method_node = node
    else:
        method_node = call_edges.get(node)


    tag = method_node or node

    if tag in visited:
        if method_node in _SEMANTIC_CACHE:
            cached_model, cached_ret = _SEMANTIC_CACHE[method_node]
            return copy.deepcopy(cached_model), set(cached_ret)
        return defaultdict(set), set()

    visited.add(tag)

    if method_node in annotation_interface_param_depend.keys():
        return annotation_interface_param_depend[method_node], annotation_interface_param_ret_depend[method_node]

    if not method_node:
        return defaultdict(set), set()

    if not ("FILENAME" in cpg.nodes[method_node] and
            "LINE_NUMBER" in cpg.nodes[method_node] and
            "LINE_NUMBER_END" in cpg.nodes[method_node]):
        return defaultdict(set), set()

    file_name = cpg.nodes[method_node]["FILENAME"]
    filepath = os.path.join(code_path, file_name)
    method_start = int(cpg.nodes[method_node]["LINE_NUMBER"])
    method_end = int(cpg.nodes[method_node]["LINE_NUMBER_END"])

    if file_name == "<empty>" or not file_name:
        return defaultdict(set), set()

    result_lines = []
    all_code = ""
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            all_code = f.read() + "\n"
            f.seek(0)
            for lineno, line in enumerate(f, start=1):
                if method_start <= lineno <= method_end:
                    result_lines.append(line.rstrip("\n"))
                if lineno > method_end:
                    break
    except FileNotFoundError:
        return defaultdict(set), set()

    semantic_model: dict[str, set[str]] = defaultdict(set)
    return_dependency = set()

    if IS_METHOD:
        params = []
        method_head = cpg.nodes[method_node].get("CODE")
        if method_head:
            ast_parser_head = ASTParser(method_head, Language.JAVA)
            method_decls = ast_parser_head.get_method_declaration() or []
            for method_decl in method_decls:
                ps = method_decl.child_by_field_name("parameters")
                if not ps:
                    continue
                for p in ps.children:
                    if p.type == "formal_parameter":
                        name_node = p.child_by_field_name("name")
                        if name_node:
                            params.append(name_node.text.decode("utf-8"))
                    elif p.type == "spread_parameter":
                        for spread_parameter_child in p.children:
                            if spread_parameter_child.type == "variable_declarator":
                                name_node = spread_parameter_child.child_by_field_name("name")
                                if name_node:
                                    params.append(name_node.text.decode("utf-8"))
        callee_node = method_node
        actual_params_of_call = []
    else:
        callee_node = call_edges.get(node)
        if not callee_node:
            return defaultdict(set), set()
        param_list = formal_params.get(node, {}).get(callee_node, [])
        params = param_list[:]

    var_last_def_line: dict[str, str] = {}

    joined_lines = "\n".join(result_lines)
    method_declarations = ASTParser(joined_lines, Language.JAVA).get_method_declaration() or []
    target_lines = result_lines
    body_rel_start_line = 0
    for method_declaration in method_declarations:
        body_node = method_declaration.child_by_field_name("body")
        if body_node is None:
            continue
        body_text = body_node.text.decode("utf-8")
        if not body_text.strip():
            continue
        target_lines = body_text.splitlines()
        body_start_row = body_node.start_point[0]
        method_start_row = method_declaration.start_point[0]
        first_stmt_row = None
        first_stmt_node = None
        for child in body_node.named_children:
            if child.type in {"line_comment", "block_comment"}:
                continue
            first_stmt_row = child.start_point[0]
            first_stmt_node = child
            break

        if first_stmt_row is not None:
            rel_to_body = first_stmt_row - body_start_row
            if 0 < rel_to_body <= len(target_lines):
                target_lines = target_lines[rel_to_body:]
            elif rel_to_body == 0 and target_lines:
                stmt_col = first_stmt_node.start_point[1] if first_stmt_node else 0
                body_col = body_node.start_point[1]
                offset = max(stmt_col - body_col, 0)
                if offset:
                    target_lines[0] = target_lines[0][offset:]
            body_rel_start_line = max(first_stmt_row - method_start_row, 0)
        else:
            body_rel_start_line = max(body_start_row - method_start_row, 0)
        break

    rel_idx = 0
    while rel_idx < len(target_lines):
        idx = body_rel_start_line + rel_idx
        line = target_lines[rel_idx]
        file_lineno = method_start + idx
        ast_parser = ASTParser(line, Language.JAVA)

        root_node = ast_parser.root
        root_type = root_node.type
        
        while root_type in ("program", "source_file", "expression_statement"):
            if root_node.named_children:
                root_type = root_node.named_children[0].type
                root_node = root_node.named_children[0]
            else:
                rel_idx += 1
                continue
        if root_type == "enhanced_for_statement":
            rel_idx += 1
            continue
        elif root_type == "assignment_expression":
            ast_node = root_node
            left = ast_node.child_by_field_name("left")
            right = ast_node.child_by_field_name("right")
            if left is None or right is None:
                rel_idx += 1
                continue

            var_name = _extract_var_name_from_left(left, ast_parser)
            all_ids_in_rhs = ast_parser._all_identifier_texts(right)
            callee_ids = ast_parser._callee_identifier_texts(right)
            object_creation_expression = ast_parser._object_creation_expression_texts(right)
            callee_ids.extend(object_creation_expression)
            object_callee_name_dict = ast_parser.object_callee_name_dict(ast_parser.root)

            diff = [item for item in all_ids_in_rhs if item not in callee_ids or callee_ids.count(item) < all_ids_in_rhs.count(item)]
            rhs_var_ids = diff
            rhs_var_ids = set(rhs_var_ids)
            callee_ids = set(callee_ids)
            rhs_var_ids.discard(var_name)

            per_line_key = f"{file_name}#{str(int(file_lineno))}"

            for ident in rhs_var_ids:
                semantic_model[var_name].add(ident)
                semantic_model[var_name].update(semantic_model[ident])
            
            for m_id in call_dict.get(per_line_key, []):
                node_method_name = _short_method_name_from_call_node(cpg, m_id)
                if node_method_name and node_method_name in callee_ids:
                    tmp_semantic_model, tmp_ret_depend = get_func_param_edge(
                        code_path, cpg, m_id, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                        IS_METHOD=False, visited=visited
                    )

                    m_actual_params = actual_params.get(m_id, {})
                    m_formal_params = formal_params.get(m_id, {}).get(call_edges[m_id], [])
                    m_params_type = params_type.get(m_id, {}).get(call_edges[m_id], [])
                    
                    if m_formal_params and m_actual_params:
                        tmp_semantic_model, tmp_ret_depend = _map_formal_to_actual_params(
                            tmp_semantic_model, tmp_ret_depend,
                            m_formal_params, m_actual_params, semantic_model
                        )

                    _merge_semantic_model_from_call(
                        tmp_semantic_model, tmp_ret_depend, semantic_model,
                        m_actual_params, m_formal_params, m_params_type,
                        node_method_name, object_callee_name_dict, var_name
                    )
        elif root_type == "local_variable_declaration":
            ast_node = root_node
            declarator = ast_node.child_by_field_name("declarator")
            left = declarator.child_by_field_name("name") if declarator else None
            right = declarator.child_by_field_name("value") if declarator else None
            if left is None or right is None:
                rel_idx += 1
                continue

            var_name = _extract_var_name_from_left(left, ast_parser)
            all_ids_in_rhs = ast_parser._all_identifier_texts(right)
            callee_ids = ast_parser._callee_identifier_texts(right)
            object_creation_expression = ast_parser._object_creation_expression_texts(right)
            callee_ids.extend(object_creation_expression)
            object_callee_name_dict = ast_parser.object_callee_name_dict(ast_parser.root)


            diff = [item for item in all_ids_in_rhs if item not in callee_ids or callee_ids.count(item) < all_ids_in_rhs.count(item)]
            rhs_var_ids = diff
            rhs_var_ids = set(rhs_var_ids)
            callee_ids = set(callee_ids)
            rhs_var_ids.discard(var_name)

            per_line_key = f"{file_name}#{str(int(file_lineno))}"

            for ident in rhs_var_ids:
                semantic_model[var_name].add(ident)
                semantic_model[var_name].update(semantic_model[ident])
            
            for m_id in call_dict.get(per_line_key, []):
                node_method_name = _short_method_name_from_call_node(cpg, m_id)
                if node_method_name and node_method_name in callee_ids:
                    tmp_semantic_model, tmp_ret_depend = get_func_param_edge(
                        code_path, cpg, m_id, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                        IS_METHOD=False, visited=visited
                    )
                    
                    m_actual_params = actual_params.get(m_id, {})
                    m_formal_params = formal_params.get(m_id, {}).get(call_edges[m_id], [])
                    m_params_type = params_type.get(m_id, {}).get(call_edges[m_id], [])

                    if m_formal_params and m_actual_params:
                        tmp_semantic_model, tmp_ret_depend = _map_formal_to_actual_params(
                            tmp_semantic_model, tmp_ret_depend,
                            m_formal_params, m_actual_params, semantic_model
                        )

                    _merge_semantic_model_from_call(
                        tmp_semantic_model, tmp_ret_depend, semantic_model,
                        m_actual_params, m_formal_params, m_params_type,
                        node_method_name, object_callee_name_dict, var_name
                    )

            type_node = right.child_by_field_name("type")
            if type_node and type_node.type == "type_identifier":
                method_name = type_node.text.decode("utf-8")
                for m_id in call_dict.get(per_line_key, []):
                    node_method_name = _short_method_name_from_call_node(cpg, m_id)
                    if node_method_name and node_method_name == method_name:
                        tmp_semantic_model, tmp_ret_depend = get_func_param_edge(
                            code_path, cpg, m_id, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                            IS_METHOD=False, visited=visited
                        )

                        m_actual_params = actual_params.get(m_id, {})
                        m_formal_params = formal_params.get(m_id, {}).get(call_edges[m_id], [])
                        m_params_type  = params_type.get(m_id, {}).get(call_edges[m_id], [])

                        if m_formal_params and m_actual_params:
                            tmp_semantic_model, tmp_ret_depend = _map_formal_to_actual_params(
                                tmp_semantic_model, tmp_ret_depend,
                                m_formal_params, m_actual_params, semantic_model
                            )

                        _merge_semantic_model_from_call(
                            tmp_semantic_model, tmp_ret_depend, semantic_model,
                            m_actual_params, m_formal_params, m_params_type,
                            node_method_name, object_callee_name_dict, var_name
                        )

        elif root_type == "method_invocation":
            inv_node = root_node
            object_callee_name_dict = ast_parser.object_callee_name_dict(ast_parser.root)
            method_names_on_line: set[str] = ast_parser._callee_names(inv_node)

            per_line_key = f"{file_name}#{str(int(file_lineno))}"
            for m_id in call_dict.get(per_line_key, []):
                node_method_name = _short_method_name_from_call_node(cpg, m_id)
                if node_method_name and node_method_name in method_names_on_line:
                    tmp_semantic_model, tmp_ret_depend = get_func_param_edge(
                        code_path, cpg, m_id, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                        IS_METHOD=False, visited=visited
                    )
                    m_actual_params = actual_params.get(m_id, {})
                    m_formal_params = formal_params.get(m_id, {}).get(call_edges[m_id], [])
                    m_params_type  = params_type.get(m_id, {}).get(call_edges[m_id], [])

                    if m_formal_params and m_actual_params:
                        tmp_semantic_model, tmp_ret_depend = _map_formal_to_actual_params(
                            tmp_semantic_model, tmp_ret_depend,
                            m_formal_params, m_actual_params, semantic_model
                        )

                    _merge_semantic_model_from_call(
                        tmp_semantic_model, tmp_ret_depend, semantic_model,
                        m_actual_params, m_formal_params, m_params_type,
                        node_method_name, object_callee_name_dict, var_name=None
                    )

        elif root_type == "return_statement":
            return_statement = root_node
            object_callee_name_dict = ast_parser.object_callee_name_dict(ast_parser.root)
            all_ids_in_rhs = ast_parser._all_identifier_texts(return_statement)
            all_ids_in_rhs_with_this = ast_parser._all_rhs_identifiers_with_this(return_statement)
            callee_ids = ast_parser._callee_identifier_texts(return_statement)
            object_creation_expression = ast_parser._object_creation_expression_texts(return_statement)
            callee_ids.extend(object_creation_expression)

            diff = [item for item in all_ids_in_rhs if item not in callee_ids or callee_ids.count(item) < all_ids_in_rhs.count(item)]
            rhs_var_ids = diff
            rhs_var_ids = set(rhs_var_ids)
            callee_ids = set(callee_ids)

            per_line_key = f"{file_name}#{str(int(file_lineno))}"
            for m_id in call_dict.get(per_line_key, []):
                node_method_name = _short_method_name_from_call_node(cpg, m_id)
                if node_method_name and node_method_name in callee_ids:
                    tmp_semantic_model, tmp_ret_depend = get_func_param_edge(
                        code_path, cpg, m_id, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                        IS_METHOD=False, visited=visited
                    )
                    m_actual_params = actual_params.get(m_id, {})
                    m_formal_params = formal_params.get(m_id, {}).get(call_edges[m_id], [])
                    m_params_type  = params_type.get(m_id, {}).get(call_edges[m_id], [])

                    if m_formal_params and m_actual_params:
                        tmp_semantic_model, tmp_ret_depend = _map_formal_to_actual_params(
                            tmp_semantic_model, tmp_ret_depend,
                            m_formal_params, m_actual_params, semantic_model
                        )

                    _merge_semantic_model_from_call(
                        tmp_semantic_model, tmp_ret_depend, semantic_model,
                        m_actual_params, m_formal_params, m_params_type,
                        node_method_name, object_callee_name_dict, var_name=None
                    )
                    return_dependency |= (tmp_ret_depend & set(params))
                    for tmp_ret_depend_item in tmp_ret_depend:
                        if "this." in tmp_ret_depend_item:
                            return_dependency.add(tmp_ret_depend_item)
            global_variables, local_variables = _get_class_and_method_variables(
                cpg, method_node, all_code, result_lines
            )
            idents_all = set()
            params_to_add = set()
            visited_return = set()
            queue = list(rhs_var_ids)
            while queue:
                curr_id = queue.pop(0)
                if curr_id in visited_return:
                    continue
                visited_return.add(curr_id)
                if curr_id in global_variables and curr_id not in params and f"this.{curr_id}" not in local_variables:
                    curr_id = "this." + curr_id
                    params_to_add.add(curr_id)
                elif curr_id in params or "this." in curr_id:
                    params_to_add.add(curr_id)
                if semantic_model[curr_id] and semantic_model[curr_id] != set():
                    queue.extend(list(semantic_model[curr_id]))
            idents_all.update(params_to_add)
            return_dependency |= idents_all

        rel_idx += 1
    
    _normalize_global_variables_with_this(
        cpg, params, method_node, all_code, result_lines, semantic_model, return_dependency
    )

    if method_node:
        merged_model, merged_ret, _ = _merge_into_cache(method_node, semantic_model, return_dependency)
        return merged_model, merged_ret

    return semantic_model, return_dependency

def get_callgraph_from_joern(cpg_dir: str):
    callgraph_path = os.path.join(cpg_dir, "callgraph.json")
    if os.path.exists(callgraph_path):
        with open(callgraph_path, "r") as f:
            callgraph = json.load(f)
    else:
        if not os.path.exists(_GET_CALLGRAPH_SCRIPT):
            raise FileNotFoundError(
                f"Joern not exists: {_GET_CALLGRAPH_SCRIPT}, cannot generate callgraph.json"
            )
        cpg_bin = os.path.normpath(os.path.join(cpg_dir, "..", "cpg.bin"))
        ret = subprocess.run(
            [
                "joern",
                "--script", _GET_CALLGRAPH_SCRIPT,
                "--param", f"cpgFile={cpg_bin}",
                "--param", f"output={callgraph_path}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ret.returncode != 0:
            raise RuntimeError(
                f"joern generate callgraph failed (exit {ret.returncode}): stderr={ret.stderr.decode(errors='replace')!r}"
            )
        if not os.path.exists(callgraph_path):
            raise FileNotFoundError(
                f"joern not generate callgraph file: {callgraph_path}"
            )
        with open(callgraph_path, "r") as f:
            callgraph = json.load(f)
    return callgraph

def preprocess(cache_dir: str):
    cpg_dir = f"{cache_dir}/cpg"
    cpg = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))

    call_graph = nx.DiGraph()
    
    methods = {}
    calls = {}
    
    method_list = []
    
    methods_full_name = {}
    for node_id, node_attrs in cpg.nodes(data=True):
        label = node_attrs.get("label", "")
        
        if label == "METHOD":
            method_name = node_attrs.get("NAME", "unknown_method")
            full_name = node_attrs.get("FULL_NAME", method_name)
            signature = node_attrs.get("SIGNATURE", "")

            if "<operator>" not in node_attrs.get("FULL_NAME"):
                methods[node_id] = {
                    "name": method_name,
                    "full_name": full_name,
                    "sub_full_name": ".".join(full_name.split(":")[0].split(".")[:-2]) + "." + method_name,
                    "signature": signature,
                    "start_line": node_attrs.get("LINE_NUMBER", 0),
                    "end_line": node_attrs.get("LINE_NUMBER_END", node_attrs.get("LINE_NUMBER", 0)),
                    "file_name": node_attrs.get("FILENAME", "")
                }
                if methods[node_id]["file_name"] != "<empty>":
                    methods_full_name[".".join(full_name.split(":")[0].split(".")[:-2]) + "." + method_name] = methods[node_id]
                if not full_name.startswith("java.lang.Class") and not full_name.startswith("java.lang.reflect"):
                    method_list.append(full_name)
                    call_graph.add_node(full_name, 
                                    label=node_id,
                                    type="METHOD")

    for method in methods:
        if methods[method]["file_name"] == "<empty>" and methods[method]["sub_full_name"] in methods_full_name:
            full_name = methods[method]["full_name"]
            class_name = "/".join(full_name.split(":")[0].split(".")[:-1])
            if os.path.exists(os.path.join(cache_dir, "code", class_name + ".java")):
                methods[method]["file_name"] = os.path.join(cache_dir, "code", class_name + ".java")
                continue
            methods[method] = methods_full_name[methods[method]["sub_full_name"]].copy()
            methods[method]["full_name"] = full_name

    callgraph = get_callgraph_from_joern(cpg_dir)
    
    for method in methods:
        for call in callgraph[str(method)]:
            if "lineNumber" not in call:
                continue
            if "<operator>" in call['methodFullName']:
                continue
            if "_id" in call:
                calls[str(call['_id'])] = {
                    "name": str(call['name']),
                    "method_full_name": str(methods[method]["full_name"]),
                    "line_number": str(call['lineNumber']),
                    "start_line": str(methods[method]['start_line']),
                    "end_line": str(methods[method]['end_line']),
                    "file_name": str(methods[method]["file_name"]),
                }
            elif "id" in call:
                calls[str(call['id'])] = {
                    "name": str(call['name']),
                    "method_full_name": str(methods[method]["full_name"]),
                    "line_number": str(call['lineNumber']),
                    "start_line": str(methods[method]['start_line']),
                    "end_line": str(methods[method]['end_line']),
                    "file_name": str(methods[method]["file_name"]),
                }
    return calls

def get_types(cpg_dir: str):
    inherent_types = {}
    deinherent_types = {}
    if os.path.exists(os.path.join(cpg_dir, "types.json")):
        with open(os.path.join(cpg_dir, "types.json"), "r") as f:
            types = json.load(f)
    else:
        process = subprocess.Popen(
            ["joern", "--script", "./scripts/get_types.sc", "--param", f"cpgFile=../cpg.bin", "--param", f"output=types.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cpg_dir,
        )

        stdout, stderr = process.communicate()

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

def is_interface(code_dir: str, cpg, node_id: str) -> bool:
    is_interface_method = False
    has_annotation = False
    return is_interface_method, has_annotation
            
def process_interface_function(cpg, node_id: str, inherent_types: dict, deinherent_types: dict) -> str | None:
    node_method = cpg.nodes[node_id].get("FULL_NAME", "")
    if not node_method:
        return None

    node_type = node_method.split(":")[0].rpartition('.')[0]
    
    if node_type in deinherent_types:
        potential_methods = deinherent_types[node_type]

        for method_name in potential_methods:
            redirect_method_name = node_method.replace(node_type, method_name)
            matching_node = next((n for n, attrs in cpg.nodes(data=True) if attrs.get("label") == "METHOD" and attrs.get("FULL_NAME") == redirect_method_name), None)
            if matching_node:
                return matching_node

    return None

def generate_interface_annotation_function_semantic_model_prompt(code_snippet: str) -> str:
    system_prompt = """
        You are an expert in analyzing the relationships between function parameters and return values in annotated interface methods.
        **Input:**

        - A interface method code snippet including annotation and method head

        **Output:**

        - A detailed analysis of the relationships between method parameters and the return value, formatted as '1':['2'] or '-1': ['2']. The relationships are determined by the position of the parameters and return values. If no relationships exist, return an empty dictionary {}.

        **Example:**

        - Given method:

        ```
        public int get_G(int g, int k) {
            g = k;
            return g;
        }
        ```

        **Analysis relationship:**

        ```
        {'1':['2'], '-1':['2']}
        ```

        Explanation:

        - `'1':['2']` means the first parameter 'g' (position 1) is assigned the value of the second parameter 'k' (position 2), indicating a relationship where parameter 2 affects parameter 1.
        - `'-1':['2']` means the return value (position -1) is determined by the second parameter 'k' (position 2), which is parameter 'g' set by the second parameter 'k' (position 2).

        **Remember:**

        - The analysis should clearly identify how parameters impact each other or the return value, based on the rules provided.
        - Return only the analysis results. If no relationships exist, return an empty dictionary {}.
        - If no relationships exist, return an empty dictionary {}.
    """

    user_prompt = f"""
        Given the method code snippet:

        ```
        {code_snippet}
        ```

        Please analyze the relationships between the parameters and return value based on the following rules:

        1. Identify the impact of input parameters on each other.
        2. Identify how the input parameters influence the return value.
        3. Use the format `'1':['2'] or '-1': ['2']` to represent the relationship:
        - `'1':['2']` means the first parameter (position 1) is affected by the second parameter (position 2).
        - `'-1':['2']` means the return value (position -1) is determined by the second parameter (position 2).
        4. If there is no relationship between the return value and the parameters, or between the parameters themselves, return an empty dictionary {{}}.

        **Example:**
        For the method:

        ```
        public int get_G(int g, int k) {{
            g = k;
            return g;
        }}
        ```

        Your output should be:

        ```
        {{'1':['2'], '-1':['2']}}
        ```
    """

    return system_prompt, user_prompt

def process_interface_annotation_function(code_path, cpg, node_id: str) -> str | None:
    line_number_start = cpg.nodes[node_id].get("LINE_NUMBER", None)
    line_number_end = cpg.nodes[node_id].get("LINE_NUMBER_END", None)
    file_path = cpg.nodes[node_id].get("FILENAME", None)

    if line_number_start is None or line_number_end is None or file_path is None:
        return {}, []

    if int(line_number_end) == 0:
        return {}, []

    full_file_path = os.path.join(code_path, file_path)
    with open(full_file_path, "r") as f:
        lines = f.readlines()
        method_code = "".join(lines[int(line_number_start) - 1:int(line_number_end)])
    system_prompt, user_prompt = generate_interface_annotation_function_semantic_model_prompt(method_code)
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
    except Exception as e:
        print(f"LLM call failed: {e}")
        return {}, []
    params_relation = {}
    return_depend = []
    if response["choices"]:
        for choice in response["choices"]:
            raw_content = choice["message"]["content"].strip().replace("'", '"')
            if not raw_content:
                continue
            try:
                content = json.loads(raw_content)
            except json.JSONDecodeError:
                try:
                    content = ast.literal_eval(raw_content)
                except (ValueError, SyntaxError) as parse_err:
                    print(f"Cannot parse LLM returned content: {raw_content} ({parse_err})")
                    continue
            for key in content.keys():
                if str(key) == "-1":
                    return_depend = content[key]
                else:
                    params_relation[key] = content[key]
            return params_relation, return_depend
    else:
        return {}, []


def semantic_model(code_path, cache_dir, cpg, call_node_info):
    actual_params: dict[str, dict[int, list[str]]] = defaultdict(dict)
    method_formal_params: dict[str, dict[str, str]] = defaultdict(dict)
    formal_params: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    params_type: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    call_node_set: set[str] = set()
    method_node_set: set[str] = set()

    param_result = {}
    result = []
    annotation_interface_param_depend = defaultdict(lambda: defaultdict(list))
    annotation_interface_param_ret_depend = defaultdict(list)

    for node, attrs in cpg.nodes(data=True):
        if (
            attrs.get("label") == "CALL"
            and attrs.get("METHOD_FULL_NAME")
            and not str(attrs["METHOD_FULL_NAME"]).startswith("<operator>")
        ):
            call_node_set.add(node)
        if (
            attrs.get("label") == "METHOD"
            and attrs.get("FULL_NAME")
            and not str(attrs["FULL_NAME"]).startswith("<operator>")
        ):
            method_node_set.add(node)

    call_edges: dict[str, str] = {}
    call_edges_reverse: dict[str, str] = {}
    call_dict: dict[str, list] = defaultdict(list)

    inherent_types, deinherent_types = get_types(f"{cache_dir}/cpg")
    for u, v, d in cpg.edges(data=True):

        lbl = d.get("label")
        if lbl == "ARGUMENT" and u in call_node_set:
            v_node = cpg.nodes[v]
            type_full_name = v_node.get("TYPE_FULL_NAME")
            name = v_node.get("NAME")
            idx_raw = v_node.get("ARGUMENT_INDEX")
            try:
                index = int(idx_raw)
            except (TypeError, ValueError):
                index = None

            if name is not None and index is not None and index > 0:
                if name.startswith("<operator>."):
                    param_code = cpg.nodes[v].get("CODE")
                    names = []
                    if param_code:
                        param_code_ast = ASTParser(param_code, Language.JAVA)
                        param_identifiers_nodes = param_code_ast.get_all_identifier_node()
                        for param_identifier_node in param_identifiers_nodes:
                            names.append(param_identifier_node.text.decode("utf-8"))
                    if not names:
                        names = [name]
                else:
                    names = [name]
                actual_params[u][index - 1] = names

        elif lbl == "CALL" and u in call_node_set:
            is_interface_method, has_annotation = is_interface(code_path, cpg, v)
            if is_interface_method and not has_annotation:
                tmp_node_id = process_interface_function(cpg, v, inherent_types, deinherent_types)
                if tmp_node_id:
                    v = tmp_node_id
            elif is_interface_method and has_annotation:
                tmp_semantic_model, tmp_return_dependency = process_interface_annotation_function(code_path, cpg, v)
                single_result = ""
                single_result += f"{cpg.nodes[v]['FULL_NAME']} "
                for semantic_key, semantic_vals in tmp_semantic_model.items():
                    single_result += f"{semantic_key}->{semantic_vals} "
                for tmp_return_dependency_item in tmp_return_dependency:
                    single_result += f"{tmp_return_dependency_item}->-1 "
                result.append(single_result.strip())

                method_head = cpg.nodes[v].get("CODE")
                if cpg.nodes[v].get("NAME") == "<init>":
                    method_head = "init " + method_head
                ast_parser_head = ASTParser(method_head, Language.JAVA)
                method_decls = ast_parser_head.get_method_declaration() or []
                
                tmp_param_pos_dict = []
                for method_decl in method_decls:
                    parameters_node = method_decl.child_by_field_name("parameters") if method_decl else None
                    for param_node in parameters_node.children:
                        if param_node.type == "formal_parameter":
                            name_node = param_node.child_by_field_name("name")
                            if name_node is not None:
                                param_name = name_node.text.decode("utf-8")
                                tmp_param_pos_dict.append(param_name)
                tmp_param_name_semantic_model = {}
                for key, _ in tmp_semantic_model.items():
                    if tmp_param_pos_dict[int(key)]:
                        for param in tmp_semantic_model[key]:
                            if tmp_param_pos_dict[int(param)]:
                                tmp_param_name_semantic_model[tmp_param_pos_dict[int(key)]].append(tmp_param_pos_dict[int(param)])
                annotation_interface_param_depend[v] = tmp_param_name_semantic_model
                annotation_interface_param_ret_depend[v] = tmp_return_dependency

            call_edges[u] = v
            call_edges_reverse[v] = u
            method_full_name = cpg.nodes[v].get("FULL_NAME", "")
            line_number = call_node_info[u].get("line_number", "")
            file_path = call_node_info[u].get("file_name", "")
            if method_full_name and line_number:
                m = re.match(
                    r'^(?P<fullName>[^:]+?)\.(?P<method>[^:]+?):(?P<ret>.+?)\((?P<params_type>.*)\)$',
                    str(method_full_name),
                )
                if m:
                    raw_params = m.group("params_type") or ""
                    params_type[u][v] = [p.strip() for p in raw_params.split(",")] if raw_params else []
                    if file_path and file_path != "<empty>":
                        key = f"{file_path}#{str(int(line_number))}"
                        call_dict[key].append(u)

    for node in call_node_set:
        callee_node = call_edges.get(node)
        if not callee_node:
            continue
        method_head = cpg.nodes[callee_node].get("CODE")
        if cpg.nodes[callee_node].get("NAME") == "<init>" and method_head == "<empty>":
            formal_params[node][callee_node] = []
            continue
        if not method_head or method_head == "<empty>":
            formal_params[node][callee_node] = []
            continue

        if cpg.nodes[callee_node].get("NAME") == "<init>":
            method_head = "init " + method_head
        ast_parser_head = ASTParser(method_head, Language.JAVA)
        method_decls = ast_parser_head.get_method_declaration() or []
        
        for method_decl in method_decls:
            parameters_node = method_decl.child_by_field_name("parameters") if method_decl else None
            if not parameters_node:
                continue
            if parameters_node.children == None:
                formal_params[node][callee_node] = []
            for param_node in parameters_node.children:
                if param_node.type == "formal_parameter":
                    name_node = param_node.child_by_field_name("name")
                    if name_node is not None:
                        param_name = name_node.text.decode("utf-8")
                        formal_params[node][callee_node].append(param_name)
    
    for method_node in method_node_set:

        method_head = cpg.nodes[method_node].get("CODE")
        if cpg.nodes[method_node].get("NAME") == "<init>" and method_head == "<empty>":
            method_formal_params[method_node] = {}
            continue
        if not method_head or method_head == "<empty>":
            method_formal_params[method_node] = {}
            continue
        
        if cpg.nodes[method_node].get("NAME") == "<init>":
            method_head = "init " + method_head
        ast_parser_head = ASTParser(method_head, Language.JAVA)
        method_decls = ast_parser_head.get_method_declaration() or []

        method_formal_params_type = []
        pattern = r"\((.*)\)"
        match = re.search(pattern, cpg.nodes[method_node]['FULL_NAME'])

        if match:
            param_types = match.group(1).split(",")
            method_formal_params_type = [p.strip().split(".")[-1] for p in param_types]

        for method_decl in method_decls:
            if "<unresolvedSignature>" in cpg.nodes[method_node]['FULL_NAME']:
                method_formal_params_type = []
                pattern = r"\((.*)\)"
                match = re.search(pattern, method_decl.text.decode("utf-8"))
                if match:
                    param_types = match.group(1).split(",")
                    method_formal_params_type = [p.strip().split(" ")[0].split(".")[-1] for p in param_types]
            parameters_node = method_decl.child_by_field_name("parameters") if method_decl else None

            if not parameters_node:
                continue
            if parameters_node.children == None:
                method_formal_params[method_node] = {}
            for param_node in parameters_node.children:
                if param_node.type == "formal_parameter":
                    name_node = param_node.child_by_field_name("name")
                    if name_node:
                        param_name = name_node.text.decode("utf-8")
                        method_formal_params[method_node][param_name] = method_formal_params_type[len(method_formal_params[method_node])]

    for node in method_node_set:
        cached_semantic = None
        cached_ret = None
        for _ in range(MAX_FIXPOINT_ITERS):
            semantic_model, return_dependency = get_func_param_edge(
                code_path, cpg, node, call_edges, call_edges_reverse, call_dict, formal_params, actual_params, params_type, annotation_interface_param_depend, annotation_interface_param_ret_depend,
                IS_METHOD=True, visited=None
            )
            merged_model, merged_ret, changed = _merge_into_cache(node, semantic_model, return_dependency)
            cached_semantic, cached_ret = merged_model, merged_ret

        semantic_model = cached_semantic
        return_dependency = cached_ret

        single_result = ""
        single_result += f"{cpg.nodes[node]['FULL_NAME']} "
        for semantic_key, semantic_vals in semantic_model.items():
            if semantic_key in method_formal_params.get(node, []):
                for val in list(semantic_vals):
                    if val in method_formal_params.get(node, []):
                        param_names = list(method_formal_params[node].keys())
                        key_index = param_names.index(semantic_key) + 1
                        val_index = param_names.index(val) + 1
                        if not _is_primitive(method_formal_params[node][semantic_key]):
                            single_result += f"{val_index}->{key_index} "
                    elif "this." in val:
                        param_names = list(method_formal_params[node].keys())
                        key_index = param_names.index(semantic_key) + 1
                        single_result += f"0->{key_index} "
            elif "this." in semantic_key:
                for val in list(semantic_vals):
                    if val in method_formal_params.get(node, []):
                        param_names = list(method_formal_params[node].keys())
                        val_index = param_names.index(val) + 1
                        single_result += f"{val_index}->0 "
        added_this = False
        for ret_dep in return_dependency:
            if ret_dep in method_formal_params.get(node, []):
                param_names = list(method_formal_params[node].keys())
                ret_index = param_names.index(ret_dep) + 1
                single_result += f"{ret_index}->-1 "
            elif "this." in ret_dep:
                if not added_this:
                    single_result += f"0->-1 "
                added_this = True
        result.append(single_result.strip())

        param_result[node] = (semantic_model, return_dependency)

    output_path = os.path.join(cache_dir, "data_depend_dict.json")
    serializable_result = {}
    for node, deps in param_result.items():
        serializable_result[node] = {}
        semantic_model, return_dependency = deps
        for key, value in semantic_model.items():
            if isinstance(value, set):
                serializable_result[node][key] = list(value)
            elif isinstance(value, dict):
                serializable_result[node][key] = {k: list(v) if isinstance(v, set) else v for k, v in value.items()}
        serializable_result[node]["return_dependency"] = list(return_dependency)
    with open(output_path, 'w') as f:
        json.dump(serializable_result, f)

    output_path = os.path.join(cache_dir, "semantic_model.json")
    with open(output_path, 'w') as f:
        json.dump(result, f)
