from dataclasses import dataclass
from typing import Optional


@dataclass(eq=False, kw_only=True)
class NODE:
    id: int

    @property
    def type(self):
        return self.__class__.__name__

    def __hash__(self) -> int:
        return self.id

    def to_dict(self):
        return self.__dict__


@dataclass(eq=False, kw_only=True)
class META_DATA(NODE):
    language: str
    overlays: str
    root: str
    version: str
    hash: str | None = None

    def __hash__(self) -> int:
        return self.id


@dataclass(eq=False, kw_only=True)
class AST_NODE(NODE):
    code: str
    order: int
    column_number: Optional[int] = None
    line_number: int | None = None


@dataclass(eq=False, kw_only=True)
class CFG_NODE(AST_NODE, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class DECLARATION(NODE):
    name: str


@dataclass(eq=False, kw_only=True)
class FILE(AST_NODE, NODE):
    name: str
    hash: str | None = None


@dataclass(eq=False, kw_only=True)
class NAMESPACE(AST_NODE, NODE):
    name: str


@dataclass(eq=False, kw_only=True)
class NAMESPACE_BLOCK(AST_NODE, NODE):
    filename: str
    full_name: str
    name: str


@dataclass(eq=False, kw_only=True)
class EXPRESSION(CFG_NODE, NODE):
    argument_index: int = -1
    argument_name: Optional[str] = None


@dataclass(eq=False, kw_only=True)
class BLOCK(EXPRESSION, NODE):
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class CALL_REPR(CFG_NODE, NODE):
    name: str
    signature: str | None = None


@dataclass(eq=False, kw_only=True)
class CALL(CALL_REPR, EXPRESSION, NODE):
    dispatch_type: str
    method_full_name: str
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class CONTROL_STRUCTURE(EXPRESSION, NODE):
    control_structure_type: str
    parser_type_name: str


@dataclass(eq=False, kw_only=True)
class FIELD_IDENTIFIER(EXPRESSION, NODE):
    canonical_name: str


@dataclass(eq=False, kw_only=True)
class IDENTIFIER(EXPRESSION, NODE):
    name: str
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class JUMP_LABEL(AST_NODE, NODE):
    name: str
    parser_type_name: str


@dataclass(eq=False, kw_only=True)
class JUMP_TARGET(CFG_NODE, NODE):
    argument_index: int
    name: str
    parser_type_name: str


@dataclass(eq=False, kw_only=True)
class LITERAL(EXPRESSION, NODE):
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class LOCAL(EXPRESSION, NODE):
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class METHOD_REF(EXPRESSION, NODE):
    method_full_name: str
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class MODIFIER(AST_NODE, NODE):
    modifier_type: str


@dataclass(eq=False, kw_only=True)
class RETURN(EXPRESSION, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class TYPE_REF(EXPRESSION, NODE):
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class UNKNOWN(EXPRESSION, NODE):
    contained_ref: str
    parser_type_name: str
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class COMMENT(AST_NODE, NODE):
    filename: str


@dataclass(eq=False, kw_only=True)
class CONFIG_FILE(NODE):
    content: str
    name: str


@dataclass(eq=False, kw_only=True)
class BINDING(NODE):
    method_full_name: str
    name: str
    signature: str


@dataclass(eq=False, kw_only=True)
class METHOD(EXPRESSION, NODE):
    ast_parent_full_name: str
    ast_parent_type: str
    filename: str
    full_name: str
    is_external: bool
    signature: str | None = None
    line_number_end: int | None = None
    column_number_end: int | None = None
    hash: str | None = None


@dataclass(eq=False, kw_only=True)
class METHOD_PARAMETER_IN(CFG_NODE, DECLARATION, NODE):
    evaluation_strategy: str
    index: int
    is_variadic: bool
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class METHOD_PARAMETER_OUT(CFG_NODE, DECLARATION, NODE):
    evaluation_strategy: str
    index: int
    is_variadic: bool
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class METHOD_RETURN(CFG_NODE, NODE):
    evaluation_strategy: str
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class MEMBER(AST_NODE, DECLARATION, NODE):
    type_full_name: str


@dataclass(eq=False, kw_only=True)
class TYPE(NODE):
    full_name: str
    name: str
    type_decl_full_name: str


@dataclass(eq=False, kw_only=True)
class TYPE_ARGUMENT(AST_NODE, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class TYPE_DECL(AST_NODE, NODE):
    ast_parent_full_name: str
    ast_parent_type: str
    filename: str
    full_name: str
    is_external: bool
    name: str
    alias_type_full_name: str | None = None
    inherits_from_type_full_name: str | None = None


@dataclass(eq=False, kw_only=True)
class TYPE_PARAMETER(AST_NODE, NODE):
    name: str


@dataclass(eq=False, kw_only=True)
class ANNOTATION(EXPRESSION, NODE):
    full_name: str
    name: str


@dataclass(eq=False, kw_only=True)
class ANNOTATION_LITERAL(EXPRESSION, NODE):
    name: str


@dataclass(eq=False, kw_only=True)
class ANNOTATION_PARAMETER(AST_NODE, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class ANNOTATION_PARAMETER_ASSIGN(AST_NODE, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class ARRAY_INITIALIZER(EXPRESSION, NODE):
    pass


@dataclass(eq=False, kw_only=True)
class IMPORT(NODE):
    code: str
    order: int
    imported_entity: str
    imported_as: str