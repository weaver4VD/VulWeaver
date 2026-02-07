from ctypes import pointer
import json
import os
from shlex import join
import subprocess
import sys
import cpu_heater
from tqdm import tqdm

import networkx as nx
import Constructing_Enhanced_UDG.joern as joern
from Constructing_Enhanced_UDG.ast_parser import ASTParser
from Constructing_Enhanced_UDG.codefile import create_code_tree
from Constructing_Enhanced_UDG.common import Language
from .project import Method, Project
from .target import Target
from Constructing_Enhanced_UDG.joern_enhance import get_types, preprocess
from Constructing_Enhanced_UDG.parallel_edges import init_token_stats, get_token_stats, reset_token_stats
import time

def init_single_method_dir(method, cache_dir):
    base_cache_dir = cache_dir.split("/method/")[0] if "/method/" in cache_dir else cache_dir
    
    method_dir = f"{cache_dir}/method/{method.signature_r}"
    dot_dir = f"{cache_dir}/method/{method.signature_r}/dot"

    os.makedirs(dot_dir, exist_ok=True)
    os.makedirs(method_dir, exist_ok=True)

    method.method_dir = method_dir
    method.write_code(method_dir)
    method.write_dot(dot_dir)

    original_code_path = f"{base_cache_dir}/code"
    os.makedirs(original_code_path, exist_ok=True)
    method.original_code_path = original_code_path
    method.base_cache_dir = base_cache_dir

    return method_dir

def slicing_single_method(
    target_repo: Target, method_signature, target_project: Project, cache_dir: str, semantic_model: bool, callee_lines = None
):
    if callee_lines is None:
        callee_lines = target_repo.line_matching[method_signature]
        
    method = target_project.get_method(method_signature, callee_lines)
    assert method is not None

    target_callee_lines = set()
    for callee_line in callee_lines:
        if method.start_line <= callee_line <= method.end_line:
            target_callee_lines.add(callee_line)
    init_single_method_dir(method, cache_dir)
    method.counterpart = method
    print(f"Begin single method slicing")
    base_cache_dir = method.base_cache_dir
    actual_original_code_path = f"{base_cache_dir}/code"

    slice_results = method.slice_by_diff_lines_detect(
        target_callee_lines,
        cache_dir,
        semantic_model,
        original_code_path=actual_original_code_path,
        need_criteria_identifier=True,
        write_dot=True,
        role="target",
    )

    return slice_results

def callee_worker_fn(pre_project: Project, ref_id, cnt, cache_dir, enhanced=False):
    if "<operator>" in ref_id:
        return None
    callees = pre_project.get_callee(ref_id, cache_dir, enhanced)
    if callees is None:
        return None
    return callees, cnt + 1, ref_id

def caller_worker_fn(pre_project: Project, ref_id, cnt, cache_dir, enhanced=False):
    if "<operator>" in ref_id:
        return None
    callers = pre_project.get_caller(ref_id, cache_dir, enhanced)
    if callers is None:
        return None
    return callers, cnt + 1, ref_id

def dfs_find_caller_intersection(caller_method_name, edge_tree, points, setter_edges, project, cache_dir, visited=None, path_edges=None, memo_cache=None):
    """
    DFS to find intersection with main call graph
    
    Args:
        caller_method_name: current caller (format: file_name#method_name#line_number)
        edge_tree: call edge tree {method_signature: {(caller, line_number, method_line_number), ...}}
        points: main call graph node set
        setter_edges: intersecting call edges
        project: project object
        cache_dir: cache directory
        visited: visited nodes (avoid cycles)
        path_edges: edges on current path (for backtracking)
        memo_cache: memo {method_signature: bool}, whether can reach points
    """
    if visited is None:
        visited = set()
    if path_edges is None:
        path_edges = []
    if memo_cache is None:
        memo_cache = {}
    if caller_method_name in memo_cache:
        can_reach = memo_cache[caller_method_name]
        if can_reach:
            for edge in path_edges:
                setter_edges.add(edge)
        return can_reach
    if caller_method_name in visited:
        return False
    
    visited.add(caller_method_name)
    if caller_method_name in points:
        for edge in path_edges:
            setter_edges.add(edge)
        memo_cache[caller_method_name] = True
        visited.remove(caller_method_name)
        return True
    res = caller_worker_fn(project, caller_method_name, 0, cache_dir)
    if res is None:
        memo_cache[caller_method_name] = False
        visited.remove(caller_method_name)
        return False
    
    callers, _, _ = res
    can_reach_points = False
    for caller in callers:
        line_number = caller.split("__split__")[0]
        caller_file_method = caller.split("__split__")[1]
        method_line_number = caller.split("__split__")[2]
        caller_method_name_next = f"{caller_file_method}#{line_number}"
        edge = (caller_method_name_next, caller_method_name, line_number, method_line_number)
        path_edges.append(edge)
        can_reach_next = dfs_find_caller_intersection(
            caller_method_name_next, 
            edge_tree, 
            points, 
            setter_edges, 
            project, 
            cache_dir, 
            visited, 
            path_edges,
            memo_cache,
        )
        path_edges.pop()
        if not can_reach_next and caller_method_name_next not in memo_cache:
            memo_cache[caller_method_name_next] = False
        
        if can_reach_next:
            can_reach_points = True
    memo_cache[caller_method_name] = can_reach_points
    visited.remove(caller_method_name)
    return can_reach_points

def dfs_find_callee_intersection(callee_method_name, edge_tree, points, getter_edges, project, cache_dir, visited=None, path_edges=None, memo_cache=None):
    """
    DFS to find intersection with main call graph (downward search).

    Args:
        callee_method_name: current callee (format: file_name#method_name#line_number)
        edge_tree: call edge tree {method_signature: {(callee, line_number, method_line_number), ...}}
        points: main call graph node set
        getter_edges: intersecting call edges
        project: project object
        cache_dir: cache directory
        visited: visited nodes (avoid cycles)
        path_edges: edges on current path (for backtracking)
        memo_cache: memo {method_signature: bool}, whether can reach points
    """
    if visited is None:
        visited = set()
    if path_edges is None:
        path_edges = []
    if memo_cache is None:
        memo_cache = {}
    if callee_method_name in memo_cache:
        can_reach = memo_cache[callee_method_name]
        if can_reach:
            for edge in path_edges:
                getter_edges.add(edge)
        return can_reach
    if callee_method_name in visited:
        return False

    visited.add(callee_method_name)
    if callee_method_name in points:
        for edge in path_edges:
            getter_edges.add(edge)
        memo_cache[callee_method_name] = True
        visited.remove(callee_method_name)
        return True
    res = callee_worker_fn(project, callee_method_name, 0, cache_dir)
    if res is None:
        memo_cache[callee_method_name] = False
        visited.remove(callee_method_name)
        return False

    callees, _, _ = res
    can_reach_points = False
    for callee in callees:
        line_number = callee["callee_linenumber"]
        callee_file_method = callee["callee_method_name"]
        method_line_number = callee["method_line_number"]
        callee_method_name_next = f"{callee_file_method}#{line_number}"
        edge = (callee_method_name, callee_method_name_next, line_number, method_line_number)
        path_edges.append(edge)
        can_reach_next = dfs_find_callee_intersection(
            callee_method_name_next,
            edge_tree,
            points,
            getter_edges,
            project,
            cache_dir,
            visited,
            path_edges,
            memo_cache,
        )
        path_edges.pop()
        if can_reach_next is False and callee_method_name_next not in memo_cache:
            memo_cache[callee_method_name_next] = False
        
        if can_reach_next:
            can_reach_points = True
    memo_cache[callee_method_name] = can_reach_points
    visited.remove(callee_method_name)
    return can_reach_points

def process_setter_callers(setter_method_signature, edge_tree, points, setter_edges, project, cnt, cache_dir, memo_cache=None):
    """
    Process setter callers until intersection with main call graph.

    Args:
        memo_cache: memo {method_signature: bool}, whether can reach points
    """
    if memo_cache is None:
        memo_cache = {}
    if setter_method_signature in memo_cache and not memo_cache[setter_method_signature]:
        return cnt
    res = caller_worker_fn(
        project, setter_method_signature, cnt, cache_dir
    )

    if res is None:
        memo_cache[setter_method_signature] = False
        return cnt

    callers, cnt, ref_id = res
    can_reach_points = False
    for caller in callers:
        line_number = caller.split("__split__")[0]
        caller_file_method = caller.split("__split__")[1]
        method_line_number = caller.split("__split__")[2]
        caller_method_name = f"{caller_file_method}#{line_number}"
        edge_tree[setter_method_signature].add((caller, line_number, method_line_number))
        if caller_method_name in points:
            setter_edges.add((caller_method_name, setter_method_signature, line_number, method_line_number))
            can_reach_points = True
        else:
            if caller_method_name in memo_cache:
                if memo_cache[caller_method_name]:
                    setter_edges.add((caller_method_name, setter_method_signature, line_number, method_line_number))
                    can_reach_points = True
            else:
                initial_edge = (caller_method_name, setter_method_signature, line_number, method_line_number)
                if dfs_find_caller_intersection(
                    caller_method_name,
                    edge_tree,
                    points,
                    setter_edges,
                    project,
                    cache_dir,
                    path_edges=[initial_edge],
                    memo_cache=memo_cache
                ):
                    can_reach_points = True
    memo_cache[setter_method_signature] = can_reach_points
    return cnt

def setter_worker_fn(setter_method_name, method_signature_dict, points, project, cnt, cache_dir, memo_cache=None):
    if setter_method_name not in method_signature_dict.keys():
        return None
    
    setter_method_signature = method_signature_dict[setter_method_name]
    local_setter_edges = set()
    local_edge_tree = {}
    local_edge_tree[setter_method_signature] = set()
    local_cnt = cnt
    if memo_cache is None:
        memo_cache = {}
    local_cnt = process_setter_callers(
        setter_method_signature, local_edge_tree, points, local_setter_edges, project, local_cnt, cache_dir, memo_cache
    )

    return local_setter_edges, local_edge_tree, local_cnt

def getter_setter(setter_method_names, method_signature_dict, points, edges, project, cnt, cache_dir, max_workers):
    setter_edges = set()
    edge_tree = {}
    memo_cache = {}
    for setter_method_name in setter_method_names:
        res = setter_worker_fn(setter_method_name, method_signature_dict, points, project, cnt, cache_dir, memo_cache)
        if res is None:
            continue
        local_setter_edges, local_edge_tree, local_cnt = res
        setter_edges.update(local_setter_edges)
        for method_sig, edge_set in local_edge_tree.items():
            if method_sig not in edge_tree:
                edge_tree[method_sig] = set()
            edge_tree[method_sig].update(edge_set)
        cnt = max(cnt, local_cnt)
    edges.update(setter_edges)

def process_getter_callees(getter_method_signature, edge_tree, points, getter_edges, project, cnt, cache_dir, memo_cache=None):
    if memo_cache is None:
        memo_cache = {}
    
    if getter_method_signature in memo_cache and not memo_cache[getter_method_signature]:
        return cnt
    
    res = callee_worker_fn(
        project, getter_method_signature, cnt, cache_dir
    )

    if res is None:
        memo_cache[getter_method_signature] = False 
        return cnt

    callees, cnt, ref_id = res
    can_reach_points = False
    for callee in callees:
        line_number = callee["callee_linenumber"]
        callee_file_method = callee["callee_method_name"]
        method_line_number = callee["method_line_number"]
        callee_method_name = f"{callee_file_method}#{line_number}"
        edge_tree[getter_method_signature].add((callee_method_name, line_number, method_line_number))
        if callee_method_name in points:
            getter_edges.add((callee_method_name, getter_method_signature, line_number, method_line_number))
            can_reach_points = True
        else:
            if callee_method_name in memo_cache:
                if memo_cache[callee_method_name]:
                    getter_edges.add((callee_method_name, getter_method_signature, line_number, method_line_number))
                    can_reach_points = True
            else:
                initial_edge = (callee_method_name, getter_method_signature, line_number, method_line_number)
                if dfs_find_callee_intersection(
                    callee_method_name,
                    edge_tree,
                    points,
                    getter_edges,
                    project,
                    cache_dir,
                    path_edges=[initial_edge],
                    memo_cache=memo_cache
                ):
                    can_reach_points = True
    memo_cache[getter_method_signature] = can_reach_points
    return cnt

def getter_worker_fn(getter_method_name, method_signature_dict, points, project, cnt, cache_dir, memo_cache=None):
    if getter_method_name not in method_signature_dict.keys():
        return None
    
    getter_method_signature = method_signature_dict[getter_method_name]
    local_getter_edges = set()
    local_edge_tree = {}
    local_edge_tree[getter_method_signature] = set()
    local_cnt = cnt
    if memo_cache is None:
        memo_cache = {}
    local_cnt = process_getter_callees(
        getter_method_signature, local_edge_tree, points, local_getter_edges, project, local_cnt, cache_dir, memo_cache
    )

    return local_getter_edges, local_edge_tree, local_cnt

def setter_getter(getter_method_names, method_signature_dict, points, edges, project, cnt, cache_dir, max_workers):
    getter_edges = set()
    edge_tree = {}
    memo_cache = {}
    for getter_method_name in getter_method_names:
        res = getter_worker_fn(getter_method_name, method_signature_dict, points, project, cnt, cache_dir, memo_cache)
        if res is None:
            continue
        local_getter_edges, local_edge_tree, local_cnt = res
        getter_edges.update(local_getter_edges)
        for method_sig, edge_set in local_edge_tree.items():
            if method_sig not in edge_tree:
                edge_tree[method_sig] = set()
            edge_tree[method_sig].update(edge_set)
        cnt = max(cnt, local_cnt)
    edges.update(getter_edges)

def get_callgraph(repo, project, cache_dir, max_workers, enhanced=False):
    from collections import deque
    import gc
    edges = set()
    points = set()
    method_signature_dict = {}
    inherent_types, deinherent_types = get_types(f"{cache_dir}/cpg")
    project.inherent_types = inherent_types
    project.deinherent_types = deinherent_types
    metadata_files = {
        "method_name_dict": f"{cache_dir}/cpg/method_name_dict.json",
        "calls": f"{cache_dir}/cpg/call.json",
        "methods": f"{cache_dir}/cpg/method.json"
    }
    
    for attr, path in metadata_files.items():
        if os.path.exists(path):
            with open(path, "r") as f:
                setattr(project, attr, json.load(f))
    
    methods = getattr(project, "methods", {})
    method_list = set()
    for method_id, method_info in methods.items():
        method_list.add(method_info["full_name"])
        method_signature_dict[method_info["name"]] = f"{method_info['file_name']}#{method_info['name']}#{method_info['start_line']}"
    project.method_list = list(method_list)
    dot_path = f"{cache_dir}/call_graph.dot"
    if os.path.exists(dot_path):
        project.call_graph_dot = nx.nx_agraph.read_dot(dot_path)
        project._load_call_graph_cache()
        gc.collect()
    callee_queue = deque()
    caller_queue = deque()
    
    setter_method_names = set()
    getter_method_names = set()

    for method_signature in repo.matching_methods:
        points.add(method_signature)
        callee_queue.append((method_signature, 0))
        caller_queue.append((method_signature, 0))
    get_call_time_start = time.time()
    while callee_queue:
        ref_id, cnt = callee_queue.popleft()
        if "<operator>" in ref_id:
            continue
            
        callees = project.get_callee(ref_id, cache_dir, enhanced)
        if not callees:
            continue
            
        for point in callees:
            callee_name = point["callee_method_name"]
            edges.add((ref_id, callee_name, point["callee_linenumber"], point["method_line_number"]))
            
            if callee_name not in points:
                points.add(callee_name)
                parts = callee_name.split("#")
                name_part = parts[-1] if len(parts) == 2 else (parts[-2] if len(parts) == 3 else None)
                if name_part:
                    if name_part.startswith("get"):
                        setter_method_names.add(name_part.replace("get", "set", 1))
                    elif name_part.startswith("set"):
                        getter_method_names.add(name_part.replace("set", "get", 1))
                
                callee_queue.append((callee_name, cnt + 1))
    while caller_queue:
        ref_id, cnt = caller_queue.popleft()
        if "<operator>" in ref_id:
            continue
            
        callers = project.get_caller(ref_id, cache_dir, enhanced)
        if not callers:
            continue
            
        for caller in callers:
            parts = caller.split("__split__")
            if len(parts) < 3: continue
            line_number, caller_file_method, method_line_number = parts[0], parts[1], parts[2]
            caller_method_name = f"{caller_file_method}#{line_number}"
            
            edges.add((caller_method_name, ref_id, line_number, method_line_number))
            
            if caller_method_name not in points:
                points.add(caller_method_name)
                parts_cn = caller_method_name.split("#")
                name_part = parts_cn[-1] if len(parts_cn) == 2 else (parts_cn[-2] if len(parts_cn) == 3 else None)
                if name_part:
                    if name_part.startswith("get"):
                        setter_method_names.add(name_part.replace("get", "set", 1))
                    elif name_part.startswith("set"):
                        getter_method_names.add(name_part.replace("set", "get", 1))
                
                caller_queue.append((caller_method_name, cnt + 1))
    get_call_time_end = time.time()
    if setter_method_names or getter_method_names:
        getter_setter_time_start = time.time()
        print(f"Processing getter_setter: setter={len(setter_method_names)}, getter={len(getter_method_names)}")
        getter_setter(setter_method_names, method_signature_dict, points, edges, project, 0, cache_dir, max_workers)
        setter_getter(getter_method_names, method_signature_dict, points, edges, project, 0, cache_dir, max_workers)
        getter_setter_time_end = time.time()
        print(f"Getter_setter processing done")
        gc.collect()

    return points, edges


def get_call(target, project, cache_dir, max_workers, enhanced=False):
    import gc
    original_cache_dir = cache_dir
    if "/method/" in cache_dir:
        cache_dir = cache_dir.split("/method/")[0]
    
    points, edges = get_callgraph(target, project, cache_dir, max_workers, enhanced)
    
    call = {
        "points": list(points),
        "edges": list(edges)
    }
    call_json_path = f"{original_cache_dir}/call.json"
    with open(call_json_path, "w") as fp:
        json.dump(call, fp, indent=4)
    del points
    del edges
    gc.collect()

    return call

def slice_per_callee(
    target_repo: Target,
    target_project: Project,
    cache_dir: str,
    callgraph: dict,
    sliced_results,
    method_signature,
    visited,
    level,
    is_pre,
    language,
    callee_name,
    semantic_model: bool,
    data_depend_dicts: dict = None,
    call_graph_enhanced: dict = None
):
    (
        slice_result_lines,
        lines,
        criteria_identifier,
    ) = (
        sliced_results[0],
        sliced_results[7],
        sliced_results[9],
    )
    if is_pre:
        call_edges = callgraph["edges"]
    else:
        call_edges = callgraph["edges"]
    base_cache_dir = cache_dir.split("/method/")[0] if "/method/" in cache_dir else cache_dir
    if hasattr(target_project, "joern") and target_project.joern is not None:
        actual_original_code_path = f"{target_project.joern.path}/code"
    else:
        actual_original_code_path = f"{base_cache_dir}/code"
    for call_edge in call_edges:
        if call_edge[2] == 'outside_project':
            continue
        if int(call_edge[2]) in slice_result_lines and (call_edge[0] == method_signature or "#".join(call_edge[0].split("#")[0:2]) == method_signature):
            caller_method = target_project.get_method(call_edge[0], call_edge[2])
            callee_method = target_project.get_method(call_edge[1])
            if callee_method is None:
                continue
            target_args = set()
            assignment_var = ""
            if semantic_model and caller_method is not None:
                caller_method_id = caller_method._pdg.method_node_id
                if data_depend_dicts is None:
                    data_depend_dict_path = os.path.join(base_cache_dir, "cpg", "data_depend_dict.json")
                    if os.path.exists(data_depend_dict_path):
                        with open(data_depend_dict_path, "r") as file:
                            data_depend_dicts = json.load(file)
                    else:
                        data_depend_dicts = {}
                
                data_depend_dict = data_depend_dicts.get(caller_method_id, {})
                
                if call_graph_enhanced is None:
                    call_graph_enhanced_path = os.path.join(base_cache_dir, "cpg", "callgraph.json")
                    if os.path.exists(call_graph_enhanced_path):
                        with open(call_graph_enhanced_path, 'r') as file:
                            call_graph_enhanced = json.load(file)
                    else:
                        call_graph_enhanced = {}
                
                caller_method_calls = call_graph_enhanced.get(caller_method_id, [])
                for caller_method_call in caller_method_calls:
                    if (isinstance(callee_name, list) and caller_method_call["name"] in callee_name) or (isinstance(callee_name, str) and caller_method_call["name"] == callee_name):
                        call_parser = ASTParser(lines[int(caller_method_call["lineNumber"])], language)
                        local_decls = call_parser.get_all_assign_node_java()
                        assignment_expressions = call_parser.get_assignment_expression()
                        if local_decls:
                            for local_decl in local_decls:
                                declarator = local_decl.child_by_field_name("declarator")
                                if declarator:
                                    assignment_var = declarator.child_by_field_name("name").text.decode("utf-8")
                        elif assignment_expressions:
                            for assignment_expression in assignment_expressions:
                                left = assignment_expression.child_by_field_name("left")
                                if left:
                                    assignment_var = left.text.decode("utf-8")

                        if language == Language.JAVA:
                            call_nodes = call_parser.query_all("(method_invocation)@name")
                        else:
                            call_nodes = call_parser.query_all("(call_expression)@name")
                        
                        for node in call_nodes:
                            if language == Language.JAVA:
                                child = node.child_by_field_name("name")
                            else:
                                child = node.child_by_field_name("function")
                            args = []
                            call_arguments_node = node.child_by_field_name("arguments")
                            if call_arguments_node is None:
                                continue
                            for call_arg in call_arguments_node.children:
                                if call_arg.type != "," and call_arg.type != "(" and call_arg.type != ")":
                                    assert call_arg.text is not None
                                    call_arg_value = call_arg.text.decode("utf-8")
                                    try:
                                        arg_variables = ASTParser(call_arg_value, language).extract_variables()
                                    except Exception:
                                        arg_variables = []
                                    if arg_variables:
                                        target_args.update(arg_variables)
                                    else:
                                        if language == Language.JAVA:
                                            call_arg_value_ast = ASTParser(call_arg_value, Language.JAVA)
                                            call_arg_value_objs = call_arg_value_ast._all_java_object_name()
                                            target_args.update(call_arg_value_objs)
                                        else:
                                            call_arg_value_ast = ASTParser(call_arg_value, Language.CPP)
                                            call_arg_value_objs = call_arg_value_ast._all_cpp_object_name()
                                            target_args.update(call_arg_value_objs)
                if target_args == set():
                    target_args.add(assignment_var)

            if (isinstance(callee_name, list) and callee_method.name in callee_name) or (isinstance(callee_name, str) and callee_method.name == callee_name):
                callee_method.sensitive_api_method = True
            if "#".join(call_edge[1].split("#")[0:2]) in target_repo.matching_methods:
                if f'{"#".join(call_edge[1].split("#")[0:2])}({callee_method.parameter_signature})' in visited:
                    continue
                visited.add(f'{"#".join(call_edge[1].split("#")[0:2])}({callee_method.parameter_signature})')
                slice_callee_results = (
                    slicing_single_method(
                        target_repo,
                        "#".join(call_edge[1].split("#")[0:2]),
                        target_project,
                        cache_dir,
                        semantic_model,
                        callee_lines={int(call_edge[3])},
                    )
                )
                if (
                    slice_callee_results is None
                ):
                    continue
                
                visited = slice_per_callee(
                    target_repo,
                    target_project,
                    cache_dir,
                    callgraph,
                    slice_callee_results,
                    "#".join(call_edge[1].split("#")[0:2]),
                    visited,
                    level + 1,
                    is_pre,
                    language,
                    callee_name,
                    semantic_model,
                    data_depend_dicts=data_depend_dicts,
                    call_graph_enhanced=call_graph_enhanced
                )
            else:
                parser = ASTParser(lines[int(call_edge[2])], language)
                if language == Language.JAVA:
                    nodes = parser.query_all("(method_invocation)@name")
                else:
                    nodes = parser.query_all("(call_expression)@name")
                if len(nodes) == 0:
                    continue
                init_single_method_dir(callee_method, cache_dir)

                slice_callee_results = None
                has_parametes = False

                for node in nodes:
                    if language == Language.JAVA:
                        child = node.child_by_field_name("name")
                    else:
                        child = node.child_by_field_name("function")
                    args = []
                    if child is None or child.text is None:
                        continue
                    if child.text.decode() == call_edge[1].split("#")[1]:
                        arguments_node = node.child_by_field_name("arguments")
                        if arguments_node is None:
                            continue
                        for arg in arguments_node.children:
                            if arg.type != "," and arg.type != "(" and arg.type != ")":
                                assert arg.text is not None
                                arg_value = arg.text.decode("utf-8")
                                args.append(arg_value)
                        if call_edge[2] in criteria_identifier:
                            slice_callee_results = (
                                callee_method.slice_by_header_line_vul_detect(
                                    cache_dir, semantic_model, args, criteria_identifier[call_edge[2]], False, True, target_args = target_args, original_code_path=actual_original_code_path
                                )
                            )
                        else:
                            slice_callee_results = (
                                callee_method.slice_by_header_line_vul_detect(
                                    cache_dir, semantic_model, args, set(), False, True, target_args = target_args, original_code_path=actual_original_code_path
                                )
                            ) 
                        has_parametes = True
                if not has_parametes:
                    slice_callee_results = (
                        callee_method.slice_by_header_line_vul_detect(
                            cache_dir, semantic_model, args, set(), False, True, target_args = target_args, original_code_path=actual_original_code_path
                        )
                    ) 

                if f'{"#".join(call_edge[1].split("#")[0:2])}({callee_method.parameter_signature})' not in visited and slice_callee_results is not None:
                    visited.add(f'{"#".join(call_edge[1].split("#")[0:2])}({callee_method.parameter_signature})')

                    visited = slice_per_callee(
                        target_repo,
                        target_project,
                        cache_dir,
                        callgraph,
                        slice_callee_results,
                        call_edge[1],
                        visited,
                        level + 1,
                        is_pre,
                        language,
                        callee_name,
                        semantic_model,
                        data_depend_dicts=data_depend_dicts,
                        call_graph_enhanced=call_graph_enhanced
                    )

        elif (
            "#".join(call_edge[1].split("#")[0:2]) == method_signature or call_edge[1] == method_signature
        ):
            caller_method = target_project.get_method(call_edge[0], call_edge[2])
            if caller_method is None:
                continue
            if "#".join(call_edge[0].split("#")[0:2]) in target_repo.matching_methods:
                if f'{"#".join(call_edge[0].split("#")[0:2])}({caller_method.parameter_signature})' in visited:
                    continue
                visited.add(f'{"#".join(call_edge[0].split("#")[0:2])}({caller_method.parameter_signature})')
                slice_caller_results = slicing_single_method(
                    target_repo,
                    "#".join(call_edge[0].split("#")[0:2]),
                    target_project,
                    cache_dir,
                    semantic_model,
                    callee_lines={int(call_edge[2])},
                )
                if slice_caller_results is None:
                    continue
                caller_results = slice_caller_results
                
                visited = slice_per_callee(
                    target_repo,
                    target_project,
                    cache_dir,
                    callgraph,
                    caller_results,
                    call_edge[0],
                    visited,
                    level + 1,
                    is_pre,
                    language,
                    callee_name,
                    semantic_model,
                    data_depend_dicts=data_depend_dicts,
                    call_graph_enhanced=call_graph_enhanced
                )
            else:
                init_single_method_dir(caller_method, cache_dir)
                caller_method.counterpart = caller_method
                slice_results = caller_method.slice_by_diff_lines_detect(
                    set([int(call_edge[2])]),
                    cache_dir,
                    semantic_model,
                    need_criteria_identifier=True,
                    write_dot=True,
                    role="target",
                    original_code_path=actual_original_code_path
                )
                if f'{"#".join(call_edge[0].split("#")[0:2])}({caller_method.parameter_signature})' not in visited and slice_results is not None:
                    visited = slice_per_callee(
                        target_repo,
                        target_project,
                        cache_dir,
                        callgraph,
                        slice_results,
                        call_edge[0],
                        visited,
                        level + 1,
                        is_pre,
                        language,
                        callee_name,
                        semantic_model,
                        data_depend_dicts=data_depend_dicts,
                        call_graph_enhanced=call_graph_enhanced
                    )

            visited.add(f'{"#".join(call_edge[0].split("#")[0:2])}({caller_method.parameter_signature})')
    return visited


def slicing_multi_method(
    target_repo: Target, target_project: Project, cache_dir, callgraph, language, callee_name, semantic_model
):
    visited = set()
    base_cache_dir = cache_dir.split("/method/")[0] if "/method/" in cache_dir else cache_dir
    data_depend_dicts = None
    call_graph_enhanced = None
    if semantic_model:
        data_depend_dict_path = os.path.join(base_cache_dir, "cpg", "data_depend_dict.json")
        if os.path.exists(data_depend_dict_path):
            with open(data_depend_dict_path, "r") as file:
                data_depend_dicts = json.load(file)
        
        call_graph_enhanced_path = os.path.join(base_cache_dir, "cpg", "callgraph.json")
        if os.path.exists(call_graph_enhanced_path):
            with open(call_graph_enhanced_path, 'r') as file:
                call_graph_enhanced = json.load(file)

    for method_signature in target_repo.matching_methods:

        callee_lines = target_repo.line_matching[method_signature]
        method = target_project.get_method(method_signature, callee_lines)
        assert method is not None
        if f"{method_signature}({method.parameter_signature})" in visited:
            continue
        visited.add(f"{method_signature}({method.parameter_signature})")
        slice_results = slicing_single_method(
            target_repo, method_signature, target_project, cache_dir, semantic_model
        )

        if slice_results is None:
            continue  
        if callgraph is None:
            continue
        visited = slice_per_callee(
            target_repo,
            target_project,
            cache_dir,
            callgraph,
            slice_results,
            method_signature,
            visited,
            1,
            True,
            language,
            callee_name,
            semantic_model,
            data_depend_dicts=data_depend_dicts,
            call_graph_enhanced=call_graph_enhanced
        )
    if data_depend_dicts:
        del data_depend_dicts
    if call_graph_enhanced:
        del call_graph_enhanced
    import gc
    gc.collect()

def get_line_map(target_project: Project, callee_name, matching_method, json_file_path):

    callee_method_line_numbers = set()
    line_numbers = set()
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    edges = data.get('edges', [])
    
    for edge in edges:
        if len(edge) >= 3:
            callee_method = None
            caller, callee, line_number, _ = edge
            caller_method_name = f"{caller.split('#')[0]}#{caller.split('#')[1]}"
            if callee.count("#") == 1:
                if caller_method_name == matching_method[0] and callee.split('#')[-1] == callee_name:
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
                elif caller_method_name == matching_method[0] and "$" in callee.split("#")[-1] and callee_name in callee.split('#')[-1].split('$'):
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
                elif caller_method_name == matching_method[0] and "<init>" in callee.split("#")[-1] and callee_name in callee.split('#')[-1].split("."):
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
            elif callee.count("#") == 2:
                if caller_method_name == matching_method[0] and callee.split('#')[-2] == callee_name:
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
                elif caller_method_name == matching_method[0] and "$" in callee.split("#")[-2] and callee_name in callee.split('#')[-2].split('$'):
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
                elif caller_method_name == matching_method[0] and "<init>" in callee.split("#")[-2] and callee_name in callee.split('#')[-2].split("."):
                    callee_method = target_project.get_method(callee, line_number)
                    line_numbers.add(int(line_number))
            if callee_method is not None:
                callee_method_line_numbers.add(int(callee_method.start_line))
                for line in callee_method.body_lines:
                    callee_method_line_numbers.add(int(line))
    return line_numbers, callee_method_line_numbers
    


def target_slicing(worker_id, tar, repo_path, cache_dir, matching_method, line_map, language, change_linemap, semantic_model_switch=False):
    import gc
    multithread_max_workers = 10
    error_code = {}
    error_code[tar] = {}
    target_proj = None
    target_repo = None
    callgraph = None
    cpg = None
    call_node_info = None
    
    try:
        try:
            time_start = time.time()
            format_lambda = False
            target_repo = Target(
                repo_path,
                matching_method,
                language,
                line_map,
                format_lambda=format_lambda
            )
            analysis_files = target_repo.analysis_files
            create_code_tree(analysis_files, cache_dir)
            print(f"✅ Target directory tree built")
            target_proj = target_repo.project
            time_end = time.time()
        except Exception as e:
            error_code[tar]["summary"] = "TARGET PROJ ERROR"
            error_code[tar]["detail"] = str(e)
            print(f"repo: {repo_path},  slicing error: {str(e)}")
            return error_code, worker_id
        
        try:
            print(f"🔄 Parsing Project Joern Graph")
            time_start = time.time()
            joern.export_with_preprocess_and_merge(f"{cache_dir}/code", cache_dir, language, overwrite=False, cdg_need=True, max_workers=multithread_max_workers)
            target_proj.load_joern_graph(None, f"{cache_dir}/pdg")
            print(f"✅ Project Joern Graph loaded")
            time_end = time.time()
            gc.collect()
        except Exception as e:
            error_code[tar]["summary"] = "PDG ERROR"
            error_code[tar]["detail"] = str(e)
            print(f"repo: {repo_path},  pdg error  : {str(e)}")
            return error_code, worker_id

        try:
            print(f"🔄 Fetching callgraph")
            time_start = time.time()
            preprocess_time_start = time.time()
            token_stats_file = os.path.join(cache_dir, "token_stats.json")
            init_token_stats(token_stats_file)
            reset_token_stats()

            call_node_info = preprocess(cache_dir, max_workers=multithread_max_workers)
            preprocess_time_end = time.time()
            get_call_time_start = time.time()
            callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=multithread_max_workers, enhanced=True)
            get_call_time_end = time.time()
            token_stats = get_token_stats()
            print(f"✅ Callgraph fetched")
            print(f"Token usage: calls={token_stats.get('call_count', 0)}, "
                        f"Prompt={token_stats.get('total_prompt_tokens', 0)}, "
                        f"Completion={token_stats.get('total_completion_tokens', 0)}, "
                        f"Total={token_stats.get('total_tokens', 0)}")
            time_end = time.time()
            gc.collect()
        except Exception as e:
            error_code[tar]["summary"] = "CALL ERROR"
            error_code[tar]["detail"] = str(e)
            print(f"repo: {repo_path},  call error: {str(e)}")
            return error_code, worker_id

        try:
            time_start = time.time()
            if change_linemap:
                print(f"🔄 Fetching line_map")
                path = cache_dir + "/call.json"
                callee_names = list(line_map.keys())
                for callee_name in callee_names:
                    callee_line_number, callee_method_line_numbers = get_line_map(target_proj, callee_name, matching_method, path)
                    if matching_method[0] not in target_repo.line_matching or not isinstance(target_repo.line_matching[matching_method[0]], set):
                        target_repo.line_matching[matching_method[0]] = set(target_repo.line_matching[matching_method[0]]) if matching_method[0] in target_repo.line_matching else set()
                    if callee_name not in target_repo.line_matching:
                        target_repo.line_matching[callee_name] = set()
                    if isinstance(callee_line_number, str):
                        target_repo.line_matching[matching_method[0]].add(callee_line_number)
                    else:
                        target_repo.line_matching[matching_method[0]].update(callee_line_number)
                    if isinstance(callee_method_line_numbers, str):
                        target_repo.line_matching[callee_name].add(callee_method_line_numbers)
                    else:
                        for line in callee_method_line_numbers:
                            target_repo.line_matching[callee_name].add(line)
                print(f"✅ line_map fetched")
            time_end = time.time()
        except Exception as e:
            error_code[tar]["summary"] = "LINE MAP ERROR"
            error_code[tar]["detail"] = str(e)
            print(f"repo: {repo_path},  slicing error: {str(e)}")
            return error_code, worker_id

        try:
            time_start = time.time()
            assert target_repo is not None
            assert target_proj is not None
            if semantic_model_switch and language == Language.JAVA:
                semantic_model_main_py = os.path.join(os.path.dirname(__file__), "semantic_model", "main.py")
                semantic_model_cache_dir = os.path.join(cache_dir, "semantic_model")
                subprocess.run(
                    [sys.executable, semantic_model_main_py, "--cache_dir", semantic_model_cache_dir, "--code_path", f"{cache_dir}/code", "--joern_path", os.environ.get("JOERN_PATH", "")],
                    check=True,
                    env={**os.environ, "JOERN_PATH": os.environ.get("JOERN_PATH", "")},
                )
                subprocess.run("mv", f"{semantic_model_cache_dir}/semantic_model.json", f"{cache_dir}/cpg/semantic_model.json")
                subprocess.run("mv", f"{semantic_model_cache_dir}/data_depend_dict.json", f"{cache_dir}/cpg/data_depend_dict.json")
                subprocess.run("rm", "-rf", semantic_model_cache_dir)
            if target_repo is not None and target_proj is not None and callgraph is not None:
                callee_names = list(line_map.keys())
                slicing_multi_method(target_repo, target_proj, cache_dir, callgraph, language, callee_names, semantic_model_switch)
            time_end = time.time()
            print(f"✅ Slicing done")
        except Exception as e:
            error_code[tar]["summary"] = "slicing error"
            error_code[tar]["detail"] = str(e)
            print(f"repo: {repo_path},  slicing error: {str(e)}")
            return error_code, worker_id
        final_token_stats = get_token_stats()
        print(f"Final token usage: calls={final_token_stats.get('call_count', 0)}, "
                    f"Prompt={final_token_stats.get('total_prompt_tokens', 0)}, "
                    f"Completion={final_token_stats.get('total_completion_tokens', 0)}, "
                    f"Total={final_token_stats.get('total_tokens', 0)}")
        
        error_code[tar]["summary"] = "SUCCESS"
        error_code[tar]["detail"] = "SUCCESS"
        error_code[tar]["token_stats"] = final_token_stats
        return error_code, worker_id
    
    finally:
        print(f"🔄 Releasing target_slicing resources: {repo_path}")
        if target_proj is not None:
            del target_proj
        if target_repo is not None:
            del target_repo
        if callgraph is not None:
            del callgraph
        if cpg is not None:
            del cpg
        if call_node_info is not None:
            del call_node_info
        
        target_proj = None
        target_repo = None
        callgraph = None
        cpg = None
        call_node_info = None
        
        gc.collect()
        print(f"✅ Resources released")
