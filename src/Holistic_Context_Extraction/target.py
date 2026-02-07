from __future__ import annotations
from typing import Optional

import os
from functools import cached_property, lru_cache

import cpu_heater
from pydriller.domain.commit import Commit
from tqdm import tqdm

import Constructing_Enhanced_UDG.ast_parser as ast_parser
from . import code_transformation
import Constructing_Enhanced_UDG.format_code as format_code
from Constructing_Enhanced_UDG.ast_parser import ASTParser
from Constructing_Enhanced_UDG.codefile import CodeFile
from Constructing_Enhanced_UDG.common import Language
from .project import Project
import scubatrace
from .get_shortest_path import shortest_path_from_list


class LazyFileLoader:
    def __init__(self, repo_path: str, language: Language):
        self.repo_path = repo_path
        self.language = language
        self._file_paths = set()
        self._scan_files()

    def _scan_files(self):
        suffix_list = []
        if self.language == Language.CPP:
            suffix_list = ["c", "cpp", "cc", "cxx", "c++", "hpp", "h", "hxx", "h++"]
        elif self.language == Language.JAVA:
            suffix_list = ["java"]
            
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.split(".")[-1] in suffix_list:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    self._file_paths.add(rel_path)

    @lru_cache(maxsize=256)
    def __getitem__(self, key):
        if key not in self._file_paths:
             raise KeyError(f"{key}")
        
        file_path = os.path.join(self.repo_path, key)
        try:
            with open(file_path, "r", errors="replace") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file {file_path}: {e}")
            return ""

    def __contains__(self, key):
        return key in self._file_paths

    def __iter__(self):
        return iter(self._file_paths)

    def keys(self):
        return self._file_paths
        
    def items(self):
        for key in self._file_paths:
            yield key, self[key]

    def values(self):
        for key in self._file_paths:
            yield self[key]
            
    def get(self, key, default=None):
        if key in self._file_paths:
            return self[key]
        return default


class Target:
    def __init__(
        self,
        repo_path: str,
        matching_method: list[str],
        language: Language,
        line_matching: dict[str, set[int]],
        format_lambda: bool = False
    ):
        self.path = repo_path
        self.include_files = set()
        self.matching_methods = matching_method
        self.project: Optional[Project] = None
        self.language = language
        self.line_matching = line_matching
        self.criteria_identifier = set()
        self.format_lambda = format_lambda

        self.include_methods = set()
        self.project = Project("target", self.analysis_files, self.language)
        if self.line_matching == {}:
            for method_name in self.matching_methods:
                method = self.project.get_method(method_name)
                assert method is not None
                identifiers = []
                parser = ASTParser(method.code, self.language)
                if self.language == Language.JAVA:
                    parameters = parser.query_all("(formal_parameter   ((identifier) @param_name))")
                else:
                    parameters = parser.query_all(
                        "(parameter_list  ( parameter_declaration (identifier)@name ))(pointer_declarator(identifier))@name"
                    )
                assert parameters is not None
                for parameter in parameters:
                    identifiers.append(parameter.text.decode())
                vis = identifiers.copy()
                st = method.start_line
                while st < method.end_line:
                    if method.lines[st].lstrip().startswith("@"):
                        st += 1
                    else:
                        break
                
                for line in range(st+1, method.end_line + 1):
                    for identifier in identifiers:
                        if identifier not in vis:
                            continue
                        if identifier in method.lines[line]:
                            if method_name not in self.line_matching:
                                self.line_matching[method_name] = set()
                            self.line_matching[method_name].add(line)
                            self.criteria_identifier.add(identifier)
                            vis.remove(identifier)
                            if len(vis) == 0:
                                break
                    if len(identifiers) == 0:
                        if method_name not in self.line_matching:
                            self.line_matching[method_name] = set()
                        self.line_matching[method_name].add(line)
                        self.criteria_identifier.add(identifier)
                    if len(vis) == 0:
                        break

    @cached_property
    def files(self):
        return LazyFileLoader(self.path, self.language)

    def get_file_content(self, include_code):
        methods = set()
        method_parser = ASTParser(include_code, self.language)
        if self.language == Language.CPP:
            nodes = method_parser.query_all(ast_parser.TS_C_METHOD)
            for node in nodes:
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
                methods.add((name_node.text.decode(), node.text.decode()))
        elif self.language == Language.JAVA:
            nodes = method_parser.query_all(ast_parser.TS_JAVA_METHOD)
            for node in nodes:
                parameters_node = node.child_by_field_name("parameters")
                if parameters_node is None:
                    parameters = []
                else:
                    parameters = ASTParser.children_by_type_name(
                        parameters_node, "formal_parameter"
                    )
                parameter_signature_list = []
                for param in parameters:
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
                name_node = node.child_by_field_name("name")
                assert name_node is not None and name_node.text is not None
                methods.add(
                    (
                        f"{name_node.text.decode()}",
                        node.text.decode(),
                    )
                )

        return methods

    def get_callee(self, method_code):
        callees = set()
        call = []
        ast = ASTParser(method_code, self.language)
        if self.language == Language.CPP:
            call = ast.query_all(ast_parser.CPP_CALL)
        elif self.language == Language.JAVA:
            call = ast.query_all(ast_parser.JAVA_CALL)
        if len(call) == 0:
            return None

        for node in call:
            callees.add(node.text.decode())

        return callees

    def bfs_search_files(self, filepath, methodname, step=0, visited=None):
        
        if visited is None:
            visited = set()
        
        
        visit_key = (filepath, methodname)
        if visit_key in visited:
            return
        visited.add(visit_key)
        
        
        
        
        
        callees = set()
        
        if os.path.isabs(filepath):
            
            rel_filepath = os.path.relpath(filepath, self.path)
        else:
            
            rel_filepath = filepath
        
        if rel_filepath not in self.include_files:
            self.include_files.add(rel_filepath)
        
        file_contents = self.get_file_content(self.files[rel_filepath])
        for method_name, method_contents in file_contents:
            if methodname == method_name:
                callees = self.get_callee(method_contents)
                
                break
        if callees is None:
            return
        if len(callees) == 0:
            return
        self.include_methods.update(file_contents)
        for method_name, method_contents in list(self.include_methods):
            if method_name in callees:
                
                
                self.bfs_search_files(rel_filepath, method_name, step + 1, visited)
                callees.remove(method_name)
        if len(callees) == 0:
            return
        
        code = self.files[rel_filepath]

        parser = ASTParser(code, self.language)
        if self.language == Language.C or self.language == Language.CPP:
            includes = parser.query_all(ast_parser.CPP_INCLUDE)
            suffix_list = [".c", ".cc", ".cxx", ".cpp"]
            header_list = [".h", ".hpp", ".hxx", ".h++", ".hh"] 
            for include in includes:
                include_name = include.text.decode()
                header = None
                for head in header_list:
                    if include_name.endswith(head):
                        header = head
                        break
                if header is None:
                    header = ".h"
                prefix = os.path.relpath(os.path.dirname(os.path.join(self.path, filepath)), self.path).replace(".", "")
                if os.path.join(prefix, include_name) in self.files:
                    for suffix in suffix_list:
                        if (
                            os.path.join(prefix, include_name.replace(header, suffix))
                            in self.files
                        ):
                            file_contents = self.get_file_content(
                                self.files[
                                    os.path.join(
                                        prefix, include_name.replace(header, suffix)
                                    )
                                ]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    if (
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        )
                                        in self.include_files
                                    ):
                                        continue
                                    self.include_files.add(
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        )
                                    )
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        ),
                                        method_name,
                                        step + 1,
                                        visited,
                                    )
                                    callees.remove(method_name)

                                    if len(callees) == 0:
                                        break

                            if len(callees) == 0:
                                break
                    if len(callees) == 0:
                        break
                    file_contents = self.get_file_content(
                        self.files[os.path.join(prefix, include_name)]
                    )
                    for method_name, method_contents in file_contents:
                        if method_name in callees:
                            if os.path.join(prefix, include_name) in self.include_files:
                                continue
                            self.include_files.add(os.path.join(prefix, include_name))
                            self.include_methods.update(file_contents)
                            self.bfs_search_files(
                                os.path.join(prefix, include_name),
                                method_name,
                                step + 1,
                                visited,
                            )
                            callees.remove(method_name)

                            if len(callees) == 0:
                                break

                    if len(callees) == 0:
                        break
                elif os.path.join(prefix, "include", include_name) in self.files:
                    for suffix in suffix_list:
                        if os.path.isfile(
                            os.path.join(
                                self.path,
                                prefix,
                                include_name.replace(header, suffix),
                            )
                        ) and not os.path.islink(
                            os.path.join(
                                self.path,
                                prefix,
                                include_name.replace(header, suffix),
                            )
                        ):
                            file_contents = self.get_file_content(
                                self.files[
                                    os.path.join(
                                        prefix, include_name.replace(header, suffix)
                                    )
                                ]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    if (
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        )
                                        in self.include_files
                                    ):
                                        continue
                                    self.include_files.add(
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        )
                                    )
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(
                                        os.path.join(
                                            prefix, include_name.replace(header, suffix)
                                        ),
                                        method_name,
                                        step + 1,
                                        visited,
                                    )
                                    callees.remove(method_name)
                        elif (
                            os.path.join(
                                prefix, "src", include_name.replace(header, suffix)
                            )
                            in self.files
                        ):
                            file_contents = self.get_file_content(
                                self.files[
                                    os.path.join(
                                        prefix,
                                        "src",
                                        include_name.replace(header, suffix),
                                    )
                                ]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    if (
                                        os.path.join(
                                            prefix,
                                            "src",
                                            include_name.replace(header, suffix),
                                        )
                                        in self.include_files
                                    ):
                                        continue
                                    self.include_files.add(
                                        os.path.join(
                                            prefix,
                                            "src",
                                            include_name.replace(header, suffix),
                                        )
                                    )
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(
                                        os.path.join(
                                            prefix,
                                            "src",
                                            include_name.replace(header, suffix),
                                        ),
                                        method_name,
                                        step + 1,
                                        visited,
                                    )
                                    callees.remove(method_name)
                                    if len(callees) == 0:
                                        break

                        if len(callees) == 0:
                            break
                    file_contents = self.get_file_content(
                        self.files[os.path.join(prefix, "include", include_name)]
                    )
                    for method_name, method_contents in file_contents:
                        if method_name in callees:
                            if (
                                os.path.join(prefix, "include", include_name)
                                in self.include_files
                            ):
                                continue
                            self.include_files.add(
                                os.path.join(prefix, "include", include_name)
                            )
                            self.include_methods.update(file_contents)
                            self.bfs_search_files(
                                os.path.join(prefix, "include", include_name),
                                method_name,
                                step + 1,
                                visited,
                            )
                            callees.remove(method_name)

                            if len(callees) == 0:
                                break

                    if len(callees) == 0:
                        break
        elif self.language == Language.JAVA:
            includes = parser.query_all(ast_parser.TS_JAVA_IMPORT)
            for include in includes:
                include_name = include.text.decode()
                for dir, _, files in os.walk(self.path):
                    for file in files:
                        if file.endswith(".java") and include_name.replace(".", "/") + ".java" in os.path.join(dir, file):
                            file_contents = self.get_file_content(
                                self.files[os.path.relpath(os.path.join(dir, file), self.path)]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    rel_file_path = os.path.relpath(os.path.join(dir, file), self.path)
                                    if rel_file_path in self.include_files:
                                        continue
                                    self.include_files.add(rel_file_path)
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(rel_file_path, method_name, step + 1, visited)
                                    callees.remove(method_name)
                                    if len(callees) == 0:
                                        break
                            if len(callees) == 0:
                                break
                        if file.endswith(".java") and include_name.replace(".", "/").lower() + "impl.java" in os.path.join(dir, file).lower():
                            file_contents = self.get_file_content(
                                self.files[os.path.relpath(os.path.join(dir, file), self.path)]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    rel_file_path = os.path.relpath(os.path.join(dir, file), self.path)
                                    if rel_file_path in self.include_files:
                                        continue
                                    self.include_files.add(rel_file_path)
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(rel_file_path, method_name, step + 1, visited)
                                    callees.remove(method_name)
                                    if len(callees) == 0:
                                        break
                            if len(callees) == 0:
                                break
                    if len(callees) == 0:
                        break
            
            packages = parser.query_all(ast_parser.TS_JAVA_PACKAGE)
            for package in packages:
                package_name = package.text.decode()
                for dir, _, files in os.walk(self.path):
                    for file in files:
                        if file.endswith(".java") and package_name.replace(".", "/") in os.path.join(dir, file):
                            self.include_files.add(os.path.relpath(os.path.join(dir, file), self.path))
                            file_contents = self.get_file_content(
                                self.files[os.path.relpath(os.path.join(dir, file), self.path)]
                            )
                            for method_name, method_contents in file_contents:
                                if method_name in callees:
                                    rel_file_path = os.path.relpath(os.path.join(dir, file), self.path)
                                    if rel_file_path in self.include_files:
                                        continue
                                    self.include_files.add(rel_file_path)
                                    self.include_methods.update(file_contents)
                                    self.bfs_search_files(rel_file_path, method_name, step + 1, visited)
                                    callees.remove(method_name)
                                    if len(callees) == 0:
                                        break
                            
                            if len(callees) == 0:
                                break
                    if len(callees) == 0:
                        break
            

    def format(self, FilePath):
        if self.path.endswith("/"):
            rel_path = FilePath.replace(self.path, "")
        else:
            rel_path = FilePath.replace(self.path + "/", "")
            
        def content_loader(path):
            return self.files[rel_path]

        codefile = CodeFile(rel_path, None, self.language, isformat=True, loader=content_loader, format_lambda=self.format_lambda)
        return codefile

    def get_files_importing_target(self, project, target_file, visited_files):
        importing_files = []
        for file_path in project.files:
            
            if "test" in file_path.lower():
                continue
            if not file_path.endswith(".java"):
                continue
            
            if file_path in visited_files:
                continue
            
            
            file = project.files[file_path]
            for import_file in file.imports:
                if import_file.relpath == target_file:
                    importing_files.append(file_path)
                    break
        return importing_files

    @cached_property
    def caller_import_files(self):
        from collections import deque
        
        project = scubatrace.Project.create(self.path, language=scubatrace.language.JAVA)
        
        
        initial_targets = set()
        for method_sig in self.matching_methods:
            file_path = method_sig.split("#")[0]
            initial_targets.add(file_path)
        
        
        queue = deque(initial_targets)
        visited = set(initial_targets)  
        
        
        for file_path in initial_targets:
            self.include_files.add(os.path.join(self.path, file_path))
        
        
        level = 0
        while queue:
            level += 1
            current_level_size = len(queue)
            print(f"\n[BFS Level {level}] Processing {current_level_size} files...")
            
            
            current_level_targets = []
            for _ in range(current_level_size):
                current_level_targets.append(queue.popleft())
            
            
            worker_list = []
            for target_file in current_level_targets:
                worker_list.append((project, target_file, visited))
            
            results = cpu_heater.multithreads(
                self.get_files_importing_target, worker_list, max_workers=15, show_progress=True
            )
            
            
            new_files_count = 0
            for importing_files in results:
                if importing_files:
                    for file_path in importing_files:
                        if file_path not in visited:
                            visited.add(file_path)
                            queue.append(file_path)
                            self.include_files.add(os.path.join(self.path, file_path))
                            new_files_count += 1
            
            print(f"[BFS Level {level}] Found {new_files_count} new files")
            
            
            if new_files_count == 0:
                print(f"[BFS] Completed! Total levels: {level}, Total files: {len(visited)}")
                break
        
        return self.include_files

    @cached_property
    def analysis_files(self):
        results = set()
        
        
        if len(self.matching_methods) == 0:
            code_results = []
            
            worker_list = []
            for root, _, files in os.walk(self.path):
                for file in files:
                    if self.language == Language.JAVA and file.endswith(".java") and "/test" not in root.lower() and "test/" not in root.lower() and "/tests" not in root.lower() and "tests/" not in root.lower():
                        results.add(os.path.join(root, file))
                    elif self.language == Language.CPP and file.endswith((".c", ".cpp", ".cc", ".cxx", ".c++", ".h", ".hpp", ".hxx", ".h++")) and ("/test" not in root.lower() and "test/" not in root.lower()):
                        results.add(os.path.join(root, file))
            
            for file in results:
                
                code_results.append(self.format(file))
        else:
            code_results = []
            for method_sig in self.matching_methods:
                if self.language == Language.JAVA:
                    self.bfs_search_files(
                        method_sig.split("#")[0], method_sig.split("#")[1],
                        visited = set()
                    )
                else:
                    self.bfs_search_files(
                        method_sig.split("#")[0], method_sig.split("#")[1],
                        visited = set()
                    )

            worker_list = []
            pre_include_files = self.include_files.copy()  

            if self.language == Language.JAVA:
                target_classes = set()
                target_packages = set()
                
                for file_path in list(self.include_files):
                    if not file_path.endswith(".java") or file_path not in self.files:
                        continue
                    
                    try:
                        content = self.files[file_path]
                        parser = ASTParser(content, self.language)
                        packages = parser.query_all(ast_parser.TS_JAVA_PACKAGE)
                        package_name = ""
                        if packages:
                            package_name = packages[0].text.decode()
                        
                        class_name = os.path.basename(file_path).replace(".java", "")
                        if package_name:
                            full_class_name = f"{package_name}.{class_name}"
                            target_classes.add(full_class_name)
                            target_packages.add(package_name)
                        else:
                            target_classes.add(class_name)
                    except Exception as e:
                        print(f"Error parsing package for {file_path}: {e}")

                
                if target_classes:
                    for file_path, content in self.files.items():
                        if file_path in self.include_files or not file_path.endswith(".java"):
                            continue
                            
                        try:
                            parser = ASTParser(content, self.language)
                            imports = parser.query_all(ast_parser.TS_JAVA_IMPORT)
                            
                            found = False
                            for imp in imports:
                                import_name = imp.text.decode()
                                
                                if import_name in target_classes:
                                    found = True
                                    break
                                
                                
                                
                                parent = imp.parent
                                if parent:
                                    full_import = parent.text.decode()
                                    if "*" in full_import:
                                         
                                         if import_name in target_packages:
                                             
                                             found = True
                                             break
                            
                            if found:
                                self.include_files.add(file_path)
                        except Exception as e:
                            
                            pass
            elif self.language == Language.C or self.language == Language.CPP:
                header_exts = (".h", ".hpp", ".hxx", ".h++", ".hh")
                source_exts = (".c", ".cpp", ".cc", ".cxx")
                all_exts = header_exts + source_exts

                
                filename_to_paths = {}
                for f in self.files:
                    if f.endswith(all_exts):
                        base_name = os.path.splitext(os.path.basename(f))[0]
                        if base_name not in filename_to_paths:
                            filename_to_paths[base_name] = []
                        filename_to_paths[base_name].append(f)

                
                include_to_files = {}  
                for file_path, content in self.files.items():
                    if not file_path.endswith(all_exts):
                        continue
                    if "#include" not in content:
                        continue
                    try:
                        parser = ASTParser(content, self.language)
                        includes = parser.query_all(ast_parser.TS_C_INCLUDE)
                        for inc in includes:
                            clean_inc = inc.text.decode().strip("\"<>").replace(os.sep, "/")
                            bn = os.path.basename(clean_inc)
                            if bn not in include_to_files:
                                include_to_files[bn] = []
                            include_to_files[bn].append((file_path, clean_inc))
                    except Exception:
                        continue

                
                worklist = list(self.include_files)
                processed_targets = set()  
                
                while worklist:
                    current_file = worklist.pop(0)
                    target_path = current_file.replace(os.sep, "/")
                    if target_path in processed_targets:
                        continue
                    processed_targets.add(target_path)

                    targets_to_check = {target_path}
                    base_name = os.path.splitext(os.path.basename(current_file))[0]

                    for candidate in filename_to_paths.get(base_name, []):
                        if candidate not in self.include_files:
                            self.include_files.add(candidate)
                            worklist.append(candidate)
                        targets_to_check.add(candidate.replace(os.sep, "/"))
                    
                    for t in targets_to_check:
                        bn = os.path.basename(t)
                        if bn in include_to_files:
                            for candidate_file, candidate_inc in include_to_files[bn]:
                                if candidate_file in self.include_files:
                                    continue

                                if t == candidate_inc or t.endswith("/" + candidate_inc):
                                    self.include_files.add(candidate_file)
                                    worklist.append(candidate_file)

                                    c_base_name = os.path.splitext(os.path.basename(candidate_file))[0]
                                    for twin in filename_to_paths.get(c_base_name, []):
                                        if twin not in self.include_files:
                                            self.include_files.add(twin)
                                            worklist.append(twin)

            worker_list = []

            for file in self.include_files:
                if self.language == Language.JAVA:
                    if not file.endswith(".java"):
                        continue
                elif self.language == Language.CPP:
                    if not (file.endswith(".cpp") or file.endswith(".c") or file.endswith(".cc") or file.endswith(".h") or file.endswith(".hpp") or file.endswith(".hxx") or file.endswith(".h++")):
                        continue

                test_file_name_set = {"test", "tests", "mock", "mocks"}
                if any(f"/{name}" in file.lower() or f"{name}/" in file.lower() for name in test_file_name_set):
                    continue
                if "HpackHuffmanDecoder.java" in file:
                    continue
                
                
                
                code_results.append(self.format(file))

        return code_results
        
