from __future__ import annotations

import re
import ast
import json
import os
import subprocess
import sys
from collections import deque
from functools import cached_property, lru_cache
from dataclasses import dataclass

import networkx as nx
from tree_sitter import Node

import Constructing_Enhanced_UDG.ast_parser as ast_parser
from . import code_transformation
import Constructing_Enhanced_UDG.format_code as format_code
import Constructing_Enhanced_UDG.joern as joern
from Constructing_Enhanced_UDG.ast_parser import ASTParser
from Constructing_Enhanced_UDG.codefile import CodeFile
from Constructing_Enhanced_UDG.common import Language
from .diffparser import AddHunk, DelHunk, Hunk, ModHunk, get_patch_hunks
from Constructing_Enhanced_UDG.joern import PDGNode
from Constructing_Enhanced_UDG.json2dot import convert_to_dot
from Constructing_Enhanced_UDG.parallel_edges import add_global_variables_to_code, get_callgraph
from typing import List, Set, Tuple, Dict, Any, Optional


def group_consecutive_ints(nums: list[int]):
    if len(nums) == 0:
        return []
    nums.sort()
    result = [[nums[0]]]
    for num in nums[1:]:
        if num == result[-1][-1] + 1:
            result[-1].append(num)
        else:
            result.append([num])
    return result


class ProjectJoern:
    def __init__(self, cpg, pdg_dir):
        self.cpg = cpg
        self.pdg_paths: dict[tuple[int, str, str], str] = self.build_pdg_paths(pdg_dir)
        self.path = pdg_dir.replace("/pdg", "")

    def build_pdg_paths(self, pdg_dir: str):
        dot_names = os.listdir(pdg_dir)
        pdg_paths: dict[tuple[int, str, str], str] = {}
        for dot in dot_names:
            dot_path = os.path.join(pdg_dir, dot)
            try:
                pdg = joern.PDG(pdg_path=dot_path)
            except Exception as e:
                continue
            if pdg.name is None or pdg.line_number is None or pdg.filename is None:
                continue
            pdg_paths[(pdg.line_number, pdg.name, pdg.filename)] = dot_path
            del pdg
        return pdg_paths

    @lru_cache(maxsize=128)
    def _load_pdg(self, path: str) -> joern.PDG:
        return joern.PDG(pdg_path=path)

    def get_pdg(self, method: Method) -> Optional[joern.PDG]:
        key = (method.start_line, method.name, method.file.path)
        path = self.pdg_paths.get(key)
        
        if path is None:
            path = self.pdg_paths.get(
                (method.start_line + 1, method.name, method.file.path)
            )
            if path is None:
                 path = self.pdg_paths.get(
                    (method.start_line - 1, method.name, method.file.path)
                )
        
        if path:
            return self._load_pdg(path)
        return None


class Project:
    def __init__(self, project_name: str, files: list[CodeFile], language: Language):
        self.project_name: str = project_name
        self.language: Language = language
        self.files: list[File] = []

        self.files_path_set: set[str] = set()

        self.inherent_types: dict[str, str] = {}
        self.deinherent_types: dict[str, str] = {}

        for file in files:
            content_provider = lambda f=file: f.formated_code
            file_obj = File(file.file_path, content_provider, self, language)
            self.files.append(file_obj)
            self.files_path_set.add(file_obj.path)
            
        self.joern: Optional[ProjectJoern] = None
        
        self.calls: dict[str, dict] = {}
        self.method_name_dict: dict[str, list[dict]] = {}
        self.method_list: list[str] = []
        self.call_graph_dot: nx.MultiDiGraph = None
        self.methods: dict[str, dict] = {}

        self.edges_by_caller: dict[str, list] = {}
        self.edges_by_callee: dict[str, list] = {}
        self.java_unresolved_edges_by_name: dict[str, list] = {}
        self.java_reflection_edges: list = []
        self.cpp_external_edges_by_name: dict[str, list] = {}

        self.method_name_pairs_cache: list[tuple[str, str, str, str]] = []

    @cached_property
    def imports_signature_set(self) -> set[str]:
        signatures = set()
        if self.language == Language.JAVA or self.language == Language.CPP:
            for file in self.files:
                signatures.update([import_.signature for import_ in file.imports])
        return signatures

    @cached_property
    def classes_signature_set(self) -> set[str]:
        signatures = set()
        if self.language == Language.JAVA:
            for file in self.files:
                signatures.update([clazz.fullname for clazz in file.classes])
        return signatures

    @cached_property
    def methods_signature_set(self) -> set[str]:
        signatures = set()
        if self.language == Language.JAVA:
             for file in self.files:
                for clazz in file.classes:
                    for method in clazz.methods:
                        signatures.add(method.signature)
        elif self.language == Language.CPP:
            for file in self.files:
                for method in file.methods:
                    signatures.add(method.signature)
        return signatures

    @cached_property
    def fields_signature_set(self) -> set[str]:
        signatures = set()
        if self.language == Language.JAVA:
             for file in self.files:
                for clazz in file.classes:
                    for field in clazz.fields:
                        signatures.add(field.signature)
        return signatures

    def load_joern_graph(self, cpg, pdg_dir):
        self.joern = ProjectJoern(cpg, pdg_dir)

    def get_file(self, path: str) -> Optional[File]:
        for file in self.files:
            if file.path == path:
                return file
        return None

    def get_import(self, signature: str) -> Optional[Import]:
        for file in self.files:
            for import_ in file.imports:
                if import_.signature == signature:
                    return import_
        return None

    def get_class(self, fullname: str) -> Optional[Class]:
        for file in self.files:
            for clazz in file.classes:
                if clazz.fullname == fullname:
                    return clazz
        return None

    def get_method(self, fullname: str, callee_lines: set = None, need_all_methods: bool = False) -> Optional[Method]:
        line_number = None
        if fullname.count("#") == 2:
            line_number = fullname.split("#")[-1]
            fullname = "#".join(fullname.split("#")[:-1])

        if self.language == Language.JAVA:
            for file in self.files:
                for clazz in file.classes:
                    matching_methods = []
                    for method in clazz.methods:
                        method_signature = method.signature
                        if method_signature == fullname:
                            if line_number is not None:
                                if method.start_line <= int(line_number) <= method.end_line:
                                    matching_methods.append(method)
                                    break
                            elif callee_lines:
                                if any(method.start_line <= int(callee_line) <= method.end_line for callee_line in callee_lines):
                                    matching_methods.append(method)
                                    break
                            else:
                                matching_methods.append(method)
                    
                    if matching_methods:
                        if len(matching_methods) == 1:
                            return matching_methods[0]
                        elif need_all_methods:
                            return matching_methods
                        else:
                            return max(matching_methods, key=lambda m: len(m.parameter_signature.split(",")))
        elif self.language == Language.CPP:
            for file in self.files:
                for method in file.methods:
                    if method.signature == fullname:
                        return method
        return None        

    def get_field(self, fullname: str) -> Optional[Field]:
        for file in self.files:
            for clazz in file.classes:
                for field in clazz.fields:
                    if field.signature == fullname:
                        return field
        return None

    @cached_property
    def cpg(self):
        assert self.joern is not None
        return self.joern.cpg
    
    def find_inherited_methods_recursive(self, current_type, method_name, method_list, visited_types=None):

        if visited_types is None:
            visited_types = set()
        
        if current_type in visited_types:
            return []
        visited_types.add(current_type)
        
        matched_methods = []
        
        current_method_name = current_type + "." + method_name
        for _method in method_list:
            if current_method_name == _method.split(":")[0]:
                matched_methods.append(_method)
        
        if matched_methods:
            return matched_methods
        
        if current_type in self.inherent_types:
            parent_type = self.inherent_types[current_type]
            return self.find_inherited_methods_recursive(parent_type, method_name, method_list, visited_types)
        
        return []

    def find_deinherent_methods_recursive(self, current_type, method_name, method_list, visited_types=None):
        if visited_types is None:
            visited_types = set()

        if current_type in visited_types:
            return []
        visited_types.add(current_type)
        
        matched_methods = []
        
        current_method_name = current_type + "." + method_name
        for _method in method_list:
            if current_method_name == _method.split(":")[0]:
                matched_methods.append(_method)
        
        if current_type in self.deinherent_types:
            for child_type in self.deinherent_types[current_type]:
    
                child_methods = self.find_deinherent_methods_recursive(child_type, method_name, method_list, visited_types)
                matched_methods.extend(child_methods)
        
        return matched_methods

    def extract_reflection_info(self, code: str, line_code: str) -> Dict[str, Any]:
        import re
        
        info = {
            'class_names': set(),
            'method_names': set(),
            'patterns': []
        }
        
        class_forname_pattern = r'Class\.forName\(["\']([^"\']+)["\']'
        matches = re.findall(class_forname_pattern, code)
        info['class_names'].update(matches)
        
        class_literal_pattern = r'=\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\.class\b'
        matches = re.findall(class_literal_pattern, code)
        info['class_names'].update(matches)
        
        getmethod_pattern = r'\.getMethod\(["\']([^"\']+)["\']'
        matches = re.findall(getmethod_pattern, code)
        info['method_names'].update(matches)
        
        getdeclaredmethod_pattern = r'\.getDeclaredMethod\(["\']([^"\']+)["\']'
        matches = re.findall(getdeclaredmethod_pattern, code)
        info['method_names'].update(matches)
        
        getconstructor_pattern = r'\.getConstructor\(|\.getDeclaredConstructor\('
        if re.search(getconstructor_pattern, code):

            class_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_.]*)\.class'
            matches = re.findall(class_pattern, code)
            info['class_names'].update(matches)
        
        invoke_pattern = r'\.invoke\(|\.newInstance\('
        if re.search(invoke_pattern, code):

            var_pattern = r'(?:Method|Constructor)\s+(\w+)\s*='
            matches = re.findall(var_pattern, code)

        
        return info

    def filter_methods_by_reflection_info(self, method_list: List[str], reflection_info: Dict[str, Any]) -> List[str]:
        candidates = []
        class_names = reflection_info.get('class_names', set())
        method_names = reflection_info.get('method_names', set())
        
        if class_names and method_names:
            for class_name in class_names:
                for method_name in method_names:
        
                    full_name = f"{class_name}.{method_name}"
                    for method in method_list:
                        if method.split(":")[0].endswith(full_name):
                            candidates.append(method)
        
                    constructor_full_name = f"{class_name}.<init>"
                    for method in method_list:
                        method_decl = method.split(":")[0]
            
                        if method_decl.endswith(constructor_full_name):
                            candidates.append(method)
        
        elif class_names:
            for class_name in class_names:
                for method in method_list:
                    if class_name in method.split(":")[0]:
                        candidates.append(method)
        
        elif method_names:
            for method_name in method_names:
                for method in method_list:
                    if method.split(":")[0].split(".")[-1] == method_name:
                        candidates.append(method)
        
        if not candidates:

            import re
            potential_classes = set(re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', reflection_info.get('code', '')))
            for potential_class in potential_classes:
                for method in method_list:
                    method_class = ".".join(method.split(":")[0].split(".")[:-1])
                    if potential_class in method_class:
                        candidates.append(method)
        
        return list(set(candidates)) if candidates else []
    
    def _safe_get_line(self, lines, idx):
        i = max(0, min(len(lines)-1, idx-1))
        return lines[i] if lines else ""

    def process_one_edge(self, edge, methods, calls, method_list: list[str], code_dir: str, enhance=True):
        src, dst, data = edge
        results = []

        src_method = None
        dst_method = None
        dst_type = None

        call_line = data.get("label")

        if src in methods:
            src_method = methods[src]["full_name"]
        elif src in calls:
            src_method = calls[src].get("method_full_name")

        if dst in methods:
            dst_method = methods[dst]["full_name"]
        elif dst in calls:
            dst_method = calls[dst].get("method_full_name")
        src_method_orig = src_method
        dst_method_orig = dst_method
        
        src_id = None
        for key, call in calls.items():
            if call.get("method_full_name") == src_method and call.get("callee_method_full_name") == dst_method and call.get("line_number") == call_line:
                src_id = key
                break

        if dst_method:
            dst_type = ".".join(dst_method.split(":")[0].split(".")[:-1])
            dst_name = dst_method.split(":")[0].split(".")[-1]

        def _emit_direct_edge():
            if src_method and dst_method and src_method != dst_method:
                line_number = ""
                if src_id in calls:
                    line_number = calls[src_id].get("line_number", "")
                elif dst in calls:
                    line_number = calls[dst].get("line_number", "")
                results.append((src_method, dst_method, line_number))

        if dst_type and dst_type in self.inherent_types and "<unresolvedSignature>" in dst_method and enhance:
        
            matched_methods = self.find_inherited_methods_recursive(dst_type, dst_name, method_list)
            
            if len(matched_methods) == 1 and "<unresolvedSignature>" in dst_method:
                results.append((src_method, matched_methods[0], calls.get(src_id, {}).get("line_number", "")))
                dst_method = matched_methods[0]
            
            elif matched_methods:
                call_info = calls.get(src_id, {})
                file_name = call_info.get("file_name")
                if file_name and os.path.exists(os.path.join(code_dir, file_name)):
                    with open(os.path.join(code_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                        code_lines = f.readlines()
                    code = " ".join(code_lines[int(call_info["start_line"])-1:int(call_info["end_line"])])
                    line_code = self._safe_get_line(code_lines, int(call_info["line_number"]))
                    code = add_global_variables_to_code(code, code_lines, Language.JAVA)
                    methods_for_llm = matched_methods + [dst_method]
                    methods_str = "\n".join(methods_for_llm) if isinstance(methods_for_llm, list) else methods_for_llm
                    callee = get_callgraph(src_method, dst_method, code, methods_str, reflect=False, line_code=str(line_code), language=self.language)
                    if callee:
                        try:
                            if callee in method_list:
                                results.append((src_method, callee, call_info.get("line_number", "")))
                        except Exception:
                            pass
                else:
                    _emit_direct_edge()
            else:
                _emit_direct_edge()

        elif dst_type and dst_type in self.deinherent_types and "<unresolvedSignature>" in dst_method and enhance:
        
            matched_methods = self.find_deinherent_methods_recursive(dst_type, dst_name, method_list)
            
            if len(matched_methods) == 1 and "<unresolvedSignature>" in dst_method:
                results.append((src_method, matched_methods[0], calls.get(src_id, {}).get("line_number", "")))
                dst_method = matched_methods[0]
            
            elif matched_methods:
                call_info = calls.get(src_id, {})
                file_name = call_info.get("file_name")
                if file_name and os.path.exists(os.path.join(code_dir, file_name)):
                    with open(os.path.join(code_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                        code_lines = f.readlines()
                    code = " ".join(code_lines[int(call_info["start_line"])-1:int(call_info["end_line"])])
                    line_code = self._safe_get_line(code_lines, int(call_info["line_number"]))
                    code = add_global_variables_to_code(code, code_lines, Language.JAVA)
                    methods_for_llm = matched_methods + [dst_method]
                    methods_str = "\n".join(methods_for_llm) if isinstance(methods_for_llm, list) else methods_for_llm
                    callee = get_callgraph(src_method, dst_method, code, methods_str, reflect=False, line_code=str(line_code), language=self.language)
                    if callee:
                        try:
                            if callee in method_list:
                                results.append((src_method, callee, call_info.get("line_number", "")))
                        except Exception:
                
                            pass
                else:
                    _emit_direct_edge()

            else:
                _emit_direct_edge()

        elif dst_method and (dst_method.startswith("java.lang.Class.getMethod") or dst_method.startswith("java.lang.reflect.Method.invoke") or dst_method.startswith("java.lang.reflect.Constructor.newInstance")) and enhance:
            call_info = calls.get(src_id, {})
            file_name = call_info.get("file_name")
            if file_name and os.path.exists(os.path.join(code_dir, file_name)):
                with open(os.path.join(code_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                    code_lines = f.readlines()
                code = " ".join(code_lines[int(call_info["start_line"])-1:int(call_info["end_line"])])
                line_code = self._safe_get_line(code_lines, int(call_info["line_number"]))
                
    
                reflection_info = self.extract_reflection_info(code, line_code)
                reflection_info['code'] = code
                
                candidate_methods = self.filter_methods_by_reflection_info(list(method_list), reflection_info)

                methods_for_llm = candidate_methods if candidate_methods else list(method_list)
                
                methods_str = "\n".join(methods_for_llm) if isinstance(methods_for_llm, list) else methods_for_llm
                callee = get_callgraph(src_method, dst_method, code, methods_str, reflect=True, line_code=str(line_code), language=self.language)
            else:
                callee = None

            if callee:
                try:
                    if callee in method_list:
                        results.append((src_method, callee, call_info.get("line_number", "")))
                except Exception:
                    pass
        else:
            _emit_direct_edge()

        try:
            if not hasattr(self, "method_name_pairs_cache"):
                self.method_name_pairs_cache = []
            for res in results:
                try:
                    src_after, dst_after, _ = res
                except Exception:
                    continue
                self.method_name_pairs_cache.append((
                    src_method_orig or "",
                    dst_method_orig or "",
                    src_after or "",
                    dst_after or "",
                ))
        except Exception:
            pass

        return results

    def process_one_edge_C_CPP(self, edge, candidate_method_list_str, code_dir):
        src, dst, data = edge
        results = []

        src_method = None
        dst_method = None
        dst_type = None

        call_line = data.get("label")

        if src in self.methods:
            src_method = self.methods[src]["full_name"]

        if dst in self.methods:
            dst_method = self.methods[dst]["full_name"]
        
        for key, call in self.calls.items():
            if call.get("method_full_name") == src_method and call.get("callee_method_full_name") == dst_method and call.get("line_number") == call_line:
                call_id = key
                break
        
        if call_id in self.calls:
            line_number = self.calls[call_id].get("line_number", "")
            file_name = self.calls[call_id].get("file_name", "")
            if file_name and os.path.exists(os.path.join(code_dir, file_name)):
                with open(os.path.join(code_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                    code_lines = f.readlines()
                code = " ".join(code_lines[int(line_number)-1:int(line_number)])
                line_code = self._safe_get_line(code_lines, int(line_number))
                callee = get_callgraph(src_method, dst_method, code, candidate_method_list_str, reflect=False, line_code=str(line_code), language=self.language)
                if callee:
                    results.append((src_method, callee, line_number))
        else:
            results.append((src_method, dst_method, call_line))

        return results
        


    def _load_call_graph_cache(self) -> None:
        if self.call_graph_dot is None:
            return

        self.edges_by_caller = {}
        self.edges_by_callee = {}
        self.java_unresolved_edges_by_name = {}
        self.java_reflection_edges = []
        self.cpp_external_edges_by_name = {}

        for u, v, data in self.call_graph_dot.edges(data=True):
            if u not in self.call_graph_dot.nodes or v not in self.call_graph_dot.nodes:
                continue
            u_id = self.call_graph_dot.nodes[u].get("label")
            v_id = self.call_graph_dot.nodes[v].get("label")
            
            if u_id is None or v_id is None:
                continue
                
            if u_id not in self.edges_by_caller:
                self.edges_by_caller[u_id] = []
            self.edges_by_caller[u_id].append((u, v, data))
            
            if v_id not in self.edges_by_callee:
                self.edges_by_callee[v_id] = []
            self.edges_by_callee[v_id].append((u, v, data))

            v_method = self.methods.get(v_id)
            if v_method:
                v_name = v_method.get("name", "")
                v_full_name = v_method.get("full_name", "")
                v_signature = v_method.get("signature", "")
                
                tmp_name = v_name
                if v_name == "<init>":
                    match = re.search(r'(?:^|[$.])([A-Za-z_]\w*)(?=\.<init>)', v_full_name)
                    if match:
                        tmp_name = match.group(1)
                    else:
                        tmp_name = v_method.get("file_name", "").split(".java")[0].split("/")[-1]
                
                if self.language == Language.JAVA:
                    if "<unresolvedSignature>" in v_signature:
                        if tmp_name not in self.java_unresolved_edges_by_name:
                            self.java_unresolved_edges_by_name[tmp_name] = []
                        self.java_unresolved_edges_by_name[tmp_name].append((u, v, data, tmp_name))
                    elif v_full_name.startswith("java.lang.Class.getMethod") or \
                         v_full_name.startswith("java.lang.reflect.Method.invoke") or \
                         v_full_name.startswith("java.lang.reflect.Constructor.newInstance"):
                        self.java_reflection_edges.append((u, v, data))
                elif self.language == Language.CPP or self.language == Language.C:
                    if v_method.get("is_external"):
                        if tmp_name not in self.cpp_external_edges_by_name:
                            self.cpp_external_edges_by_name[tmp_name] = []
                        self.cpp_external_edges_by_name[tmp_name].append((u, v, data, tmp_name))

    def get_callee(self, fullname: str, cache_dir: str, enhanced=False):
        if "/method/" in cache_dir:
            cache_dir = cache_dir.split("/method/")[0]
        callees = []
        project_methods = self.get_method(fullname, need_all_methods=True)
        if project_methods is None:
            return callees
        assert project_methods is not None
        method_ids = set()
        if isinstance(project_methods, list):
            for method in project_methods:
                method_ids.update(method.line_number_pdg_map[0])
        else:
            method_ids = project_methods.line_number_pdg_map[0]

        if not self.edges_by_caller:
            self._load_call_graph_cache()

        for method_id in method_ids:
            if method_id in self.edges_by_caller:
                for u, v, data in self.edges_by_caller[method_id]:
                    line = str(data.get("label"))
                    
                    u_id = self.call_graph_dot.nodes[u]["label"]
                    v_id = self.call_graph_dot.nodes[v]["label"]
                    v_name = self.methods[v_id]["name"]
                    v_full_name = self.methods[v_id]["full_name"]

                    if u_id in method_ids:
                        u_call_line_number = line

                        continue_flag = False
                        if enhanced:
                            if self.language == Language.JAVA:
                                if ("<unresolvedSignature>" in v_full_name or v_full_name.startswith("java.lang.Class.getMethod") or v_full_name.startswith("java.lang.reflect.Method.invoke") or v_full_name.startswith("java.lang.reflect.Constructor.newInstance")):
                                    results = self.process_one_edge((u_id, v_id, data), self.methods, self.calls, self.method_list, f"{cache_dir}/code")
                                    if results:
                                        for result in results:
                                            _, callee_method_full_name, _ = result
                                            if callee_method_full_name and callee_method_full_name in self.call_graph_dot.nodes:
                                                tmp_id = self.call_graph_dot.nodes[callee_method_full_name]["label"]
                                                tmp_name = self.methods[tmp_id]["name"]
                                                tmp_file_name = self.methods[tmp_id]["file_name"]
                                                tmp_line_number = str(self.methods[tmp_id]["start_line"])
                                                callees.append(
                                                    {
                                                        "callee_linenumber": u_call_line_number,
                                                        "callee_method_name": f"{tmp_file_name}#{tmp_name}#{tmp_line_number}",
                                                        "method_line_number": tmp_line_number,
                                                    }
                                                )
                                                continue_flag = True
                            elif self.language == Language.CPP or self.language == Language.C:
                                if self.methods[v_id]["is_external"]:
                                    sig_full_dict = {}
                                    candidate_method_list = []
                                    for method in self.method_name_dict[v_name]:
                                        if method.get("signature") and method["signature"] != "":
                                            candidate_method_list.append(method["signature"])
                                            if method.get("full_name") and method["full_name"] != "":
                                                sig_full_dict[method["signature"]] = method["full_name"]
                                    result = self.process_one_edge_C_CPP((u_id, v_id, data), "\n".join(candidate_method_list), f"{cache_dir}/code")
                                    if result:
                                        for result in result:
                                            _, callee_method_signature, _ = result
                                            if callee_method_signature and callee_method_signature in sig_full_dict:
                                                callee_method_full_name = sig_full_dict[callee_method_signature]
                                                if callee_method_full_name and callee_method_full_name in self.call_graph_dot.nodes:
                                                    tmp_id = self.call_graph_dot.nodes[callee_method_full_name]["label"]
                                                    tmp_name = self.methods[tmp_id]["name"]
                                                    tmp_line_number = str(self.methods[tmp_id]["start_line"])
                                                    tmp_file_name = self.methods[tmp_id]["file_name"]
                                                    callees.append(
                                                        {
                                                            "callee_linenumber": u_call_line_number,
                                                            "callee_method_name": f"{tmp_file_name}#{tmp_name}#{tmp_line_number}",
                                                            "method_line_number": tmp_line_number,
                                                        }
                                                    )
                                                    continue_flag = True
                        if continue_flag == True:
                            continue
                        v_name = self.methods[v_id]["name"]
                        v_file_name = self.methods[v_id]["file_name"]
                        v_line_number = str(self.methods[v_id]["start_line"])
                        v_full_name = self.methods[v_id]["full_name"]

                        if v_name == "<init>":
                            match = re.search(r'(?:^|[$.])([A-Za-z_]\w*)(?=\.<init>)', v_full_name)
                            if match:
                                v_name = match.group(1)
                            else:
                                v_name = v_file_name.split(".java")[0].split("/")[-1]
                    
                        if v_line_number == "":
                            continue
                        if u_call_line_number == "":
                            continue

                        callees.append(
                            {
                                "callee_linenumber": u_call_line_number,
                                "callee_method_name": f"{v_file_name}#{v_name}#{v_line_number}",
                                "method_line_number": v_line_number,
                            }
                        )
        return callees

    def get_caller(self, fullname: str, cache_dir: str, enhanced=False):
        if "/method/" in cache_dir:
            cache_dir = cache_dir.split("/method/")[0]
        callers = []
        project_methods = self.get_method(fullname, need_all_methods=True)
        if project_methods is None:
            return []
        assert project_methods is not None
        method_ids = set()
        if isinstance(project_methods, list):
            for method in project_methods:
                method_ids.update(method.line_number_pdg_map[0])
        else:
            method_ids = project_methods.line_number_pdg_map[0]
        
        ref_method_name = fullname.split("#")[1]

        if not self.edges_by_callee:
            self._load_call_graph_cache()

        for method_id in method_ids:
            if method_id in self.edges_by_callee:
                for u, v, data in self.edges_by_callee[method_id]:
                    line = data.get("label")
                    u_id = self.call_graph_dot.nodes[u]["label"]
                    v_id = self.call_graph_dot.nodes[v]["label"]

                    v_name = self.methods[v_id]["name"]
                    v_full_name = self.methods[v_id]["full_name"]
                    v_file_name = self.methods[v_id]["file_name"]
                    v_line_number = str(self.methods[v_id]["start_line"])

                    u_file_name = self.methods[u_id]["file_name"]
                    u_name = self.methods[u_id]["name"]
                    u_line_number = str(self.methods[u_id]["start_line"])
                    
                    if u_line_number == "":
                        continue
                    if v_line_number == "":
                        continue
                    u_call_line_number = line
                    if u_call_line_number == "":
                        continue
                    
                    if v_name == "<init>":
                        match = re.search(r'(?:^|[$.])([A-Za-z_]\w*)(?=\.<init>)', v_full_name)
                        if match:
                            v_name = match.group(1)
                        else:
                            v_name = v_file_name.split(".java")[0].split("/")[-1]
                    
                    callers.append(f"{u_call_line_number}__split__{u_file_name}#{u_name}__split__{v_line_number}")

        if enhanced:
            if self.language == Language.JAVA:
    
                if ref_method_name in self.java_unresolved_edges_by_name:
                    for u, v, data, _ in self.java_unresolved_edges_by_name[ref_method_name]:
                        u_id = self.call_graph_dot.nodes[u]["label"]
                        v_id = self.call_graph_dot.nodes[v]["label"]
                        u_file_name = self.methods[u_id]["file_name"]
                        u_name = self.methods[u_id]["name"]
                        
                        results = self.process_one_edge((u_id, v_id, data), self.methods, self.calls, self.method_list, f"{cache_dir}/code")
                        if results:
                            for result in results:
                                _, callee_method_full_name, _ = result
                                if callee_method_full_name and callee_method_full_name in self.call_graph_dot.nodes:
                                    resolved_v_id = self.call_graph_dot.nodes[callee_method_full_name]["label"]
                                    if resolved_v_id in method_ids:
                                        v_line_number = str(self.methods[resolved_v_id]["start_line"])
                                        u_call_line_number = data.get("label")
                                        callers.append(f"{u_call_line_number}__split__{u_file_name}#{u_name}__split__{v_line_number}")

    
                for u, v, data in self.java_reflection_edges:
                    u_id = self.call_graph_dot.nodes[u]["label"]
                    v_id = self.call_graph_dot.nodes[v]["label"]
                    u_file_name = self.methods[u_id]["file_name"]
                    u_line_number = str(self.methods[u_id]["start_line"])
                    
                    if u_file_name and os.path.exists(os.path.join(cache_dir, "code", u_file_name)):
            
                        with open(os.path.join(cache_dir, "code", u_file_name), "r", encoding="utf-8", errors="ignore") as f:
                            code_lines = f.readlines()
                        line_code = self._safe_get_line(code_lines, int(u_line_number))
                        
                        if ref_method_name in line_code:
                            results = self.process_one_edge((u_id, v_id, data), self.methods, self.calls, self.method_list, f"{cache_dir}/code")
                            if results:
                                for result in results:
                                    _, callee_method_full_name, _ = result
                                    if callee_method_full_name and callee_method_full_name in self.call_graph_dot.nodes:
                                        resolved_v_id = self.call_graph_dot.nodes[callee_method_full_name]["label"]
                                        if resolved_v_id in method_ids:
                                            v_line_number = str(self.methods[resolved_v_id]["start_line"])
                                            u_name = self.methods[u_id]["name"]
                                            u_call_line_number = data.get("label")
                                            callers.append(f"{u_call_line_number}__split__{u_file_name}#{u_name}__split__{v_line_number}")

            elif self.language == Language.CPP or self.language == Language.C:
                if ref_method_name in self.cpp_external_edges_by_name:
                    for u, v, data, _ in self.cpp_external_edges_by_name[ref_method_name]:
                        u_id = self.call_graph_dot.nodes[u]["label"]
                        v_id = self.call_graph_dot.nodes[v]["label"]
                        u_file_name = self.methods[u_id]["file_name"]
                        u_name = self.methods[u_id]["name"]
                        
                        sig_full_dict = {}
                        candidate_method_list = []
                        for method in self.method_name_dict.get(ref_method_name, []):
                            if method.get("signature") and method["signature"] != "":
                                candidate_method_list.append(method["signature"])
                                if method.get("full_name") and method["full_name"] != "":
                                    sig_full_dict[method["signature"]] = method["full_name"]
                                    
                        result = self.process_one_edge_C_CPP((u_id, v_id, data), "\n".join(candidate_method_list), f"{cache_dir}/code")
                        if result:
                            for res in result:
                                _, callee_method_signature, _ = res
                                if callee_method_signature and callee_method_signature in sig_full_dict:
                                    callee_method_full_name = sig_full_dict[callee_method_signature]
                                    if callee_method_full_name and callee_method_full_name in self.call_graph_dot.nodes:
                                        resolved_v_id = self.call_graph_dot.nodes[callee_method_full_name]["label"]
                                        if resolved_v_id in method_ids:
                                            v_line_number = str(self.methods[resolved_v_id]["start_line"])
                                            u_call_line_number = data.get("label")
                                            callers.append(f"{u_call_line_number}__split__{u_file_name}#{u_name}__split__{v_line_number}")

        return list(set(callers))

@dataclass
class Line:
    line_number: int
    code: str
    file: File

class File:
    def __init__(
        self, path: str, content: str | Any, project: Optional[Project], language: Language
    ):
        self.language = language
        self.project = project
        self.path = path
        self.name = os.path.basename(path)
        self._content = content
        self._parser = None
        self._code = None

        if project is None:
            if isinstance(content, str):
                self.project = Project("None", [CodeFile(path, content, language, isformat=False)], language)
            else:
                 pass 
        else:
            self.project = project

    @property
    def code(self) -> str:
        if self._code is None:
            if isinstance(self._content, str):
                self._code = self._content
            elif callable(self._content):
                self._code = self._content()
            else:
                self._code = str(self._content)
        return self._code

    @code.setter
    def code(self, value: str):
        self._code = value
        self._parser = None

    @property
    def parser(self) -> ASTParser:
        if self._parser is None:
            self._parser = ASTParser(self.code, self.language)
        return self._parser

    @cached_property
    def package(self) -> str:
        assert self.language == Language.JAVA
        package_node = self.parser.query_oneshot(ast_parser.TS_JAVA_PACKAGE)
        return package_node.text.decode() if package_node is not None else "<NONE>"

    @cached_property
    def imports(self) -> list[Import]:
        if self.language == Language.JAVA:
            return [
                Import(import_node, self, self.language)
                for import_node in self.parser.query_all(ast_parser.TS_JAVA_IMPORT)
            ]
        elif self.language == Language.CPP:
            return [
                Import(import_node, self, self.language)
                for import_node in self.parser.query_all(ast_parser.TS_C_INCLUDE)
            ]
        else:
            return []

    @cached_property
    def classes(self) -> list[Class]:
        if self.language == Language.JAVA:
            return [
                Class(class_node, self, self.language)
                for class_node in self.parser.query_all(ast_parser.TS_JAVA_CLASS)
            ]
        else:
            return []

    @cached_property
    def fields(self) -> list[Field]:
        return [field for clazz in self.classes for field in clazz.fields]

    @cached_property
    def methods(self) -> list[Method]:
        if self.language == Language.JAVA:
            return [method for clazz in self.classes for method in clazz.methods]
        elif self.language == Language.CPP:
            methods: list[Method] = []
            query = ast_parser.TS_C_METHOD
            methods_dict = {}
            methods_intervals = []
            for method_node in self.parser.query_all(query):
                if method_node.text is None:
                    continue
                if method_node.text.decode().lstrip().startswith("namespace"):
                    continue
                methods_dict[
                    f"{method_node.start_point[0]}##{method_node.end_point[0]}"
                ] = method_node
                methods_intervals.append(
                    (method_node.start_point[0], method_node.end_point[0])
                )
            methods_intervals = self.merge_intervals(methods_intervals)
            for st, ed in methods_intervals:
                if st == ed:
                    continue
                if f"{st}##{ed}" in methods_dict.keys():
                    methods.append(
                        Method(methods_dict[f"{st}##{ed}"], None, self, self.language)
                    )
            return methods
        else:
            return []

    def merge_intervals(self, intervals):
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])

        merged = [intervals[0]]

        for current in intervals[1:]:
            last = merged[-1]

            if current[0] <= last[1]:
                merged[-1] = [last[0], max(last[1], current[1])]
            else:
                merged.append(current)

        return merged


class Import:
    def __init__(self, node: Node, file: File, language: Language):
        self.file = file
        self.node = node
        self.code = node.text.decode()
        self.signature = file.path + "#" + self.code


class Class:
    def __init__(self, node: Node, file: File, language: Language):
        self.language = language
        self.file = file
        self.code = node.text.decode()
        self.node = node
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        self.name = name_node.text.decode()
        self.fullname = f"{file.package}.{self.name}"

    @cached_property
    def fields(self):
        file = self.file
        parser = file.parser
        class_node = self.node
        class_name = self.name
        fields: list[Field] = []
        query = f"""
        (class_declaration
            name: (identifier)@class.name
            (#eq? @class.name "{class_name}")
            body: (class_body
                (field_declaration)@field
            )
        )    
        """
        for field_node in parser.query_by_capture_name(query, "field", node=class_node):
            fields.append(Field(field_node, self, file))
        return fields

    @cached_property
    def methods(self):
        file = self.file
        parser = file.parser
        class_node = self.node
        class_name = self.name
        methods: list[Method] = []
        query = f"""
        [
            (class_declaration
                name: (identifier)@class.name
                (#eq? @class.name "{class_name}")
                body: (class_body
                    [(method_declaration)
                    (constructor_declaration)]@method
                )
            )
            (enum_declaration
                name: (identifier)@class.name
                (#eq? @class.name "{class_name}")
                body: (enum_body
                    (enum_body_declarations
                        [(method_declaration)
                        (constructor_declaration)]@method
                    )?
                )
            )
        ]
        """
        for method_node in parser.query_by_capture_name(
            query, "method", node=class_node
        ):
            methods.append(Method(method_node, self, file, self.language))
        return methods


class Field:
    def __init__(self, node: Node, clazz: Class, file: File):
        self.name = (
            node.child_by_field_name("declarator")
            .child_by_field_name("name")# type: ignore
            .text.decode()
        )
        self.clazz = clazz
        self.file = file
        self.code = node.text.decode()
        self.signature = f"{self.clazz.fullname}.{self.name}"


class Method:
    def __init__(self, node: Node, clazz: Optional[Class], file: File, language: Language):
        self.language = language
        if language == Language.JAVA:
            name_node = node.child_by_field_name("name")
            assert name_node is not None and name_node.text is not None
            self.name = name_node.text.decode()
        else:
            name_node = node.child_by_field_name("declarator")
            while name_node is not None and name_node.type not in {
                "identifier",
                "operator_name",
                "type_identifier",
            }:
                all_temp_name_node = name_node
                if (
                    name_node.child_by_field_name("declarator") is None
                    and name_node.type == "reference_declarator"
                ):
                    for temp_node in name_node.children:
                        if temp_node.type == "function_declarator":
                            name_node = temp_node
                            break
                if name_node.child_by_field_name("declarator") is not None:
                    name_node = name_node.child_by_field_name("declarator")
                while name_node is not None and (
                    name_node.type == "qualified_identifier"
                    or name_node.type == "template_function"
                ):
                    temp_name_node = name_node
                    for temp_node in name_node.children:
                        if temp_node.type in {
                            "identifier",
                            "destructor_name",
                            "qualified_identifier",
                            "operator_name",
                            "type_identifier",
                            "pointer_type_declarator",
                        }:
                            name_node = temp_node
                            break
                    if name_node == temp_name_node:
                        break
                if name_node is not None and name_node.type == "destructor_name":
                    for temp_node in name_node.children:
                        if temp_node.type == "identifier":
                            name_node = temp_node
                            break
                if (
                    name_node is not None
                    and name_node.type == "field_identifier"
                    and name_node.child_by_field_name("declarator") is None
                ):
                    break
                if name_node == all_temp_name_node:
                    break

            assert name_node is not None and name_node.text is not None
            self.name = name_node.text.decode()
        self.clazz = clazz
        self.file = file
        self.node = node
        assert node.text is not None
        self.code = node.text.decode()
        self.start_line = node.start_point[0] + 1
        self.end_line = node.end_point[0] + 1

        self.lines: dict[int, str] = {
            i + self.start_line: line for i, line in enumerate(self.code.split("\n"))
        }

        self._pdg: Optional[joern.PDG] = None

        self.joern_path: Optional[str] = None

        self.counterpart: Optional[Method] = None
        self.method_dir: Optional[str] = None
        self.html_base_path: str = ""
        self.method_file: str = ""
        self.diff_add_lines: list[tuple[int, int]] = []
        self.diff_del_lines: list[tuple[int, int]] = []
        self.sensitive_api_method: bool | False = False
        self.base_cache_dir: Optional[str] = None
        self.abs_lines: dict[int, str] = {
            i + self.start_line: line
            for i, line in enumerate(self.code.split("\n"))
        }

    @classmethod
    def init_from_file_code(cls, path: str, language: Language):
        with open(path, "r") as f:
            code = f.read()
        file = File(path, code, None, language)
        parser = ASTParser(code, language)
        method_node = parser.query_oneshot(ast_parser.TS_C_METHOD)
        assert method_node is not None
        return cls(method_node, None, file, language)

    @property
    def pdg(self) -> Optional[joern.PDG]:
        if self.file.project is None:
            return None
        assert self.file.project.joern is not None
        if self._pdg is None:
            self._pdg = self.file.project.joern.get_pdg(self)
        return self._pdg

    @cached_property
    def abstract_code(self):
        return code_transformation.abstract(self.code, self.language)

    @property
    def line_pdg_pairs(self) -> Optional[dict[int, joern.PDGNode]]:
        line_pdg_pairs = {}
        if self.pdg is None:
            return None
        for node_id in self.pdg.g.nodes():
            node = self.pdg.get_node(node_id)
            if node.line_number is None:
                continue
            line_pdg_pairs[node.line_number] = node
        return line_pdg_pairs

    @property
    def rel_line_pdg_pairs(self) -> Optional[dict[int, joern.PDGNode]]:
        rel_line_pdg_pairs = {}
        if self.pdg is None:
            return None
        for node_id in self.pdg.g.nodes():
            node = self.pdg.get_node(node_id)
            if node.line_number is None:
                continue
            rel_line_pdg_pairs[node.line_number - self.start_line + 1] = node
        return rel_line_pdg_pairs

    @cached_property
    def line_number_pdg_map(self):
        pdg = self.pdg
        if pdg is None:
            return [[], {}]
        method_nodes = []
        line_map_method_nodes = pdg.line_map_method_nodes_id
        for line in line_map_method_nodes:
            if isinstance(line_map_method_nodes[line], int):
                method_nodes.append(line_map_method_nodes[line])
                line_map_method_nodes[line] = [line_map_method_nodes[line]]
            else:
                method_nodes.extend(line_map_method_nodes[line])
        return [method_nodes, line_map_method_nodes]

    @property
    def callee(self):
        callees = set()
        parser = ASTParser(self.code, self.language)
        if self.language == Language.JAVA:
            call = parser.query_all(ast_parser.JAVA_CALL)
        else:   
            call = parser.query_all(ast_parser.CPP_CALL)
        if len(call) == 0:
            return None

        for node in call:
            if node.text is None:
                continue
            callees.add(node.text.decode())

        return callees

    @property
    def body_node(self) -> Optional[Node]:
        return self.node.child_by_field_name("body")

    @property
    def body_start_line(self) -> int:
        if self.body_node is None:
            return self.start_line
        else:
            return self.body_node.start_point[0] + 1

    @property
    def body_end_line(self) -> int:
        if self.body_node is None:
            return self.end_line
        else:
            return self.body_node.end_point[0] + 1

    @property
    def diff_dir(self) -> str:
        assert self.method_dir is not None
        return f"{self.method_dir}/diff"

    @property
    def dot_dir(self) -> str:
        assert self.method_dir is not None
        return f"{self.method_dir}/dot"

    @property
    def rel_line_set(self) -> set[int]:
        return set(range(self.rel_start_line, self.rel_end_line + 1))

    @property
    def parameters(self) -> list[Node]:
        parameters_node = self.node.child_by_field_name("parameters")
        if parameters_node is None:
            return []
        parameters = ASTParser.children_by_type_name(
            parameters_node, "formal_parameter"
        )
        return parameters

    @property
    def parameter_signature(self) -> str:
        parameter_signature_list = []
        for param in self.parameters:
            type_node = param.child_by_field_name("type")
            assert type_node is not None
            if type_node.type == "generic_type":
                type_identifier_node = ASTParser.child_by_type_name(
                    type_node, "type_identifier"
                )
                if type_identifier_node is None:
                    type_name = ""
                else:
                    assert type_identifier_node.text is not None
                    type_name = type_identifier_node.text.decode()
            else:
                assert type_node.text is not None
                type_name = type_node.text.decode()
            parameter_signature_list.append(type_name)
        return ",".join(parameter_signature_list)
    
    @property
    def parameter_signature_list(self) -> list:
        parameter_signature_list = []
        for param in self.parameters:
            type_node = param.child_by_field_name("type")
            assert type_node is not None
            if type_node.type == "generic_type":
                type_identifier_node = ASTParser.child_by_type_name(
                    type_node, "type_identifier"
                )
                if type_identifier_node is None:
                    type_name = ""
                else:
                    assert type_identifier_node.text is not None
                    type_name = type_identifier_node.text.decode()
            else:
                assert type_node.text is not None
                type_name = type_node.text.decode()
            parameter_signature_list.append(type_name)
        return parameter_signature_list

    @property
    def signature(self) -> str:
        if self.language == Language.JAVA:
            assert self.clazz is not None
            return f"{self.file.path}#{self.name}"
        else:
            return f"{self.file.path}#{self.name}"

    @property
    def signature_r(self) -> str:
        if self.language == Language.JAVA:
            assert self.clazz is not None
            fullname_r = ".".join(self.clazz.fullname.split(".")[::-1])
            return f"{self.name}({self.parameter_signature}).{fullname_r}"
        else:
            return f"{self.name}#{self.start_line}#{self.end_line}#{self.file.name}"

    @property
    def diff_lines(self) -> set[int]:
        lines = set()
        for hunk in self.patch_hunks:
            if type(hunk) == DelHunk:
                lines.update(range(hunk.a_startline, hunk.a_endline + 1))
            elif type(hunk) == ModHunk:
                lines.update(range(hunk.a_startline, hunk.a_endline + 1))
        return lines

    @property
    def rel_diff_lines(self) -> set[int]:
        return set([line - self.start_line + 1 for line in self.diff_lines])

    @property
    def diff_identifiers(self):
        assert self.counterpart is not None
        diff_identifiers = {}
        for hunk in self.patch_hunks:
            if type(hunk) == DelHunk:
                lines = set(range(hunk.a_startline, hunk.a_endline + 1))
                criteria_identifier_a = self.identifier_by_lines(lines)
                diff_identifiers.update(criteria_identifier_a)
            elif type(hunk) == ModHunk:
                a_lines = set(range(hunk.a_startline, hunk.a_endline + 1))
                b_lines = set(range(hunk.b_startline, hunk.b_endline + 1))
                criteria_identifier_a = self.identifier_by_lines(a_lines)
                criteria_identifier_b = self.counterpart.identifier_by_lines(b_lines)
                lines = a_lines.union(b_lines)
                for line in lines:
                    if (
                        line in criteria_identifier_a.keys()
                        and line in criteria_identifier_b.keys()
                    ):
                        diff_identifiers[line] = (
                            criteria_identifier_a[line] - criteria_identifier_b[line]
                        )
                    elif line in criteria_identifier_a.keys():
                        diff_identifiers[line] = criteria_identifier_a[line]
        return diff_identifiers

    @cached_property
    def patch_hunks(self) -> list[Hunk]:
        assert self.counterpart is not None
        hunks = get_patch_hunks(self.file.code, self.counterpart.file.code)
        for hunk in hunks.copy():
            if type(hunk) == ModHunk or type(hunk) == DelHunk:
                if not (
                    self.start_line <= hunk.a_startline
                    and hunk.a_endline <= self.end_line
                ):
                    hunks.remove(hunk)
            elif type(hunk) == AddHunk:
                if (
                    hunk.insert_line < self.start_line
                    or hunk.insert_line > self.end_line
                ):
                    hunks.remove(hunk)

        def sort_key(hunk: Hunk):
            if type(hunk) == AddHunk:
                return hunk.insert_line
            elif type(hunk) == ModHunk or type(hunk) == DelHunk:
                return hunk.a_startline
            else:
                return 0

        hunks.sort(key=sort_key)
        return hunks

    @property
    def header_lines(self) -> set[int]:
        return set(range(self.start_line, self.body_start_line + 1))

    @property
    def body_lines(self) -> set[int]:
        body_start_line = self.body_start_line
        body_end_line = self.body_end_line
        if self.lines[self.body_start_line].strip().endswith("{"):
            body_start_line += 1
        if self.lines[self.body_end_line].strip().endswith("}"):
            body_end_line -= 1
        return set(range(body_start_line, body_end_line + 1))

    @property
    def body_code(self) -> str:
        return "\n".join([self.lines[line] for line in sorted(self.body_lines)])

    @property
    def modified_parameters(self):
        diff_lines = self.diff_lines
        modified_parameters = {}
        if self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                if line in diff_lines:
                    left_param = node.child_by_field_name("left")

                    if left_param is None or left_param.text is None or left_param.text.decode() == "":
                        continue
                    try:
                        modified_parameters[line].add(left_param.text.decode())
                    except:
                        modified_parameters[line] = set()
                        modified_parameters[line].add(left_param.text.decode())

        return modified_parameters

    def abstract_code_by_lines(self, lines: set[int]):
        result = "\n".join([self.abs_rel_lines[line] for line in sorted(lines)])
        return result + "\n"

    def code_by_lines(self, lines: set[int], *, placeholder: Optional[str] = None) -> str:
        max_line = max(lines) if lines else 0
        line_no_width = len(str(max_line))

        if placeholder is None:
            result = ""
            for line in sorted(lines):
                if self.rel_lines[line].strip() == "":
                    continue
                l = line - 1
                while l > 0 and (self.rel_lines[l].strip().startswith("//") or self.rel_lines[l].strip().startswith("*")):
                    if l in lines:
                        l -= 1
                        continue
                    result += f"{l + self.start_line - 1:>{line_no_width}}: {self.rel_lines[l]}\n"
                    l -= 1
                result += f"{line + self.start_line - 1:>{line_no_width}}: {self.rel_lines[line]}\n"
            return result + "\n"
        else:
            code_with_placeholder = ""
            last_line = 0
            placeholder_counter = 0
            for line in sorted(lines):
                if line - last_line > 1:
                    is_comment = True
                    for i in range(last_line + 1, line):
                        if self.rel_lines[i].strip() == "":
                            continue
                        if not self.rel_lines[i].strip().startswith("//"):
                            is_comment = False
                            break
                    if is_comment:
                        pass
                    elif line - last_line == 2 and (
                        self.rel_lines[line - 1].strip() == ""
                        or self.rel_lines[line - 1].strip().startswith("//")
                    ):
                        pass
                    else:
                        code_with_placeholder += f"{placeholder}\n"
                        placeholder_counter += 1
                code_with_placeholder += f"{line + self.start_line - 1:>{line_no_width}}: {self.rel_lines[line]}\n"
                last_line = line
            return code_with_placeholder

    def reduced_hunks(self, slines: set[int]) -> list[str]:
        placeholder_lines = self.rel_line_set - slines
        return self.code_hunks(placeholder_lines)

    def code_hunks(self, lines: set[int]) -> list[str]:
        hunks: list[str] = []
        lineg = group_consecutive_ints(list(lines))
        for g in lineg:
            hunk = self.code_by_lines(set(g))
            hunks.append(hunk)
        return hunks

    def recover_placeholder(
        self, code: str, slice_lines: set[int], placeholder: str
    ) -> Optional[str]:
        placeholder_hunks = self.reduced_hunks(slice_lines)
        if code.count(placeholder) != len(placeholder_hunks):
            return None
        result = ""
        for line in code.split("\n"):
            if line.strip().lower() == placeholder.strip().lower():
                result += placeholder_hunks.pop(0)
            else:
                result += line + "\n"
        return result

    def code_by_exclude_lines(self, lines: set[int], *, placeholder: Optional[str]) -> str:
        exclude_lines = self.rel_line_set - lines
        return self.code_by_lines(exclude_lines, placeholder=placeholder)

    def identifier_by_lines(self, lines: set[int]):
        identifier_list = {}
        if self.language == Language.CPP:
            identifier_nodes = self.file.parser.get_all_identifier_node()
            for node in identifier_nodes:
                if node.parent is not None and node.parent.type == "unary_expression":
                    line = node.parent.start_point[0] + 1
                    if line in lines:
                        assert node.parent.text is not None
                        try:
                            identifier_list[line].add(node.parent.text.decode())
                        except:
                            identifier_list[line] = {node.parent.text.decode()}
                else:
                    line = node.start_point[0] + 1
                    if line in lines:
                        assert node.text is not None
                        try:
                            identifier_list[line].add(node.text.decode())
                        except:
                            identifier_list[line] = {node.text.decode()}
        return identifier_list

    def conditions_by_lines(self, lines: set[int]):
        conditions_list = set()
        if self.language == Language.CPP:
            conditional_nodes = self.file.parser.get_all_conditional_node()
            for node in conditional_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    conditions_list.add(line)
        elif self.language == Language.JAVA:
            conditional_nodes = self.file.parser.get_all_conditional_node()
            for node in conditional_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    conditions_list.add(line)
        return conditions_list

    def ret_by_lines(self, lines: set[int]):
        ret_list = set()
        if self.language == Language.CPP:
            ret_nodes = self.file.parser.get_all_return_node()
            for node in ret_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        elif self.language == Language.JAVA:
            ret_nodes = self.file.parser.get_all_return_node()
            for node in ret_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        return ret_list

    def assignment_by_lines(self, lines: set[int]):
        assign_list = set()
        if self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    assign_list.add(line)
        elif self.language == Language.JAVA:
            assign_nodes = self.file.parser.get_all_assign_node_java()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    assign_list.add(line)
        return assign_list

    def call_by_lines(self, lines: set[int]):
        ret_list = set()
        if self.language == Language.CPP:
            call_nodes = self.file.parser.get_all_call_node()
            for node in call_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        elif self.language == Language.JAVA:
            call_nodes = self.file.parser.get_all_call_node_java()
            for node in call_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        return ret_list

    def all_assignment_lines(self):
        assign_list = set()
        if self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                assign_list.add(line)
        elif self.language == Language.JAVA:
            assign_nodes = self.file.parser.get_all_assign_node_java()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                assign_list.add(line)
        return assign_list

    @cached_property
    def all_flow_control_lines(self):
        control_list = {}
        if self.language == Language.CPP:
            control_nodes = self.file.parser.get_all_flow_control_goto()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "goto"
            control_nodes = self.file.parser.get_all_flow_control_break()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "break"
            control_nodes = self.file.parser.get_all_flow_control()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "continue"
        elif self.language == Language.JAVA:
            control_nodes = self.file.parser.get_all_flow_control_break()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "break"
            control_nodes = self.file.parser.get_all_flow_control()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "continue"
        return control_list

    @property
    def normalized_body_code(self) -> str:
        return format_code.normalize(self.body_code)

    @property
    def formatted_code(self) -> str:
        return format.format(
            self.code, self.language, del_comment=False, del_linebreak=True
        )

    @property
    def rel_start_line(self) -> int:
        return 1

    @property
    def rel_end_line(self) -> int:
        return self.end_line - self.start_line + 1

    @property
    def rel_body_start_line(self) -> int:
        return self.body_start_line - self.start_line + 1

    @property
    def rel_body_end_line(self) -> int:
        return self.body_end_line - self.start_line + 1

    @property
    def rel_lines(self) -> dict[int, str]:
        return {line - self.start_line + 1: code for line, code in self.lines.items()}

    @property
    def abs_rel_lines(self) -> dict[int, str]:
        return {
            line - self.start_line + 1: code for line, code in self.abs_lines.items()
        }

    @property
    def length(self):
        return self.end_line - self.start_line + 1

    @property
    def file_suffix(self):
        if self.language == Language.CPP:
            suffix = ".c"
        elif self.language == Language.JAVA:
            suffix = ".java"
        else:
            suffix = ""
        return suffix

    def write_dot(self, dir: Optional[str] = None):
        if self.file.path == "libcpp/init.c":
            return
        if self.pdg is None:
            return
        assert self.pdg is not None
        if self.file.project is None:
            return
        assert self.file.project is not None
        assert self.file.project.project_name is not None
        dot_name = f"{self.file.project.project_name}.dot"
        if dir is not None:
            dot_path = os.path.join(dir, dot_name)
        else:
            dot_path = os.path.join(self.dot_dir, dot_name)
        nx.nx_agraph.write_dot(self.pdg.g, dot_path)

    def write_code(self, dir: Optional[str] = None):
        assert self.method_dir is not None
        if self.file.project is None:
            return
        assert self.file.project is not None
        assert self.file.project.project_name is not None
        file_name = f"{self.file.project.project_name}{self.file_suffix}"
        if dir is not None:
            code_path = os.path.join(dir, file_name)
        else:
            code_path = os.path.join(self.method_dir, file_name)
        with open(code_path, "w") as f:
            f.write(self.code)

    def diff2html(self, method: Method):
        assert self.method_dir is not None
        file1 = self.method_file
        file2 = method.method_file
        title = f"{self.signature} vs {method.signature}"
        output_path = os.path.join(self.method_dir, "diff.html")
        out = subprocess.run(
            [
                "git",
                "--no-pager",
                "diff",
                "--no-index",
                "-w",
                "-b",
                "--unified=10000",
                "--function-context",
                file1,
                file2,
            ],
            stdout=subprocess.PIPE,
        )
        subprocess.run(
            [
                "diff2html",
                "-f",
                "html",
                "-F",
                output_path,
                "--su",
                "-s",
                "side",
                "--lm",
                "lines",
                "-i",
                "stdin",
                "-t",
                title,
            ],
            input=out.stdout,
            stderr=subprocess.DEVNULL,
        )

    def code_by_lines_ppathf(
        self, lines: set[int], *, placeholder: bool = False
    ) -> str:
        if not placeholder:
            result = "\n".join([self.rel_lines[line] for line in sorted(lines)])
            return result + "\n"
        else:
            code_with_placeholder = ""
            last_line = 0
            placeholder_counter = 0
            for line in sorted(lines):
                if line - last_line > 1:
                    is_comment = True
                    for i in range(last_line + 1, line):
                        if self.rel_lines[i].strip() == "":
                            continue
                        if not self.rel_lines[i].strip().startswith("//"):
                            is_comment = False
                            break
                    if is_comment:
                        pass
                    elif line - last_line == 2 and (
                        self.rel_lines[line - 1].strip() == ""
                        or self.rel_lines[line - 1].strip().startswith("//")
                    ):
                        pass
                    else:
                        code_with_placeholder += (
                            f"/* Placeholder_{placeholder_counter} */\n"
                        )
                        placeholder_counter += 1
                code_with_placeholder += self.rel_lines[line] + "\n"
                last_line = line
            return code_with_placeholder

    @staticmethod
    def backward_slice(
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: set[str],
        all_nodes: dict[int, list[PDGNode]],
        level: int,
    ) -> tuple[set[int], set[PDGNode]]:
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()

        for slice_line in criteria_lines:
            for node in all_nodes[slice_line]:
                if node.type == "METHOD_RETURN":
                    continue
                for pred_node in node.pred_cfg_nodes:
                    if (
                        pred_node.line_number is None
                        or int(pred_node.line_number) == sys.maxsize
                    ):
                        continue
                    result_lines.add(int(pred_node.line_number))
                    result_nodes.add(pred_node)

        for sline in criteria_lines:
            for node in all_nodes[sline]:
                if node.type in ["METHOD_RETURN"]:
                    continue
                visited = set()
                queue = deque([(node, 0)])
                while queue:
                    node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                        if depth < level:
                            for pred_node, edge in node.pred_ddg:
                                if (
                                    pred_node.line_number is None
                                    or int(pred_node.line_number) == sys.maxsize
                                ):
                                    continue
                                processed_edge = edge.replace("this.", "")
                                if edge not in node.code and processed_edge not in node.code:
                                    continue
                                if len(criteria_identifier) > 0:
                                    if edge not in criteria_identifier:
                                        continue
                                queue.append((pred_node, depth + 1))

        return result_lines, result_nodes

    @staticmethod
    def forward_slice_with_weight(
        method: Method,
        cache_dir: str,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: set[str],
        semantic_model: bool,
        all_nodes: dict[int, list[PDGNode]],
        level: int,
        need_header_line=False,
        target_args: set = set(),
    ):
        result_nodes = set()
        result_lines = set()
        result_edges = set()
        result_weight = {}
        flag = need_header_line

        if semantic_model:
            data_depend_dicts_dir = os.path.join(method.base_cache_dir, "cpg", "data_depend_dict.json")
            with open(data_depend_dicts_dir, "r") as f:
                data_depend_dicts = json.load(f)

            data_depend_dict: dict[str, list[str]] = {}

        for sline in criteria_lines:
            if sline not in all_nodes:
                continue
            for node in all_nodes[sline]:
                if "[" not in str(node.type):
                    continue
                if node.type == "METHOD":
                    if semantic_model:
                        data_depend_dict = data_depend_dicts[node.node_id]
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                

                if semantic_model:
                    if data_depend_dict:
                        if method.start_line in criteria_lines:
                            target_lines = {line for line in criteria_lines if line != method.start_line}
                        else:
                            target_lines = set(criteria_lines)
                    else:
                        target_lines = set(criteria_lines)
                    
                    for target_line in target_lines:
                        if target_line not in method.abs_lines.keys():
                            continue
                        assignment_var = ""
                        ast_parser = ASTParser(method.abs_lines[int(target_line)], method.language)
                        if method.language == Language.JAVA:
                            local_decls = ast_parser.get_all_assign_node_java()
                            assignment_expressions = ast_parser.get_assignment_expression()
                        else:
                            local_decls = ast_parser.get_all_assign_node()
                            assignment_expressions = ast_parser.get_assignment_expression()

                        call_nodes = ast_parser.query_all("(method_invocation)@name")
                        
                        for call_node in call_nodes:
                            child = call_node.child_by_field_name("name")
                            args = []
                            call_arguments_node = call_node.child_by_field_name("arguments")
                            if call_arguments_node is None:
                                continue
                            for call_arg in call_arguments_node.children:
                                if call_arg.type != "," and call_arg.type != "(" and call_arg.type != ")":
                                    assert call_arg.text is not None
                                    call_arg_value = call_arg.text.decode("utf-8")
                                    try:
                                        arg_variables = ASTParser(call_arg_value, method.language).extract_variables()
                                    except Exception:
                                        arg_variables = []
                                    if arg_variables:
                                        target_args.update(arg_variables)
                                    else:
                                        call_arg_value_ast = ASTParser(call_arg_value, method.language)
                                        if method.language == Language.JAVA:
                                            call_arg_value_objs = call_arg_value_ast._all_java_object_name()
                                        else:
                                            call_arg_value_objs = call_arg_value_ast._all_cpp_object_name()
                                        target_args.update(call_arg_value_objs)
                        if assignment_var and target_args == set():
                            target_args.add(assignment_var)

                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    pre_node, node, depth = queue.popleft()
                    if node not in visited:
                        
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if pre_node != node and pre_node.line_number is not None:
                                result_edges.add(
                                    (pre_node.line_number, node.line_number)
                                )
                        if (
                            node.type != "METHOD"
                            and "RETURN" not in str(node.type)
                        ) or need_header_line:
                            for succ_node, edge in node.succ_ddg:
                                processed_edge = edge.replace("this.", "")
                                if edge not in node.code and processed_edge not in node.code:
                                    continue
                                if semantic_model:
                                    if target_args and edge not in target_args:
                                        continue
                                if len(criteria_identifier) > 0:
                                    if edge not in criteria_identifier:
                                        continue
                                if semantic_model:
                                    assignment_var = ""
                                    succ_code_parser = ASTParser(succ_node.code, method.language)
                                    if method.language == Language.JAVA:
                                        local_decls = succ_code_parser.get_all_assign_node_java()
                                    else:
                                        local_decls = succ_code_parser.get_all_assign_node()
                                    assignment_expressions = succ_code_parser.get_assignment_expression()
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
                                    if assignment_var:
                                        target_args.add(assignment_var)
                                queue.append((node, succ_node, depth + 1))

        need_header_line = flag
        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue

                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    pre_node, node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if pre_node != node and pre_node.line_number is not None:
                                result_edges.add(
                                    (pre_node.line_number, node.line_number)
                                )
                        if "RETURN" not in str(node.type):
                            for succ_node in node.succ_cdg:
                                queue.append((node, succ_node, depth + 1))

        return result_lines, result_nodes, result_weight, result_edges


    @staticmethod
    def forward_slice(criteria_lines: set[int], criteria_nodes: set[PDGNode], criteria_identifier: set[str], all_nodes: dict[int, list[PDGNode]], level: int) -> tuple[set[int], set[PDGNode]]:
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        if level == 0:
            level = 1000

        for slice_line in criteria_lines:
            if slice_line not in all_nodes:
                continue    
            for node in all_nodes[slice_line]:
                if node.type == "METHOD" or "METHOD_RETURN" in str(node.type):
                    continue
                if node.line_number is None:
                    continue
                for succ_node in node.succ_cfg_nodes:
                    if succ_node.line_number is None or int(succ_node.line_number) == sys.maxsize:
                        continue
                    if succ_node.line_number < node.line_number:
                        continue
                    result_lines.add(int(succ_node.line_number))
                    result_nodes.add(succ_node)

        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD" or "METHOD_RETURN" in str(node.type):
                    continue
                visited = set()
                queue = deque([(node, 0)])
                while queue:
                    node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        if node not in result_nodes:
                            result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                        if depth < level:
                            for succ_node, edge in node.succ_ddg:
                                processed_edge = edge.replace("this.", "")
                                if edge not in node.code and processed_edge not in node.code:
                                    continue
                                if succ_node.line_number is None or int(succ_node.line_number) == sys.maxsize or node.line_number is None:
                                    continue
                                if succ_node.line_number < node.line_number:
                                    continue
                                if len(criteria_identifier) > 0 and edge not in criteria_identifier:
                                        continue
                                queue.append((succ_node, depth + 1))

        return result_lines, result_nodes


    def slice(
        self,
        criteria_lines: set[int],
        criteria_identifier: set,
        backward_slice_level: int = 4,
        forward_slice_level: int = 4,
        is_rel: bool = False,
    ):
        assert self.pdg is not None
        if is_rel:
            criteria_lines = set(
                [line + self.start_line - 1 for line in criteria_lines]
            )

        all_lines = set(self.lines.keys())
        all_nodes: dict[int, list[PDGNode]] = {
            line: self.pdg.get_nodes_by_line_number(line) for line in all_lines
        }
        criteria_nodes: set[PDGNode] = set()
        for line in criteria_lines:
            for node in self.pdg.get_nodes_by_line_number(line):
                node.is_patch_node = True
                node.add_attr("color", "red")
                criteria_nodes.add(node)

        slice_result_lines = set(criteria_lines)
        slice_result_lines |= self.header_lines
        slice_result_lines.add(self.end_line)

        result_lines, backward_nodes = self.backward_slice(
            criteria_lines,
            criteria_nodes,
            criteria_identifier,
            all_nodes,
            backward_slice_level,
        )
        slice_result_lines.update(result_lines)
        result_lines, forward_nodes = self.forward_slice(
            criteria_lines,
            criteria_nodes,
            criteria_identifier,
            all_nodes,
            forward_slice_level,
        )
        slice_result_lines.update(result_lines)
        slice_nodes = criteria_nodes.union(backward_nodes).union(forward_nodes)
        slice_result_rel_lines = set(
            [
                line - self.start_line + 1
                for line in slice_result_lines
                if line >= self.start_line
            ]
        )

        sliced_code = self.code_by_lines(slice_result_rel_lines)
        return slice_result_lines, slice_result_rel_lines, slice_nodes, sliced_code

    def slice_by_diff_lines(
        self,
        backward_slice_level: int = 4,
        forward_slice_level: int = 4,
        need_criteria_identifier: bool = False,
        write_dot: bool = False,
    ):
        criteria_identifier = self.diff_identifiers if need_criteria_identifier else {}
        criteria_identifier_set = set()
        for line in criteria_identifier:
            criteria_identifier_set.update(criteria_identifier[line])
        slice_results = self.slice(
            self.diff_lines,
            criteria_identifier_set,
            backward_slice_level,
            forward_slice_level=forward_slice_level,
            is_rel=False,
        )
        if write_dot and slice_results is not None:
            assert self.pdg is not None and self.method_dir is not None
            slice_nodes = slice_results[2]
            g = nx.subgraph(self.pdg.g, [node.node_id for node in slice_nodes])
            os.makedirs(self.method_dir, exist_ok=True)
            if self.file.project is None:
                role = "None"
            else:
                assert self.file.project.project_name is not None
                role = self.file.project.project_name
            nx.nx_agraph.write_dot(
                g,
                os.path.join(
                    self.dot_dir,
                    f"{role}#{backward_slice_level}#{forward_slice_level}.dot",
                ),
            )
        return slice_results

    def backward_slice_vul_detect(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier,
        all_nodes: dict[int, list[PDGNode]],
        need_header_line=False,
    ):
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        result_edges = set()
        result_weight = {}
        if need_header_line:
            flag = True
        else:
            flag = False

        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue
                if "[" not in str(node.type):
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    node, succ_node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if node != succ_node and succ_node.line_number is not None:
                                result_edges.add(
                                    (node.line_number, succ_node.line_number)
                                )
                        if node.type == "METHOD":
                            continue
                        if "[" not in str(node.type):
                            continue
                        if (
                            "METHOD_PARAMETER_IN" in str(node.type)
                        ) and not need_header_line:
                            continue
                        for pred_node, edge in node.pred_ddg:
                            if (
                                pred_node.line_number is None
                                or int(pred_node.line_number) == sys.maxsize
                            ):
                                continue
                            processed_edge = edge.replace("this.", "")
                            if edge not in node.code and processed_edge not in node.code:
                                continue
                            if edge not in criteria_identifier and len(criteria_identifier) > 0:
                                continue
                            queue.append((pred_node, node, depth + 1))

        if flag:
            need_header_line = True

        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue

                if "[" not in str(node.type):
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    node, succ_node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if node != succ_node and succ_node.line_number is not None:
                                result_edges.add(
                                    (node.line_number, succ_node.line_number)
                                )
                        if node.type == "METHOD":
                            continue

                        if "[" not in str(node.type):
                            continue
                        if (
                            "METHOD_PARAMETER_IN" in str(node.type)
                        ) and not need_header_line:
                            continue
                        for pred_node in node.pred_cdg:
                            if (
                                pred_node.line_number is None
                                or int(pred_node.line_number) == sys.maxsize
                            ):
                                continue
                            queue.append((pred_node, node, depth + 1))

        return result_lines, result_nodes, result_weight, result_edges


    def backward_ddg_slice_vul_detect(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: dict[int, str],
        all_nodes: dict[int, list[PDGNode]],
        need_header_line: bool = False,
    ):
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        result_edges = set()
        result_weight = {}
        
        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue

                if "[" not in str(node.type):
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    node, succ_node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if node != succ_node and succ_node.line_number is not None:
                                result_edges.add(
                                    (node.line_number, succ_node.line_number)
                                )
                        if node.type == "METHOD":
                            continue
                        if "[" not in str(node.type):
                            continue
                        if (
                            "METHOD_PARAMETER_IN" in str(node.type)
                        ) and not need_header_line:
                            continue
                        for pred_node, edge in node.pred_ddg:

                            if (
                                pred_node.line_number is None
                                or int(pred_node.line_number) == sys.maxsize
                            ):
                                continue
                            processed_edge = edge.replace("this.", "")
                            if edge not in node.code and processed_edge not in node.code:
                                continue
                            if (
                                criteria_identifier != {}
                                and len(criteria_identifier[sline]) > 0
                            ):
                                if edge not in criteria_identifier[sline]:
                                    continue
                            queue.append((pred_node, node, depth + 1))

        return result_lines, result_nodes, result_weight, result_edges

    def backward_ddg_slice_vul_detect_with_taint(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: dict[int, str],
        all_nodes: dict[int, list[PDGNode]],
        need_header_line: bool = False,
    ):
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        
        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue

                if "[" not in str(node.type):
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    node, succ_node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                        if node.type == "METHOD":
                            continue
                        if "[" not in str(node.type):
                            continue
                        if (
                            "METHOD_PARAMETER_IN" in str(node.type)
                        ) and not need_header_line:
                            continue
                        for pred_node, edge in node.pred_ddg:

                            if (
                                pred_node.line_number is None
                                or int(pred_node.line_number) == sys.maxsize
                            ):
                                continue

                            queue.append((pred_node, node, depth + 1))

        return result_lines, result_nodes

    def backward_cdg_slice_vul_detect(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: dict[int, set[str]],
        all_nodes: dict[int, list[PDGNode]],
        need_header_line: bool = False,
    ):
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        result_edges = set()
        result_weight = {}
        
        for sline in criteria_lines:
            if sline not in all_nodes:
                continue    
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue
                if "[" not in str(node.type):
                    continue
                if (
                    "METHOD_RETURN" in str(node.type)
                ) and not need_header_line:
                    continue
                visited = set()
                queue = deque([(node, node, 0)])
                while queue:
                    node, succ_node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        result_nodes.add(node)
                        if node.line_number is not None:
                            result_lines.add(node.line_number)
                            try:
                                result_weight[node.line_number] += 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            except:
                                result_weight[node.line_number] = 1 / (depth + 1)
                                result_weight[node.line_number] = (
                                    result_weight[node.line_number]
                                    if result_weight[node.line_number] <= 1
                                    else 1
                                )
                            if node != succ_node and succ_node.line_number is not None:
                                result_edges.add(
                                    (node.line_number, succ_node.line_number)
                                )
                        if node.type == "METHOD":
                            continue
                        if "[" not in str(node.type):
                            continue
                        if (
                            "METHOD_PARAMETER_IN" in str(node.type)
                        ) and not need_header_line:
                            continue
                        for pred_node in node.pred_cdg:
                            if (
                                pred_node.line_number is None
                                or int(pred_node.line_number) == sys.maxsize
                            ):
                                continue
                            queue.append((pred_node, node, depth + 1))

        return result_lines, result_nodes, result_weight, result_edges



    def normal_forward_slice_on_DDG(
        self, sline: int, node: PDGNode, criteria_identifier: set[str]
    ) -> tuple[set[int], set[int], dict[int, float], set[tuple[int, int]]]:
        result_nodes = set()
        result_lines = set()
        result_edges = set()
        result_weight = {}
        if node.type == "METHOD" or "[" not in str(node.type) or "PARAM" in str(node.type):
            return result_nodes, result_lines, result_weight, result_edges
        visited = set()
        queue = deque([(node, node, 0)])
        while queue:
            pre_node, node, depth = queue.popleft()
            if node not in visited:
                visited.add(node)
                result_nodes.add(node)
                if node.line_number is not None:
                    result_lines.add(node.line_number)
                    try:
                        result_weight[node.line_number] += 1 / (depth + 1)
                        result_weight[node.line_number] = (
                            result_weight[node.line_number]
                            if result_weight[node.line_number] <= 1
                            else 1
                        )
                    except:
                        result_weight[node.line_number] = 1 / (depth + 1)
                        result_weight[node.line_number] = (
                            result_weight[node.line_number]
                            if result_weight[node.line_number] <= 1
                            else 1
                        )
                    if pre_node != node and pre_node.line_number is not None:
                        result_edges.add((pre_node.line_number, node.line_number))
                if "[" not in str(node.type):
                    continue
                if node.type != "METHOD" and "RETURN" not in str(node.type):
                    for succ_node, edge in node.succ_ddg:
                        processed_edge = edge.replace("this.", "")
                        if edge not in node.code and processed_edge not in node.code:
                            continue

                        if len(criteria_identifier) > 0 and edge not in criteria_identifier:
                            continue
                        queue.append((node, succ_node, depth + 1))
        return result_nodes, result_lines, result_weight, result_edges

    def normal_forward_slice_on_DDG_with_taint(
        self, sline: int, node: PDGNode, criteria_identifier: set[str]
    ) -> tuple[set[int], set[int]]:
        result_nodes = set()
        result_lines = set()
        if node.type == "METHOD" or "[" not in str(node.type) or "PARAM" in str(node.type):
            return result_nodes, result_lines
        visited = set()
        queue = deque([(node, node, 0)])
        while queue:
            pre_node, node, depth = queue.popleft()
            if node not in visited:
                visited.add(node)
                result_nodes.add(node)
                if node.line_number is not None:
                    result_lines.add(node.line_number)
                    
                if "[" not in str(node.type):
                    continue
                if node.type != "METHOD" and "RETURN" not in str(node.type):
                    for succ_node, edge in node.succ_ddg:
                        processed_edge = edge.replace("this.", "")
                        if edge not in node.code and processed_edge not in node.code:
                            continue
                        queue.append((node, succ_node, depth + 1))

        return result_nodes, result_lines

    def normal_forward_slice_on_CDG(
        self, node: PDGNode
    ) -> tuple[set[int], set[int], dict[int, float], set[tuple[int, int]]]:
        result_nodes = set()
        result_lines = set()
        result_edges = set()
        result_weight = {}
        if node.type == "METHOD" or "[" not in str(node.type) or "PARAM" in str(node.type):
            return result_nodes, result_lines, result_weight, result_edges
        visited = set()
        queue = deque([(node, node, 0)])
        while queue:
            pre_node, node, depth = queue.popleft()
            if node not in visited:
                visited.add(node)
                result_nodes.add(node)
                if node.line_number is not None:
                    result_lines.add(node.line_number)
                    try:
                        result_weight[node.line_number] += 1 / (depth + 1)
                        result_weight[node.line_number] = (
                            result_weight[node.line_number]
                            if result_weight[node.line_number] <= 1
                            else 1
                        )
                    except:
                        result_weight[node.line_number] = 1 / (depth + 1)
                        result_weight[node.line_number] = (
                            result_weight[node.line_number]
                            if result_weight[node.line_number] <= 1
                            else 1
                        )
                    if pre_node != node and pre_node.line_number is not None:
                        result_edges.add((pre_node.line_number, node.line_number))
                if "[" not in str(node.type):
                    continue
                if "RETURN" not in str(node.type):
                    for succ_node in node.succ_cdg:
                        queue.append((node, succ_node, depth + 1))

        return result_nodes, result_lines, result_weight, result_edges

    def customized_forward_slice_per_node(
        self, sline: int, node, criteria_identifier, all_nodes, all_assignments
    ) -> tuple[set[int], set[int], dict[int, float], set[tuple[int, int]]]:
        result_nodes = set()
        result_lines = set()
        result_edges = set()
        result_weights = {}
        temp_criteria_lines = set()
        temp_criteria_nodes = set()
        visited = set()
        queue = deque([(node, 0)])
        while queue:
            temp_node, depth = queue.popleft()
            if temp_node not in visited:
                visited.add(temp_node)
                if "[" not in str(temp_node.type):
                    continue
                if (
                    temp_node.type != "METHOD"
                    and "METHOD_PARAMETER_IN" not in str(temp_node.type)
                    and temp_node.line_number not in all_assignments
                ):
                    for pred_node, edge in temp_node.pred_ddg:
                        if (
                            pred_node.line_number is None
                            or int(pred_node.line_number) == sys.maxsize
                        ):
                            continue
                        if edge not in temp_node.code:
                            continue
                        if edge not in criteria_identifier and len(criteria_identifier) > 0:
                            continue
                        queue.append((pred_node, depth + 1))
                else:
                    if "[" not in str(temp_node.type):
                        continue
                    if (
                        temp_node.type == "METHOD"
                        or "METHOD_PARAMETER_IN" in str(temp_node.type)
                    ):
                        continue
                    temp_criteria_lines.add(temp_node.line_number)
                    temp_criteria_nodes.add(temp_node)
                    break

        if len(temp_criteria_nodes) == 0:
            (
                temp_result_nodes,
                temp_result_lines,
                temp_result_weights,
                temp_result_edges,
            ) = self.normal_forward_slice_on_CDG(node)
            result_lines = result_lines.union(temp_result_lines)
            result_nodes = result_nodes.union(temp_result_nodes)
            result_edges = result_edges.union(temp_result_edges)
            result_weights.update(temp_result_weights)
        else:
            result_lines = result_lines.union(temp_criteria_lines)
            result_nodes = result_nodes.union(temp_criteria_nodes)
            for temp_sline in temp_criteria_lines:
                if temp_sline not in all_nodes:
                    continue    
                for temp_node in all_nodes[temp_sline]:
                    if "[" not in str(temp_node.type):
                        continue
                    (
                        temp_result_nodes,
                        temp_result_lines,
                        temp_result_weights,
                        temp_result_edges,
                    ) = self.normal_forward_slice_on_DDG(
                        sline, temp_node, criteria_identifier
                    )
                    result_lines = result_lines.union(temp_result_lines)
                    result_nodes = result_nodes.union(temp_result_nodes)
                    result_edges = result_edges.union(temp_result_edges)
                    result_weights.update(temp_result_weights)

        return result_nodes, result_lines, result_weights, result_edges

    def customized_forward_slice_vul_detect(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        criteria_identifier: set[str],
        all_nodes: dict[int, list[PDGNode]],
        need_header_line=False,
        is_rel=False,
    ):
        assignments = self.assignment_by_lines(criteria_lines)
        ret = self.ret_by_lines(criteria_lines)
        conditions = self.conditions_by_lines(criteria_lines)
        calls = self.call_by_lines(criteria_lines)
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        result_edges = set()
        all_assignments = self.all_assignment_lines()
        result_weights = {}

        for sline in criteria_lines:
            if sline in ret:
                continue
            if sline not in all_nodes:
                continue
            for node in all_nodes[sline]:
                if node.type == "METHOD":
                    continue
                if "[" not in str(node.type):
                    continue
                if ("PARAM" in str(node.type)) and not need_header_line:
                    continue
                if sline in assignments:
                    (
                        temp_result_nodes,
                        temp_result_lines,
                        temp_result_weights,
                        temp_result_edges,
                    ) = self.normal_forward_slice_on_DDG(
                        sline, node, criteria_identifier
                    )
                    result_lines = result_lines.union(temp_result_lines)
                    result_nodes = result_nodes.union(temp_result_nodes)
                    result_edges = result_edges.union(temp_result_edges)
                    for line in temp_result_weights:
                        try:
                            result_weights[line] += temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )
                        except:
                            result_weights[line] = temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )
                elif sline in conditions:
                    (
                        temp_result_nodes,
                        temp_result_lines,
                        temp_result_weights,
                        temp_result_edges,
                    ) = self.customized_forward_slice_per_node(
                        sline, node, criteria_identifier, all_nodes, all_assignments
                    )
                    result_lines = result_lines.union(temp_result_lines)
                    result_nodes = result_nodes.union(temp_result_nodes)
                    result_edges = result_edges.union(temp_result_edges)
                    for line in temp_result_weights:
                        try:
                            result_weights[line] += temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )
                        except:
                            result_weights[line] = temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )

                elif sline in calls:
                    (
                        temp_result_nodes,
                        temp_result_lines,
                        temp_result_weights,
                        temp_result_edges,
                    ) = self.customized_forward_slice_per_node(
                        sline, node, criteria_identifier, all_nodes, all_assignments
                    )
                    result_lines = result_lines.union(temp_result_lines)
                    result_nodes = result_nodes.union(temp_result_nodes)
                    result_edges = result_edges.union(temp_result_edges)
                    for line in temp_result_weights:
                        try:
                            result_weights[line] += temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )
                        except:
                            result_weights[line] = temp_result_weights[line]
                            result_weights[line] = (
                                result_weights[line] if result_weights[line] <= 1 else 1
                            )

        return result_lines, result_nodes, result_edges, result_weights

    def cfg_slicing_for_control(
        self,
        criteria_lines: set[int],
        criteria_nodes: set[PDGNode],
        all_nodes,
        need_header_line=False,
        level=3,
    ):
        result_lines = criteria_lines.copy()
        result_nodes = criteria_nodes.copy()
        result_edges = set()
        result_weights = {}
        method_code = self.code
        ast_parser = ASTParser(method_code, Language.CPP)
        goto_query = """
        (goto_statement
        (statement_identifier)@label
        )
        """
        flag = need_header_line
        goto_results = ast_parser.query_all(goto_query)
        for line in criteria_lines:
            if line in self.all_flow_control_lines:
                if line not in all_nodes:
                    continue    
                for node in all_nodes[line]:
                    if node.type == "METHOD":
                        continue
                    if "[" not in str(node.type):
                        continue
                    if (
                        "METHOD_RETURN" in str(node.type)
                    ) and not need_header_line:
                        continue
                if self.all_flow_control_lines[line] == "goto":
                    for res in goto_results:
                        if res.start_point[0] + 1 == line - self.start_line + 1:
                            if res.text is None:
                                continue
                            identifier = res.text.decode()
                            lable_query = f"""
                            (labeled_statement
                                label: (statement_identifier)@label
                                (#eq? @label "{identifier}")
                            )
                            """
                            result_node = ast_parser.query_oneshot(lable_query)
                            if result_node is not None:
                                result_lines.add(
                                    result_node.start_point[0] + self.start_line
                                )
                                result_edges.add(
                                    (line, result_node.start_point[0] + self.start_line)
                                )
                                try:
                                    result_weights[
                                        result_node.start_point[0] + self.start_line
                                    ] += 1 / 2
                                    result_weights[
                                        result_node.start_point[0] + self.start_line
                                    ] = (
                                        result_weights[
                                            result_node.start_point[0] + self.start_line
                                        ]
                                        if result_weights[
                                            result_node.start_point[0] + self.start_line
                                        ]
                                        <= 1
                                        else 1
                                    )
                                except:
                                    result_weights[
                                        result_node.start_point[0] + self.start_line
                                    ] = 1 / 2
                                    result_weights[
                                        result_node.start_point[0] + self.start_line
                                    ] = (
                                        result_weights[
                                            result_node.start_point[0] + self.start_line
                                        ]
                                        if result_weights[
                                            result_node.start_point[0] + self.start_line
                                        ]
                                        <= 1
                                        else 1
                                    )
                                lable_line = (
                                    result_node.start_point[0] + self.start_line
                                )
                                while (
                                    lable_line in all_nodes
                                    and len(all_nodes[lable_line]) == 0
                                ):
                                    lable_line += 1
                                if lable_line not in all_nodes:
                                    lable_line -= 1
                                for node in all_nodes[lable_line]:
                                    if (
                                        node.type == "METHOD"
                                        or "METHOD_RETURN"
                                        in str(node.type)
                                    ):
                                        continue
                                    visited = set()
                                    queue = deque([(node, node, 1)])
                                    while queue:
                                        pred_node, node, depth = queue.popleft()
                                        if depth > level:
                                            continue
                                        if node not in visited:
                                            visited.add(node)
                                            result_nodes.add(node)
                                            if node.line_number is not None:
                                                result_lines.add(node.line_number)
                                                try:
                                                    result_weights[
                                                        node.line_number
                                                    ] += 1 / (depth + 1)
                                                    result_weights[node.line_number] = (
                                                        result_weights[node.line_number]
                                                        if result_weights[
                                                            node.line_number
                                                        ]
                                                        <= 1
                                                        else 1
                                                    )
                                                except:
                                                    result_weights[node.line_number] = (
                                                        1 / (depth + 1)
                                                    )
                                                    result_weights[node.line_number] = (
                                                        result_weights[node.line_number]
                                                        if result_weights[
                                                            node.line_number
                                                        ]
                                                        <= 1
                                                        else 1
                                                    )
                                                if (
                                                    node != pred_node
                                                    and pred_node.line_number
                                                    is not None
                                                ):
                                                    result_edges.add(
                                                        (
                                                            pred_node.line_number,
                                                            node.line_number,
                                                        )
                                                    )
                                            if (
                                                node.type != "METHOD"
                                                and "METHOD_PARAMETER_IN"
                                                not in str(node.type)
                                            ):
                                                for succ_node in node.succ_cfg_nodes:
                                                    if (
                                                        succ_node.line_number is None
                                                        or int(succ_node.line_number)
                                                        == sys.maxsize
                                                    ):
                                                        continue
                                                    queue.append(
                                                        (node, succ_node, depth + 1)
                                                    )
                else:
                    for_query = """
                    ( for_statement)@name(   switch_statement)@name(while_statement)@name
                    """
                    results = ast_parser.query_all(for_query)
                    for identifier_node in results:
                        if (
                            line - self.start_line + 1
                            < identifier_node.start_point[0] + 1
                            or line - self.start_line + 1
                            > identifier_node.end_point[0] + 1
                        ):
                            continue
                        if self.all_flow_control_lines[line] == "break":
                            break_query = "( break_statement)@name"
                            body = identifier_node.child_by_field_name("body")
                            break_results = ast_parser.query_all(break_query, node=body)
                            for res in break_results:
                                if line - self.start_line + 1 != res.start_point[0] + 1:
                                    continue
                                end_line = (
                                    identifier_node.end_point[0] + self.start_line
                                )
                                while end_line not in all_nodes:
                                    end_line += 1
                                result_lines.add(end_line)
                                result_edges.add((line, end_line))
                                try:
                                    result_weights[end_line] += 1 / 2
                                    result_weights[end_line] = (
                                        result_weights[end_line]
                                        if result_weights[end_line] <= 1
                                        else 1
                                    )
                                except:
                                    result_weights[end_line] = 1 / 2
                                    result_weights[end_line] = (
                                        result_weights[end_line]
                                        if result_weights[end_line] <= 1
                                        else 1
                                    )
                        else:
                            continue_query = "(continue_statement)@name"
                            body = identifier_node.child_by_field_name("body")
                            continue_results = ast_parser.query_all(
                                continue_query, node=body
                            )
                            for res in continue_results:
                                if line - self.start_line + 1 != res.start_point[0] + 1:
                                    continue
                                end_line = (
                                    identifier_node.start_point[0] + self.start_line
                                )
                                while end_line not in all_nodes:
                                    end_line += 1
                                result_lines.add(end_line)
                                result_edges.add((line, end_line))
                                try:
                                    result_weights[end_line] += 1 / 2
                                    result_weights[end_line] = (
                                        result_weights[end_line]
                                        if result_weights[end_line] <= 1
                                        else 1
                                    )
                                except:
                                    result_weights[end_line] = 1 / 2
                                    result_weights[end_line] = (
                                        result_weights[end_line]
                                        if result_weights[end_line] <= 1
                                        else 1
                                    )
                need_header_line = flag
                if line not in all_nodes:
                    continue    
                for node in all_nodes[line]:
                    if node.type == "METHOD":
                        continue
                    if "[" not in str(node.type):
                        continue
                    if (
                        "METHOD_RETURN" in str(node.type)
                        and not need_header_line
                    ):
                        continue
                    visited = set()
                    queue = deque([(node, node, 1)])
                    while queue:
                        node, succ_node, depth = queue.popleft()
                        if depth > level:
                            continue
                        if node not in visited:
                            visited.add(node)
                            result_nodes.add(node)
                            if node.line_number is not None:
                                result_lines.add(node.line_number)
                                try:
                                    result_weights[node.line_number] += 1 / (depth + 1)
                                    result_weights[node.line_number] = (
                                        result_weights[node.line_number]
                                        if result_weights[node.line_number] <= 1
                                        else 1
                                    )
                                except:
                                    result_weights[node.line_number] = 1 / (depth + 1)
                                    result_weights[node.line_number] = (
                                        result_weights[node.line_number]
                                        if result_weights[node.line_number] <= 1
                                        else 1
                                    )
                                if (
                                    node != succ_node
                                    and succ_node.line_number is not None
                                ):
                                    result_edges.add(
                                        (node.line_number, succ_node.line_number)
                                    )
                            if "[" not in str(node.type):
                                continue
                            if (
                                node.type != "METHOD"
                                and "METHOD_PARAMETER_IN"
                                not in str(node.type)
                            ):
                                for pred_node in node.pred_cfg_nodes:
                                    if (
                                        pred_node.line_number is None
                                        or int(pred_node.line_number) == sys.maxsize
                                    ):
                                        continue
                                    queue.append((pred_node, node, depth + 1))

        return result_lines, result_nodes, result_edges, result_weights

    def slice_vul_detect(
        self,
        cache_dir: str,
        criteria_lines: set[int],
        criteria_identifier,
        semantic_model: bool,
        need_header_line=False,
        is_rel=False,
        target_args: set = set(),
    ):
        if self.pdg is None:
            return set(), set(), set(), "", "", {}, set()
        assert self.pdg is not None
        if is_rel:
            criteria_lines = set(
                [line + self.start_line - 1 for line in criteria_lines]
            )
        all_lines = set(self.lines.keys())
        all_nodes: dict[int, list[PDGNode]] = {
            line: self.pdg.get_nodes_by_line_number(line) for line in all_lines
        }
        if self.end_line not in all_nodes:
            all_nodes[self.end_line] = []
        criteria_nodes: set[PDGNode] = set()
        for line in criteria_lines:
            for node in self.pdg.get_nodes_by_line_number(line):
                node.is_patch_node = True
                node.add_attr("color", "red")
                criteria_nodes.add(node)
        slice_result_edges = set()

        temp_lines = criteria_lines.copy()
        if need_header_line:
            for slice_line in temp_lines:
                if slice_line not in all_nodes:
                    continue
                for node in all_nodes[slice_line]:
                    if node.type != "METHOD":
                        continue
                    for pred_node in node.succ_cfg_nodes:
                        if (
                            pred_node.line_number is None
                            or int(pred_node.line_number) == sys.maxsize
                        ):
                            continue
                        criteria_lines.add(int(pred_node.line_number))
                        criteria_nodes.add(pred_node)
                        slice_result_edges.add((slice_line, int(pred_node.line_number)))

        slice_result_lines = set(criteria_lines)

        result_lines, backward_nodes, backward_weight, backward_edges = (
            self.backward_slice_vul_detect(
                criteria_lines,
                criteria_nodes,
                criteria_identifier,
                all_nodes,
                need_header_line,
            )
        )

        slice_result_lines.update(result_lines)
        criteria_lines.update(result_lines)
        if need_header_line:
            result_lines, forward_nodes, forward_weights, forward_edges = (
                self.forward_slice_with_weight(
                    self,
                    cache_dir,
                    criteria_lines,
                    criteria_nodes,
                    criteria_identifier,
                    semantic_model,
                    all_nodes,
                    level=4,
                    need_header_line=need_header_line,
                    target_args = target_args,
                )
            )
        else:
            result_lines, forward_nodes, forward_edges, forward_weights = (
                self.customized_forward_slice_vul_detect(
                    criteria_lines, criteria_nodes, criteria_identifier, all_nodes
                )
            )
            if len(result_lines) == len(criteria_lines):
                result_lines, forward_nodes, forward_weights, forward_edges = (
                    self.forward_slice_with_weight(
                        self,
                        cache_dir,
                        criteria_lines,
                        criteria_nodes,
                        criteria_identifier,
                        semantic_model,
                        all_nodes,
                        level=4,
                        need_header_line=need_header_line,
                        target_args = target_args,
                    )
                )
        slice_result_lines.update(result_lines)
        slice_nodes = (
            criteria_nodes.union(backward_nodes)
            .union(forward_nodes)
        )
        slice_result_edges = backward_edges.union(forward_edges)
        slice_result_weight = {}
        for line in criteria_lines:
            slice_result_weight[line] = 1
        for line in backward_weight:
            try:
                slice_result_weight[line] += backward_weight[line]
                slice_result_weight[line] = (
                    slice_result_weight[line] if slice_result_weight[line] <= 1 else 1
                )
            except:
                slice_result_weight[line] = backward_weight[line]
                slice_result_weight[line] = (
                    slice_result_weight[line] if slice_result_weight[line] <= 1 else 1
                )

        for line in forward_weights:
            try:
                slice_result_weight[line] += forward_weights[line]
                slice_result_weight[line] = (
                    slice_result_weight[line] if slice_result_weight[line] <= 1 else 1
                )
            except:
                slice_result_weight[line] = forward_weights[line]
                slice_result_weight[line] = (
                    slice_result_weight[line] if slice_result_weight[line] <= 1 else 1
                )

        slice_result_lines.add(self.start_line)
        slice_result_lines.add(self.end_line)
        slice_result_rel_lines = set(
            [
                line - self.start_line + 1
                for line in slice_result_lines
                if line >= self.start_line and line <= self.end_line
            ]
        )



        slice_result_lines = set(
            [line + self.start_line - 1 for line in slice_result_rel_lines]
        )

        for inedge, outedge in slice_result_edges.copy():
            if inedge not in slice_result_lines or outedge not in slice_result_lines:
                slice_result_edges.remove((inedge, outedge))

        for sline in slice_result_lines:
            for node in self.pdg.get_nodes_by_line_number(sline):
                slice_nodes.add(node)

        slice_result_rel_lines = set(slice_result_rel_lines)
        sliced_code = self.code_by_lines(slice_result_rel_lines)
        abs_sliced_code = self.abstract_code_by_lines(slice_result_rel_lines)

        return (
            slice_result_lines,
            slice_result_rel_lines,
            slice_nodes,
            sliced_code,
            abs_sliced_code,
            slice_result_weight,
            slice_result_edges,
        )

    def slice_by_diff_lines_detect(
        self,
        criteria_lines: set,
        cache_dir: str,
        semantic_model: bool,
        original_code_path: str = None,
        criteria_identifier: set = set(),
        need_criteria_identifier: bool = False,
        write_dot: bool = False,
        level=0,
        role="target",
    ) :
        if original_code_path:
            self.original_code_path = original_code_path
        
        diff_identifiers = self.diff_identifiers if need_criteria_identifier else {}
        modified_parameters = (
            self.modified_parameters if need_criteria_identifier else {}
        )
        criteria_identifier.update(diff_identifiers)
        if need_criteria_identifier:
            for line in modified_parameters.keys():
                try:
                    criteria_identifier.update(modified_parameters[line])
                except:
                    criteria_identifier.update(modified_parameters[line])

        for identifier in criteria_identifier:
            if "->" in identifier:
                if len(identifier.split("->")) > 2:
                    criteria_identifier.add("->".join(identifier.split("->")[:-1]))
                else:
                    criteria_identifier.add(identifier.split("->")[0])
            elif "." in identifier:
                if len(identifier.split(".")) > 2:
                    criteria_identifier.add(".".join(identifier.split(".")[:-1]))
                else:
                    criteria_identifier.add(identifier.split(".")[0])
        if level > 1:
            return None
        if self.start_line in criteria_lines:
            need_header_line = True
        else:
            need_header_line = False
        
        slice_results = self.slice_vul_detect(
            cache_dir,
            criteria_lines,
            criteria_identifier,
            semantic_model,
            is_rel=False,
            need_header_line=need_header_line,
        )
        if write_dot and slice_results is not None:
            if self.pdg is None:
                return slice_results + (self.lines, self.abs_lines, criteria_identifier)
            assert self.pdg is not None and self.method_dir is not None
            slice_nodes:set[PDGNode] = slice_results[2]
            valid_nodes = [node for node in slice_nodes if isinstance(node, joern.PDGNode)]
            g = nx.subgraph(self.pdg.g, [node.node_id for node in valid_nodes])
            os.makedirs(self.method_dir, exist_ok=True)
            nx.nx_agraph.write_dot(g, os.path.join(self.dot_dir, f"{role}_slicing.dot"))
            fp = open(f"{self.method_dir}/{role}_slicing{self.file_suffix}", "w")
            fp.write(slice_results[3])
            fp.close()

            slice_result_lines = slice_results[0]
            line = self.start_line
            while line < self.end_line:
                if self.lines[line].startswith("@"):
                    slice_result_lines.add(line)
                else:
                    slice_result_lines.add(line)
                    if not self.lines[line].strip().replace("\n", "").endswith("{"):
                        line += 1
                        slice_result_lines.add(line)
                    break
                line += 1

            criteria_lines_set_file_path = f"{self.method_dir}/criteria_lines_set.json"
            if os.path.exists(criteria_lines_set_file_path):
                with open(criteria_lines_set_file_path, "r") as f:
                    criteria_lines_set = set(json.load(f)) | set(slice_result_lines)
                slice_result_lines = criteria_lines_set
            else:
                with open(criteria_lines_set_file_path, "w") as f:
                    json.dump(list(slice_result_lines), f)

            slice_result_rel_lines = set(
                [
                    line - self.start_line + 1
                    for line in slice_result_lines
                    if self.end_line >= line >= self.start_line
                ]
            )

            ast = ASTParser(self.code, self.language)
            if self.language == Language.JAVA:
                body_node = ast.query_oneshot("(method_declaration body: (block)@body)")
                if body_node is None:
                    return
                slice_result_rel_lines = self.ast_dive_java(body_node, slice_result_rel_lines)
                slice_result_lines = set([line + self.start_line - 1 for line in slice_result_rel_lines])
            elif self.language == Language.CPP:
                body_node = ast.query_oneshot("(function_definition body: (compound_statement)@body)")
                if body_node is None:
                    return
                slice_result_rel_lines = self.ast_dive_c(body_node, slice_result_rel_lines)

            slice_result_lines = set([line + self.start_line - 1 for line in slice_result_rel_lines])
            sliced_code = self.code_by_lines(slice_result_rel_lines)

            fp = open(f"{self.method_dir}/{role}_slicing_code{self.file_suffix}", "w")
            fp.write(sliced_code)
            fp.close()
            from Constructing_Enhanced_UDG.joern_enhance import add_global_variables
            add_global_variables(f"{self.method_dir}/{role}_slicing_code{self.file_suffix}", f"{self.original_code_path}/{self.file.path}", self.language)

        return slice_results + (self.lines, self.abs_lines, criteria_identifier)

    def slice_by_header_line_vul_detect(
        self,
        cache_dir: str,
        semantic_model: bool,
        args_list: list = [],
        criteria_identifier: set = set(),
        need_criteria_identifier: bool = False,
        write_dot: bool = False,
        target_args: set = set(),
        original_code_path: str = None,
    ):
        if original_code_path:
            self.original_code_path = original_code_path
        
        true_criteria_identifier = {}
        identifiers = []
        parser = ASTParser(self.code, self.language)
        if self.language == Language.JAVA:
            parameters = parser.query_by_capture_name(
                "(formal_parameter   ((identifier) @param_name))",
                "param_name",
            )
        else:
            parameters = parser.query_by_capture_name(
                "(parameter_list  ( parameter_declaration (identifier)@name ))(pointer_declarator(identifier))@name",
                "name",
            )
        parameters.sort(key=lambda node: node.start_point)
        for parameter in parameters:
            identifiers.append(parameter.text.decode())
        if need_criteria_identifier:
            param_arg_pairs = zip(identifiers, args_list)
            arg_param_mapping = {}
            for param, arg in param_arg_pairs:
                arg_param_mapping[arg] = param
            if len(criteria_identifier) == 0:
                for identifier in identifiers:
                    try:
                        true_criteria_identifier[self.start_line].append(identifier)
                    except:
                        true_criteria_identifier[self.start_line] = [identifier]
            else:
                for identifier in criteria_identifier:
                    try:
                        true_criteria_identifier[self.start_line].append(
                            arg_param_mapping[identifier]
                        )
                    except:
                        true_criteria_identifier[self.start_line] = [
                            arg_param_mapping[identifier]
                        ]

        for line in true_criteria_identifier:
            for identifier in list(true_criteria_identifier[line]):
                if "->" in identifier:
                    if len(identifier.split("->")) > 2:
                        true_criteria_identifier[line].add(
                            "->".join(identifier.split("->")[:-1])
                        )
                    else:
                        true_criteria_identifier[line].add(identifier.split("->")[0])
                elif "." in identifier:
                    if len(identifier.split(".")) > 2:
                        true_criteria_identifier[line].add(
                            ".".join(identifier.split(".")[:-1])
                        )
                    else:
                        true_criteria_identifier[line].add(identifier.split(".")[0])

        criteria_lines = set()
        criteria_identifier = set()
        for line in true_criteria_identifier:
            criteria_identifier.update(true_criteria_identifier[line])
        vis = criteria_identifier.copy()
        if self.sensitive_api_method == True:
            criteria_lines.add(self.start_line)
            criteria_lines.update(self.body_lines)
        else:
            for line in range(self.start_line, self.end_line + 1):
                for identifier in criteria_identifier:
                    if identifier in self.lines[line] and identifier in vis:
                        criteria_lines.add(line)
                        vis.remove(identifier)
                if len(vis) == 0:
                    break
            criteria_lines.add(self.start_line)
        
        if semantic_model:
            tmp_target_arg = set()
            param_arg_pairs = zip(identifiers, args_list)
            arg_param_mapping = {}
            for param, arg in param_arg_pairs:
                arg_param_mapping[arg] = param
            for target_arg in target_args:
                if target_arg in arg_param_mapping:
                    tmp_target_arg.add(arg_param_mapping[target_arg])
            slice_results = self.slice_vul_detect(
                cache_dir,
                criteria_lines,
                criteria_identifier,
                semantic_model,
                is_rel=False,
                need_header_line=True,
                target_args = tmp_target_arg,
            )
        else:
            slice_results = self.slice_vul_detect(
                cache_dir,
                criteria_lines,
                criteria_identifier,
                semantic_model,
                is_rel=False,
                need_header_line=True,
            )
        role = "target"
        if write_dot and slice_results is not None:
            if self.pdg is None:
                return slice_results + (self.lines, self.abs_lines, criteria_identifier)
            assert self.pdg is not None and self.method_dir is not None
            slice_nodes:set[PDGNode] = slice_results[2]
            valid_nodes = [node for node in slice_nodes if isinstance(node, joern.PDGNode)]
            g = nx.subgraph(self.pdg.g, [node.node_id for node in valid_nodes])
            os.makedirs(self.method_dir, exist_ok=True)
            nx.nx_agraph.write_dot(g, os.path.join(self.dot_dir, f"{role}_slicing.dot"))
            fp = open(f"{self.method_dir}/{role}_slicing{self.file_suffix}", "w")
            fp.write(slice_results[3])
            fp.close()

            slice_result_lines, slice_result_weight, slice_result_edges = (
                slice_results[0],
                slice_results[5],
                slice_results[6],
            )            
            line = self.start_line
            while line < self.end_line:
                if self.lines[line].startswith("@"):
                    slice_result_lines.add(line)
                else:
                    slice_result_lines.add(line)
                    if not self.lines[line].strip().replace("\n", "").endswith("{"):
                        line += 1
                        slice_result_lines.add(line)
                    break
                line += 1
            

            slice_result_rel_lines = set(
                [
                    line - self.start_line + 1
                    for line in slice_result_lines
                    if self.end_line >= line >= self.start_line
                ]
            )
            ast = ASTParser(self.code, self.language)
            if self.language == Language.JAVA:
                body_node = ast.query_oneshot("(method_declaration body: (block)@body)")
                if body_node is None:
                    return
                slice_result_rel_lines = self.ast_dive_java(body_node, slice_result_rel_lines)
                slice_result_lines = set([line + self.start_line - 1 for line in slice_result_rel_lines])
            elif self.language == Language.CPP:
                body_node = ast.query_oneshot("(function_definition body: (compound_statement)@body)")
                if body_node is None:
                    return
                slice_result_rel_lines = self.ast_dive_c(body_node, slice_result_rel_lines)

            slice_result_lines = set([line + self.start_line - 1 for line in slice_result_rel_lines])
            if self.end_line not in slice_result_lines:
                slice_result_lines.add(self.end_line)
            
            criteria_lines_set_file_path = f"{self.method_dir}/criteria_lines_set.json"
            if os.path.exists(criteria_lines_set_file_path):
                with open(criteria_lines_set_file_path, "r") as f:
                    criteria_lines_set = set(json.load(f)) | set(slice_result_lines)
                slice_result_lines = criteria_lines_set
            else:
                with open(criteria_lines_set_file_path, "w") as f:
                    json.dump(list(slice_result_lines), f)

            slice_result_rel_lines = set(
                [
                    line - self.start_line + 1
                    for line in slice_result_lines
                    if self.end_line >= line >= self.start_line
                ]
            )

            sliced_code = self.code_by_lines(slice_result_rel_lines)
            abs_sliced_code = self.abstract_code_by_lines(slice_result_rel_lines)
            fp = open(f"{self.method_dir}/{role}_slicing_code{self.file_suffix}", "w")
            fp.write(sliced_code)
            fp.close()
            from Constructing_Enhanced_UDG.joern_enhance import add_global_variables
            add_global_variables(f"{self.method_dir}/{role}_slicing_code{self.file_suffix}", f"{self.original_code_path}/{self.file.path}", self.language)

        return slice_results + (self.lines, self.abs_lines, criteria_identifier)



    @staticmethod
    def ast_dive_java(root: Node, slice_lines: set[int]) -> set[int]:
        def is_in_node(line: int, node: Node) -> bool:
            node_start_line = node.start_point[0] + 1
            node_end_line = node.end_point[0] + 1
            return node_start_line <= line <= node_end_line
        sensitive_node_types = [
            "throw_statement",
            "return_statement",
            "break_statement",
            "continue_statement",
        ]
        for node in root.named_children:
            tmp_lines = set()
            node_start_line = node.start_point[0] + 1
            node_end_line = node.end_point[0] + 1
            for sline in slice_lines:
                if is_in_node(sline, node):
                    tmp_lines.add(sline)
            if len(tmp_lines) == 0:
                continue
            if node.type == "expression_statement":
                slice_lines.update([line for line in range(node_start_line, node_end_line + 1)])
            elif node.type == "if_statement":
                condition_node = node.child_by_field_name("condition")
                if condition_node is None:
                    continue
                slice_lines.update([node_start_line])
                slice_lines.update([condition_node.start_point[0] + 1, condition_node.end_point[0] + 1])
                consequence_node = node.child_by_field_name("consequence")
                if consequence_node is None:
                    continue
                slice_lines.update([consequence_node.start_point[0] + 1, consequence_node.end_point[0] + 1])
                for child_node in consequence_node.named_children:
                    if child_node.type in sensitive_node_types:
                        slice_lines.update([line + 1 for line in range(child_node.start_point[0], child_node.end_point[0] + 1)])
                Method.ast_dive_java(consequence_node, slice_lines)

                alternative_node = node.child_by_field_name("alternative")
                if alternative_node is None:
                    continue
                next_alternative_node = alternative_node.child_by_field_name("alternative")
                if next_alternative_node is None:
                    slice_lines.update([alternative_node.start_point[0] + 1], [alternative_node.end_point[0] + 1])
                    for child_node in alternative_node.named_children:
                        if child_node.type in sensitive_node_types:
                            slice_lines.update([line + 1 for line in range(child_node.start_point[0], child_node.end_point[0] + 1)])
                else:
                    slice_lines.update([alternative_node.start_point[0] + 1])
                    alternative_consequence_node = alternative_node.child_by_field_name("consequence")
                    for child_node in alternative_consequence_node.named_children:
                        if child_node.type in sensitive_node_types:
                            slice_lines.update([line + 1 for line in range(child_node.start_point[0], child_node.end_point[0] + 1)])
                Method.ast_dive_java(alternative_node, slice_lines)
            elif node.type == "try_statement":
                slice_lines.update([node_start_line, node_end_line])
                body_node = node.child_by_field_name("body")
                if body_node is None:
                    continue
                slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                Method.ast_dive_java(body_node, slice_lines)

                catch_node = ASTParser.children_by_type_name(node, "catch_clause")
                for child_node in catch_node:
                    slice_lines.update([child_node.start_point[0] + 1, child_node.end_point[0] + 1])
                    body_node = child_node.child_by_field_name("body")
                    if body_node is None:
                        continue
                    for tmp_body_node in body_node.named_children:
                        if tmp_body_node.type in sensitive_node_types:
                            slice_lines.update([line + 1 for line in range(tmp_body_node.start_point[0], tmp_body_node.end_point[0] + 1)])
                    Method.ast_dive_java(body_node, slice_lines)

                finally_node = ASTParser.child_by_type_name(node, "finally_clause")
                if finally_node is None:
                    continue
                slice_lines.update([finally_node.start_point[0] + 1, finally_node.end_point[0] + 1])
                for child_node in finally_node.named_children:
                    if child_node.type in sensitive_node_types:
                        slice_lines.update([line + 1 for line in range(child_node.start_point[0], child_node.end_point[0] + 1)])
                Method.ast_dive_java(finally_node, slice_lines)
            elif node.type == "for_statement":
                body_node = node.child_by_field_name("body")
                if body_node is None:
                    continue
                init_node = node.child_by_field_name("init")
                if init_node is None:
                    continue
                if init_node.start_point[0] + 1 in slice_lines:
                    slice_lines.update([init_node.start_point[0] + 1, init_node.end_point[0] + 1])
                    slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                condition_node = node.child_by_field_name("condition")
                if condition_node is None:
                    continue
                if condition_node.start_point[0] + 1 in slice_lines:
                    slice_lines.update([condition_node.start_point[0] + 1, condition_node.end_point[0] + 1])
                    slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                update_node = node.child_by_field_name("update")
                if update_node is None:
                    continue
                if update_node.start_point[0] + 1 in slice_lines:
                    slice_lines.update([update_node.start_point[0] + 1, update_node.end_point[0] + 1])
                    slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                Method.ast_dive_java(body_node, slice_lines)
            elif node.type == "block":
                slice_lines.update([node_start_line, node_end_line])
                Method.ast_dive_java(node, slice_lines)
            else:
                slice_lines.update([line for line in range(node_start_line, node_end_line + 1)])
        return slice_lines

    def ast_dive_c(self, root: Node, slice_lines: set[int]) -> set[int]:
        def is_in_node(line: int, node: Node) -> bool:
            node_start_line = node.start_point[0] + 1
            node_end_line = node.end_point[0] + 1
            return node_start_line <= line <= node_end_line
        for node in root.named_children:
            tmp_lines = set()
            node_start_line = node.start_point[0] + 1
            node_end_line = node.end_point[0] + 1
            for sline in slice_lines:
                if is_in_node(sline, node):
                    tmp_lines.add(sline)
            if len(tmp_lines) == 0:
                continue
            if node.type == "expression_statement":
                slice_lines.update([line for line in range(node_start_line, node_end_line + 1)])
            elif node.type == "if_statement":
                condition_node = node.child_by_field_name("condition")
                if condition_node is None:
                    continue
                slice_lines.update([node_start_line])
                slice_lines.update([condition_node.start_point[0] + 1, condition_node.end_point[0] + 1])
                consequence_node = node.child_by_field_name("consequence")
                if consequence_node is None:
                    continue
                slice_lines.update([consequence_node.start_point[0] + 1, consequence_node.end_point[0] + 1])
                self.ast_dive_c(consequence_node, slice_lines)

                alternative_node = node.child_by_field_name("alternative")
                if alternative_node is None:
                    continue
                next_alternative_node = alternative_node.child_by_field_name("alternative")
                if next_alternative_node is None:
                    slice_lines.update([alternative_node.start_point[0] + 1], [alternative_node.end_point[0] + 1])
                else:
                    slice_lines.update([alternative_node.start_point[0] + 1])
                self.ast_dive_c(alternative_node, slice_lines)
            elif node.type == "for_statement":
                body_node = node.child_by_field_name("body")
                if body_node is None:
                    continue
                slice_lines.update([node.start_point[0] + 1])
                slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                self.ast_dive_c(body_node, slice_lines)
            elif node.type == "switch_statement":
                body_node = node.child_by_field_name("body")
                if body_node is None:
                    continue
                condition_node = node.child_by_field_name("condition")
                if condition_node is None:
                    continue
                slice_lines.update([condition_node.start_point[0] + 1, condition_node.end_point[0] + 1])
                slice_lines.update([body_node.start_point[0] + 1, body_node.end_point[0] + 1])
                self.ast_dive_c(body_node, slice_lines)
            elif node.type == "case_statement":
                slice_lines.add(node_start_line)
                self.ast_dive_c(node, slice_lines)
            elif node.type == "block" or node.type == "compound_statement":
                slice_lines.update([node_start_line, node_end_line])
                self.ast_dive_c(node, slice_lines)
            else:
                slice_lines.update([line for line in range(node_start_line, node_end_line + 1)])
        return slice_lines