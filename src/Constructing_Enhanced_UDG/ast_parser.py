from typing import Generator

from typing import List, Dict, Optional
from . import common
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser

TS_JAVA_PACKAGE = "(package_declaration (scoped_identifier) @package)(package_declaration (identifier) @package)"
TS_JAVA_IMPORT = "(import_declaration (scoped_identifier) @import)"
TS_JAVA_CLASS = "(class_declaration) @class (enum_declaration) @class"
TS_JAVA_FIELD = "(field_declaration) @field"
TS_C_INCLUDE = "(preproc_include (system_lib_string)@string_content)(preproc_include (string_literal)@string_content)"
TS_C_METHOD = "(function_definition)@method"
TS_COND_STAT = "(if_statement)@name (while_statement)@name (for_statement)@name"
TS_ASSIGN_STAT = "(assignment_expression)@name"
TS_JAVA_METHOD = "(method_declaration) @method (constructor_declaration) @method"
TS_JAVA_METHODNAME = "(method_declaration 	(identifier)@id)(constructor_declaration 	(identifier)@id)"
TS_METHODNAME = "(method_declaration 	(identifier)@id)(constructor_declaration 	(identifier)@id)"
TS_FPARAM = "(formal_parameters)@name"
CPP_CALL = '''
(call_expression (identifier)@name)(call_expression (field_expression)@name)
'''
JAVA_CALL = '''
(method_invocation (identifier)@name)
'''
CPP_INCLUDE = '''
(preproc_include
  path: (string_literal
    (string_content)@incude
  )
)
'''

TS_JAVA_COMMENT = "(line_comment)@name (block_comment)@name"
TS_CPP_COMMENT = "(comment)@name"

class ASTParser:
    def __init__(self, code: str | bytes, language: common.Language | str):
        if language == common.Language.CPP:
            self.LANGUAGE = Language(tscpp.language())
            
            
            
            
        elif language == common.Language.C:
            self.LANGUAGE = Language(tsc.language())
        elif language == common.Language.JAVA:
            self.LANGUAGE = Language(tsjava.language())
        else:
            self.LANGUAGE = Language(tsc.language())
        
        self.parser = Parser(self.LANGUAGE)
        if isinstance(code, str):
            self.tree = self.parser.parse(bytes(code, "utf-8"))
        elif isinstance(code, bytes):
            self.tree = self.parser.parse(code)
        else:
            print(code)
        self.root = self.tree.root_node

    @staticmethod
    def children_by_type_name(node: Node, type: str) -> list[Node]:
        node_list = []
        for child in node.named_children:
            if child.type == type:
                node_list.append(child)
        return node_list

    def query_from_node(self, node: Node, query_str: str):
        query = self.LANGUAGE.query(query_str)
        captures = query.captures(node)
        return captures
        
    @staticmethod
    def child_by_type_name(node: Node, type: str) -> Optional[Node]:
        for child in node.named_children:
            if child.type == type:
                return child
        return None

    def traverse_tree(self) -> Generator[Node, None, None]:
        cursor = self.tree.walk()
        visited_children = False
        while True:
            if not visited_children:
                assert cursor.node is not None
                yield cursor.node
                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

    def query(self, query_str: str, *, node: Optional[Node] = None) -> dict[str, list[Node]]:
        query = self.LANGUAGE.query(query_str)
        if node is not None:
            captures = query.captures(node)
        else:
            captures = query.captures(self.root)
        return captures

    def query_oneshot(self, query_str: str, *, node: Optional[Node] = None) -> Optional[Node]:
        captures = self.query(query_str, node=node)
        for nodes in captures.values():
            return nodes[0]
        return None

    def query_all(self, query_str: str, *, node: Optional[Node] = None) -> list[Node]:
        captures = self.query(query_str, node=node)
        results = []
        for nodes in captures.values():
            results.extend(nodes)
        return results

    def query_by_capture_name(self, query_str: str, capture_name: str, *, node: Optional[Node] = None) -> list[Node]:
        captures = self.query(query_str, node=node)
        return captures.get(capture_name, [])

    def get_error_nodes(self, *, node: Optional[Node] = None) -> list[Node]:
        query_str = """
        (ERROR)@error
        """
        return self.query_by_capture_name(query_str, "error", node=node)

    def get_all_identifier_node(self) -> list[Node]:
        query_str = """
        (identifier)@id
        """
        return self.query_by_capture_name(query_str, "id")

    def get_all_conditional_node(self) -> list[Node]:
        query_str = TS_COND_STAT
        return self.query_by_capture_name(query_str, "name")

    def get_all_assign_node(self) -> list[Node]:
        query_str = """
        (declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_all_assign_node_java(self) -> list[Node]:
        query_str = """
        (local_variable_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_all_return_node(self) -> list[Node]:
        query_str = """
        (return_statement)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_all_call_node(self) -> list[Node]:
        query_str = """
        (call_expression)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_all_call_node_java(self) -> list[Node]:
        query_str = """
        (method_invocation)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_all_includes(self) -> list[Node]:
        if self.LANGUAGE == Language(tscpp.language()) or self.LANGUAGE == Language(tsc.language()):
            query_str = """
            (preproc_include)@name
            """
        else:
            query_str = """
            (import_declaration)@name
            """
        return self.query_by_capture_name(query_str, "name")
    
    def get_field_access_identifier(self) -> list[Node]:
        query_str = """
        (field_access field: (identifier)@id)
        """
        return self.query_by_capture_name(query_str, "id")
    
    def get_all_flow_control_goto(self) -> list[Node]:
        query_str = """
        (goto_statement)@label
            """
        return self.query_by_capture_name(query_str, "label")

    def get_all_flow_control_break(self) -> list[Node]:
        query_str = """
        ( break_statement)@name
            """
        return self.query_by_capture_name(query_str, "name")

    def get_all_flow_control(self) -> list[Node]:
        query_str = """
        ( continue_statement)@name
            """
        return self.query_by_capture_name(query_str, "name")
    
    def get_all_field_declaration(self) -> list[Node]:
        query_str = """
        (field_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_method_declaration(self) -> list[Node]:
        query_str = """
        (method_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_method_invocation(self) -> list[Node]:
        query_str = """
            (method_invocation)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_assignment_expression(self) -> list[Node]:
        query_str = """
            (assignment_expression)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_return_statement(self) -> list[Node]:
        query_str = """
            (return_statement)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_field_access(self) -> list[Node]:
        query_str = """
        (field_access)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_class_declaration(self) -> list[Node]:
        query_str = """
        (class_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_class_declaration_cpp(self) -> list[Node]:
        query_str = """
        (class_specifier)@name
        """
        return self.query_by_capture_name(query_str, "name")
        
    def get_package_declaration_java(self) -> list[Node]:
        query_str = """
        (package_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_package_declaration_cpp(self) -> list[Node]:
        query_str = """
        (preproc_include)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_import_declaration(self) -> list[Node]:
        query_str = """
        (import_declaration)@name
        """
        return self.query_by_capture_name(query_str, "name")

    def get_root(self):
        return self.root
    
    def get_enhanced_for_statment(self) -> list[Node]:
        query_str = """
        (enhanced_for_statement)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def get_all_lambda_expression(self) -> list[Node]:
        query_str = """
        (lambda_expression)@body
        """
        return self.query_by_capture_name(query_str, "body")

    def get_all_methods_c_cpp(self) -> list[Node]:
        query_str = """
        (function_definition)@name
        """
        return self.query_by_capture_name(query_str, "name")
    
    def find_first_param_use(self, function_name: str, params: List[str]) -> Dict[str, Optional[int]]:
        
        result = {param: None for param in params}

        if self.LANGUAGE == Language(tscpp.language()) or self.LANGUAGE == Language(tsc.language()):
            func_query = f"""
            (function_definition
                declarator: (function_declarator
                    (identifier)@name
                    (
                body: (compound_statement)@body)
            """
        else:  
            func_query = f"""
            (method_declaration
                name: (identifier)@name
                (
                body: (block)@body)
            """

        func_nodes = self.query_by_capture_name(func_query, "body")
        if not func_nodes:
            return result  

        func_body = func_nodes[0]  
        id_query = """
        (identifier)@id
        """
        identifiers = self.query_by_capture_name(id_query, "id", node=func_body)

        for param in params:
            for id_node in identifiers:
                if id_node.text.decode("utf-8") == param:
                    line_number = id_node.start_point[0] + 1
                    if result[param] is None or line_number < result[param]:
                        result[param] = line_number

        return result
    
    @staticmethod
    def _iter_nodes(root: Node):
        stack = [root]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def _all_java_object_name(self) -> set[str]:
        ids = set()
        for n in self._iter_nodes(self.root):
            if n.type == "method_invocation" or n.type == "field_access":
                obj_node = n.child_by_field_name("object")
                while obj_node and not obj_node.type == "identifier":
                    obj_node = obj_node.child_by_field_name("object")
                if obj_node and obj_node.type == "identifier":
                    ids.add(obj_node.text.decode("utf-8"))
        return ids
    
    def _all_cpp_object_name(self) -> set[str]:
        ids = set()
        for n in self._iter_nodes(self.root):
            if n.type == "call_expression":
                obj_node = n.child_by_field_name("function")
                while obj_node and not obj_node.type == "identifier":
                    obj_node = obj_node.child_by_field_name("function")
                if obj_node and obj_node.type == "identifier":
                    ids.add(obj_node.text.decode("utf-8"))
        return ids

    def _all_type_name(self, root: Node) -> set[str]:
        ids = set()
        for n in self._iter_nodes(root):
            if n.type == "type_identifier":
                ids.add(n.text.decode("utf-8"))
        return ids

    def _all_identifier_texts(self, root: Node) -> list[str]:
        ids = []
        for n in self._iter_nodes(root):
            if n.type == "identifier":
                ids.append(n.text.decode("utf-8"))
        return ids

    def extract_variables(self) -> list[str]:
        identifiers = self._all_identifier_texts(self.root)

        callee_names: set[str] = set()
        if self.language == common.Language.JAVA:
            call_nodes = self.get_all_call_node_java()
            for node in call_nodes:
                name_node = node.child_by_field_name("name")
                if name_node is None:
                    continue
                if name_node.type == "identifier" and name_node.text is not None:
                    callee_names.add(name_node.text.decode("utf-8"))
                elif name_node.type == "scoped_identifier":
                    terminal = name_node.child_by_field_name("name")
                    if terminal and terminal.text is not None:
                        callee_names.add(terminal.text.decode("utf-8"))
        else:
            call_nodes = self.get_all_call_node()
            for node in call_nodes:
                func_node = node.child_by_field_name("function")
                if func_node and func_node.type == "identifier" and func_node.text is not None:
                    callee_names.add(func_node.text.decode("utf-8"))

        filtered_types: set[str] = set()
        try:
            filtered_types.update(self._all_type_name(self.root))
        except Exception:
            pass
        try:
            filtered_types.update(self._object_creation_expression_texts(self.root))
        except Exception:
            pass

        variables: list[str] = []
        seen: set[str] = set()
        for identifier in identifiers:
            if identifier in callee_names:
                continue
            if identifier in filtered_types:
                continue
            if identifier in {"this", "super"}:
                continue
            if identifier not in seen:
                seen.add(identifier)
                variables.append(identifier)

        return variables

    def _full_this_field_access(self, n: Node) -> Optional[str]:
        if n.type != "field_access":
            return None

        fields = []
        cur = n
        base_is_this = False

        
        while cur and cur.type == "field_access":
            
            fld = cur.child_by_field_name("field") or cur.child_by_field_name("name")
            if not fld or fld.type != "identifier":
                return None
            fields.append(fld.text.decode("utf-8"))

            obj = cur.child_by_field_name("object")
            if obj is None:
                return None
            if obj.type == "this":
                base_is_this = True
                break
            elif obj.type == "field_access":
                cur = obj
                continue
            else:
                
                return None

        if not base_is_this:
            return None

        fields.reverse()  
        return "this." + ".".join(fields)

    def _all_rhs_identifiers_with_this(self, root: Node) -> set[str]:
        ids = set()
        this_chain_ids = set()   
        bare_to_remove = set()   

        for n in self._iter_nodes(root):
            if n.type == "identifier":
                ids.add(n.text.decode("utf-8"))
            elif n.type == "field_access":
                full = self._full_this_field_access(n)
                if full:
                    this_chain_ids.add(full)
                    
                    
                    parts = full.split(".")[1:]  
                    bare_to_remove.update(parts)

        
        ids.difference_update(bare_to_remove)
        ids.update(this_chain_ids)
        return ids

    def _callee_identifier_texts(self, node: Node):
        callee = []

        
        def iter_callee_identifiers(node: Node):
            stack = [node]
            while stack:
                n = stack.pop()
                
                if n.type == "field_access" or n.type == "method_invocation":
                    ids = self._all_identifier_texts(n)
                    callee.extend(ids)
                    continue
                
                
                stack.extend(reversed(n.children))

        
        iter_callee_identifiers(node)
        
        return callee

    def _callee_names(self, root: Node) -> set[str]:
        callees = set()
        for n in self._iter_nodes(root):
            if n.type == "method_invocation":
                name_node = n.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    callees.add(name_node.text.decode("utf-8"))
        return callees
    
    def object_callee_name_dict(self, root: Node) -> dict:
        object_callee_name_dict = {}
        for n in self._iter_nodes(root):
            if n.type == "method_invocation":
                name_node = n.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    name = name_node.text.decode("utf-8")
                    obj_node = n.child_by_field_name("object")
                    while obj_node and not obj_node.type == "identifier":
                        obj_node = obj_node.child_by_field_name("object")
                    if obj_node and obj_node.type == "identifier":
                        object_name = obj_node.text.decode("utf-8")
                        object_callee_name_dict[name] = object_name
        return object_callee_name_dict

    def _object_creation_expression_texts(self, root: Node):
        object_creation_expression = []
        for n in self._iter_nodes(root):
            if n.type == "object_creation_expression":
                type_node = n.child_by_field_name("type")
                if type_node and type_node.type == "type_identifier":
                    object_creation_expression.append(type_node.text.decode("utf-8"))
        return object_creation_expression
    
    def _all_variables(self):
        identifiers = set()  

        
        def iter_identifiers(node: Node):
            stack = [node]
            while stack:
                n = stack.pop()
                
                if n.type == "field_access" or n.type == "method_invocation":
                    obj_node = n.child_by_field_name("object")
                    args_node = n.child_by_field_name("arguments")
                    if obj_node:
                        stack.append(obj_node)
                    if args_node:
                        stack.append(args_node)
                    continue
                    
                
                if n.type == "marker_annotation":
                    continue
                
                
                if n.type == "identifier":
                    identifiers.add(n.text.decode("utf-8"))
                
                
                stack.extend(reversed(n.children))

        
        iter_identifiers(self.root)
        
        return identifiers

    def _all_variables_with_this(self, root: Node):
        identifiers = set()

        
        def iter_identifiers(node: Node):
            stack = [node]
            while stack:
                n = stack.pop()
                
                if n.type == "field_access" or n.type == "method_invocation":
                    pre_node = n
                    obj_node = n.child_by_field_name("object")
                    while obj_node and not (obj_node.type == "identifier" or obj_node.type == "this"):
                        pre_node = obj_node
                        obj_node = obj_node.child_by_field_name("object")
                    if obj_node and obj_node.type == "identifier":
                        identifiers.add(obj_node.text.decode("utf-8"))
                    if obj_node and obj_node.type == "this":
                        identifiers.add(pre_node.text.decode("utf-8"))
                    continue
                    
                
                if n.type == "marker_annotation":
                    continue
                
                
                if n.type == "identifier":
                    identifiers.add(n.text.decode("utf-8"))
                
                
                stack.extend(reversed(n.children))

        
        iter_identifiers(root)
        
        return identifiers

    def _all_field_declaration(self, root: Node) -> list[Node]:
        fields = []
        def iter_callee_identifiers(node: Node):
            stack = [node]
            while stack:
                n = stack.pop()
                
                if n.type == "field_declaration":
                    fields.append(n)
                    continue
                if n.type == "class_declaration":
                    continue
                stack.extend(reversed(n.children))
        iter_callee_identifiers(root)
        return fields


def extract_imports(code: str):
    imports = set()
    ast_parser = ASTParser(code, common.Language.JAVA)
    for node in ast_parser.get_all_includes():
        imports.add(node.text.decode("utf-8"))
    return imports
