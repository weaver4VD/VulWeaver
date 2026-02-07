import os
import re
import subprocess
import tempfile

from . import ast_parser
from . import config
from .ast_parser import ASTParser
from .common import Language
from tree_sitter import Node

encoding_format = "ISO-8859-1"


def del_comment(file_contents, language: Language):
    parser = ASTParser(file_contents, language)
    if language == Language.JAVA:
        nodes = parser.query_all(ast_parser.TS_JAVA_COMMENT)
    elif language == Language.CPP:
        nodes = parser.query_all(ast_parser.TS_CPP_COMMENT)
    nodes = [node for node in nodes]
    all_comment = set()
    for node in nodes:
        if node.text.decode().strip() == "//":
            continue
        all_comment.add(node.text.decode())
    for comment in all_comment:
        file_contents = file_contents.replace(comment, "")
    
    file_contents = file_contents.replace("//", "")
    return file_contents

def get_comment(code, language: Language):
    parser = ASTParser(code, language)
    if language == Language.JAVA:
        nodes = parser.query_all(ast_parser.TS_JAVA_COMMENT)
    elif language == Language.CPP:
        nodes = parser.query_all(ast_parser.TS_CPP_COMMENT)
    nodes = [node for node in nodes]
    all_comment = set()
    for node in nodes:
        if node.text.decode().strip() == "//":
            continue
        all_comment.add(node.text.decode())
    
    return all_comment

def add_bracket(code: str, language: Language):
    code_bytes = code.encode()
    parser = ASTParser(code, language)
    nodes = parser.query_all(ast_parser.TS_COND_STAT)
    nodes = [node for node in nodes]
    need_modified_bytes = []
    for node in nodes:
        consequence_node = node.child_by_field_name("consequence")
        if consequence_node is None:
            continue
        if consequence_node.type != "compound_statement":
            if (
                consequence_node.start_byte,
                consequence_node.end_byte,
            ) not in need_modified_bytes:
                need_modified_bytes.append(
                    (consequence_node.start_byte, consequence_node.end_byte)
                )
        alternative_node = node.child_by_field_name("alternative")
        if alternative_node is None:
            continue
        alternative_node = alternative_node.named_child(0)
        if (
            alternative_node is not None
            and alternative_node.type != "compound_statement"
            and alternative_node.type != "if_statement"
        ):
            if (
                alternative_node.start_byte,
                alternative_node.end_byte,
            ) not in need_modified_bytes:
                st = alternative_node.start_byte
                ed = alternative_node.end_byte
                need_modified_bytes.append(
                    (alternative_node.start_byte, alternative_node.end_byte)
                )
    need_modified_bytes = sorted(need_modified_bytes)
    i = 0
    while i < len(need_modified_bytes):
        st, ed = need_modified_bytes[i]
        if ed - st <= 1:
            i += 1
            continue
        code_bytes = (
            code_bytes[:st]
            + b"{\n"
            + code_bytes[st : ed + 1]
            + b"}\n"
            + code_bytes[ed + 1 :]
        )
        j = i + 1
        while j < len(need_modified_bytes):
            st_next, ed_next = need_modified_bytes[j]
            if st_next >= st and st_next <= ed:
                st_next += 2
            else:
                st_next += 4
            if ed_next >= st and ed_next <= ed:
                ed_next += 2
            else:
                ed_next += 4
            need_modified_bytes[j] = (st_next, ed_next)
            j += 1
        i += 1
    return code_bytes.decode()


def del_lineBreak_C(code):
    comments = get_comment(code, Language.C)
    comment_map = {}
    cnt = 0
    for comment in comments:
        repl = f"__COMMENT__{cnt};"
        code = code.replace(comment, repl)
        comment_map[repl] = comment
        cnt += 1
    lines = code.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].endswith("\\"):
            temp = i
            while lines[i].endswith("\\"):
                i += 1
            lines[temp] = lines[temp].strip()
            for k in range(temp + 1, i + 1):
                if k == len(lines):
                    break
                lines[temp] += " "
                lines[temp] += lines[k].strip()
                lines[k] = "\n"
        else:
            i += 1
    i = 0
    while i < len(lines):
        if lines[i].strip() == "" or lines[i].strip().startswith("#"):
            i += 1
        else:
            temp = i
            while (
                i < len(lines)
                and not lines[i].strip().endswith(";")
                and not lines[i].strip().endswith("{")
                and not lines[i].strip().endswith(")")
                and not lines[i].strip().endswith("}")
                and not lines[i].strip().endswith(":")
                and not lines[i].strip().startswith("#")
            ):
                i += 1
            while i < len(lines) - 1 and (
                lines[i + 1].strip().startswith("?")
                or lines[i + 1].strip().startswith("||")
                or lines[i + 1].strip().startswith("&&")
            ):
                i += 1
            if i < len(lines) and lines[i].strip().startswith("#"):
                i -= 1
            if temp != i:
                lines[temp] = lines[temp]
            for j in range(temp + 1, i + 1):
                if j == len(lines):
                    break
                lines[temp] += " "
                lines[temp] += lines[j].strip()
                lines[j] = ""
            if temp == i:
                i += 1
    code = "\n".join(lines)
    for repl in comment_map.keys():
        code = code.replace(repl, comment_map[repl])
    return code


def del_macros(code):
    lines = code.split("\n")
    removed_macros = {
        "R_API",
        "INLINE",
        "TRIO_PRIVATE_STRING",
        "GF_EXPORT",
        "LOCAL",
        "IN",
        "OUT",
        "_U_",
        "EFIAPI",
        "UNUSED_PARAM",
        "__declspec(dllexport) mrb_value",
        'extern "C"',
        "__rte_always_inline",
        "__init",
        "__user",
        "UNUSED",
        "noinline",
        "static",
        "__attribute__(())",
        "SK_RESTRICT"
    }
    i = 0
    while i < len(lines):
        if lines[i].endswith("\\"):
            temp = i
            while lines[i].endswith("\\"):
                i += 1
            lines[temp] = lines[temp][:-1]
            for k in range(temp + 1, i + 1):
                if k == len(lines):
                    break
                lines[temp] += " "
                if k != i:
                    lines[temp] += lines[k][:-1].strip()
                else:
                    lines[temp] += lines[k].strip()
                lines[k] = "\n"
        else:
            i += 1
    i = 0
    while i < len(lines):
        if (
            lines[i].startswith("#ifdef")
            or lines[i].startswith("#else")
            or lines[i].startswith("#endif")
            or lines[i].startswith("#if")
            or lines[i].startswith("#elif")
        ):
            if lines[i].startswith("#else") or lines[i].startswith("#elif"):
                j = i
                while not lines[j].startswith("#endif"):
                    lines[j] = ""
                    j += 1
                i = j
            lines[i] = ""
        i += 1

    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("#") and not lines[i].strip().startswith(
            "#include"
        ):
            lines[i] = ""
        for rmv_macro in removed_macros:
            lines[i] = lines[i].replace(rmv_macro, "")
        lines[i] = (
            lines[i]
            .replace("METHODDEF(void)", "void")
            .replace("METHODDEF(JDIMENSION)", "int")
            .replace("= nullptr)", ")")
            .replace("auto codec = SkAndroidCodec::MakeFromData(bytes);", "SkAndroidCodec codec = SkAndroidCodec::MakeFromData(bytes);")
        )
        i += 1
    return "\n".join(lines)


def format_and_del_comment_c_cpp(code, del_macro=True, del_comments=True):
    code = (
        subprocess.run(
            [
                "astyle",
                "--style=java",
                "--squeeze-ws",
                "--keep-one-line-statements",
                "--max-code-length=200",
                "--delete-empty-lines",
            ],
            input=code.encode(),
            stdout=subprocess.PIPE,
        )
        .stdout.decode()
        .strip()
    )
    if del_comments:
        code = del_comment(code, Language.CPP)
    if del_macro:
        code = del_macros(code)
    code = del_lineBreak_C(code)
    code = remove_empty_lines(code)
    code = (
        subprocess.run(
            [
                "astyle",
                "--style=java",
                "--squeeze-ws",
                "--keep-one-line-statements",
                "--max-code-length=200",
                "--delete-empty-lines",
            ],
            input=code.encode(),
            stdout=subprocess.PIPE,
        )
        .stdout.decode()
        .strip()
    )
    return code

def remove_empty_lines(string) -> str:
    return re.sub(r"^\s*$\n", "", string, flags=re.MULTILINE)


def remove_spaces(string):
    return re.sub(r"\s+", "", string)


def normalize(code: str, del_comments: bool = True) -> str:
    if del_comments:
        code = del_comment(code)
    code = del_lineBreak_C(code)
    code = remove_spaces(code)
    return code.strip()

def del_lineBreak_Java(code: str):
    comments = get_comment(code, Language.JAVA)
    comment_map = {}
    cnt = 0
    for comment in comments:
        repl = f"__COMMENT__{cnt};"
        code = code.replace(comment, repl)
        comment_map[repl] = comment
        cnt += 1
    code = code.replace("//\n", "")
    lines = code.split("\n")
    i = 0
    while i < len(lines):
        if (
            lines[i].strip() == ""
            or lines[i].strip().startswith("@")
        ):
            i += 1
        else:
            temp = i
            while (
                i < len(lines)
                and not lines[i].strip().endswith(";")
                and not lines[i].strip().endswith("{")
                and not lines[i].strip().endswith(")")
                and not lines[i].strip().endswith("}")
                and not lines[i].strip().endswith(":")
                and not lines[i].strip().startswith("@")
            ):
                i += 1
            while i < len(lines) - 1 and (lines[i + 1].strip().startswith("?") or lines[i + 1].strip().startswith("||") or lines[i + 1].strip().startswith("&&") or lines[i + 1].strip().startswith(".")):
                i += 1
            if i < len(lines) and lines[i].strip().startswith("@"):
                i -= 1
            if temp == i:
                i += 1
                continue
            if temp > len(lines):
                print(lines)
                print(temp)
            for j in range(temp + 1, i + 1):
                lines[temp] += " "
                lines[temp] += lines[j].strip()
                lines[j] = ""
    
    code = "\n".join(lines)
    for repl in comment_map.keys():
        code = code.replace(repl, comment_map[repl])
    
    code = code.replace("import lambok.Getter;", "").replace("@Getter", "").replace("@Setter", "").replace("@Data", "").replace("@AllArgsConstructor", "").replace("@NoArgsConstructor", "").replace("@Builder", "").replace("import lambok.Setter;", "").replace("import lombok.*", "")


    return code


def addBracket(src):
    f = open(src, "r")
    lines = f.readlines()
    i = 0
    relines = ""
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.replace(" ", "").endswith(";\n"):
            relines += line
        elif (
            line.lstrip().startswith("if ")
            or line.lstrip().startswith("for ")
            or (
                line.strip().startswith("else")
                and not line.lstrip().startswith("else if")
            )
            or line.lstrip().startswith("while ")
            or line.lstrip().startswith("try ")
            or line.lstrip().startswith("catch ")
            or line.lstrip().startswith("else if")
            or line.lstrip().startswith("switch ")
        ) and line.replace(" ", "").rstrip().endswith("}"):
            k = line.find("{")
            temp = line[0 : k + 1] + "\n"
            line = line[k + 1 :]
            st = 0
            left = 1
            while left > 0 and st < len(line):
                if line[st] == "{":
                    left += 1
                    temp += line[0 : st + 1] + "\n"
                    line = line[st + 1 :]
                    st = -1
                elif line[st] == "}":
                    left -= 1
                    temp += line[0:st] + "\n}\n"
                    line = line[st + 1 :]
                    st = -1
                st += 1
            if not (left <= 0 and st >= len(line)):
                relines += temp + line
            else:
                relines += temp
        elif (
            (
                line.lstrip().startswith("if ")
                or line.lstrip().startswith("for ")
                or (
                    line.strip().startswith("else")
                    and not line.lstrip().startswith("else if")
                )
                or line.lstrip().startswith("while ")
                or line.lstrip().startswith("try ")
                or line.lstrip().startswith("catch ")
                or line.lstrip().startswith("else if")
                or line.lstrip().startswith("switch")
            )
            and not line.replace(" ", "").rstrip().endswith("{")
            and not line.replace(" ", "").rstrip().endswith(";")
        ):
            first = True
            temp = ""
            left = 1
            before = ""
            while (
                (
                    line.lstrip().startswith("if ")
                    or line.lstrip().startswith("for ")
                    or (
                        line.strip().startswith("else")
                        and not line.lstrip().startswith("else if")
                    )
                    or line.lstrip().startswith("while ")
                    or line.lstrip().startswith("try ")
                    or line.lstrip().startswith("catch ")
                    or line.lstrip().startswith("else if")
                    or line.lstrip().startswith("switch")
                )
                and not line.replace(" ", "").rstrip().endswith("{")
                and not line.replace(" ", "").rstrip().endswith(";")
            ):
                if first:
                    temp = line[0:-1] + "{\n"
                else:
                    j = i - 1
                    while j >= 0 and lines[j].replace(" ", "") == "\n":
                        j -= 1
                    i += 1
                    if (
                        line.strip().startswith("else")
                        and not line.lstrip().startswith("else if")
                        and before == "else"
                    ):
                        temp += "}\n" + line[0:-1] + "{\n"
                    elif before == "else" and left != 0:
                        temp += "}\n" + line[0:-1] + "{\n"
                    elif lines[j].replace(" ", "").strip() == "}":
                        temp += "}\n" + line[0:-1] + "{\n"
                    else:
                        temp += line[0:-1] + "{\n"
                        left += 1
                if line.lstrip().startswith("if "):
                    before = "if"
                elif line.lstrip().startswith("for "):
                    before = "for"
                elif line.strip().startswith("else") and not line.lstrip().startswith(
                    "else if"
                ):
                    before = "else"
                elif line.lstrip().startswith("while "):
                    before = "while"
                elif line.lstrip().startswith("try "):
                    before = "try"
                elif line.lstrip().startswith("catch "):
                    before = "catch"
                elif line.lstrip().startswith("else if"):
                    before = "else if"
                elif line.lstrip().startswith("switch"):
                    before = "switch"
                while (
                    lines[i].lstrip().startswith("if ")
                    or lines[i].lstrip().startswith("if(")
                    or lines[i].lstrip().startswith("for ")
                    or (
                        lines[i].strip().startswith("else")
                        and not lines[i].lstrip().startswith("else if")
                    )
                    or lines[i].lstrip().startswith("while ")
                    or lines[i].lstrip().startswith("try ")
                    or lines[i].lstrip().startswith("catch ")
                    or lines[i].lstrip().startswith("else if")
                    or lines[i].lstrip().startswith("switch ")
                ) and not (
                    lines[i].replace(" ", "").rstrip().endswith("{")
                    or lines[i].replace(" ", "").rstrip().endswith(";")
                ):
                    if lines[i].strip().startswith("else") and (
                        before == "for" or before == "while"
                    ):
                        temp += "}\n" + lines[i][:-1] + "{\n"
                        i += 1
                        before = "else"
                    elif lines[i].replace(" ", "").rstrip().endswith("}"):
                        k = lines[i].find("{")
                        temp1 = lines[i][0 : k + 1] + "\n"
                        lines[i] = lines[i][k + 1 :]
                        st = 0
                        left1 = 1
                        while left1 > 0 and st < len(lines[i]):
                            if lines[i][st] == "{":
                                left1 += 1
                                temp1 += lines[i][0 : st + 1] + "\n"
                                lines[i] = lines[i][st + 1 :]
                                st = -1
                            elif lines[i][st] == "}":
                                left1 -= 1
                                temp1 += lines[i][0:st] + "\n}\n"
                                lines[i] = lines[i][st + 1 :]
                                st = -1
                            st += 1
                        if not (left1 <= 0 and st >= len(lines[i])):
                            temp += temp1 + lines[i]
                        else:
                            temp += temp1
                    else:
                        temp += lines[i][:-1] + "{\n"
                        left += 1
                        if line.lstrip().startswith("if "):
                            before = "if"
                        elif line.lstrip().startswith("for "):
                            before = "for"
                        elif line.strip().startswith(
                            "else"
                        ) and not line.lstrip().startswith("else if"):
                            before = "else"
                        elif line.lstrip().startswith("while "):
                            before = "while"
                        elif line.lstrip().startswith("try "):
                            before = "try"
                        elif line.lstrip().startswith("catch "):
                            before = "catch"
                        elif line.lstrip().startswith("else if"):
                            before = "else if"
                        elif line.lstrip().startswith("switch"):
                            before = "switch"
                        i += 1
                fl = True
                if (
                    lines[i].lstrip().startswith("if ")
                    or lines[i].lstrip().startswith("if(")
                    or lines[i].lstrip().startswith("for ")
                    or (
                        lines[i].strip().startswith("else")
                        and not lines[i].lstrip().startswith("else if")
                    )
                    or lines[i].lstrip().startswith("while ")
                    or lines[i].lstrip().startswith("try ")
                    or lines[i].lstrip().startswith("catch ")
                    or lines[i].lstrip().startswith("else if")
                    or lines[i].lstrip().startswith("switch ")
                ) and lines[i].replace(" ", "").rstrip().endswith("{"):
                    while (
                        lines[i].lstrip().startswith("if ")
                        or lines[i].lstrip().startswith("if(")
                        or lines[i].lstrip().startswith("for ")
                        or (
                            lines[i].strip().startswith("else")
                            and not lines[i].lstrip().startswith("else if")
                        )
                        or lines[i].lstrip().startswith("while ")
                        or lines[i].lstrip().startswith("try ")
                        or lines[i].lstrip().startswith("catch ")
                        or lines[i].lstrip().startswith("else if")
                        or lines[i].lstrip().startswith("switch ")
                    ) and lines[i].replace(" ", "").rstrip().endswith("{"):
                        temp += lines[i]
                        i += 1
                        left1 = 1
                        be = False
                        while left1 > 0 and i < len(lines):
                            if "{" in lines[i]:
                                k = lines[i].find("{")
                                temp1 = lines[i][0 : k + 1] + "\n"
                                lines[i] = lines[i][k + 1 :]
                                st = 0
                                left1 += 1
                                while left1 > 0 and st < len(lines[i]):
                                    if lines[i][st] == "{":
                                        left1 += 1
                                        temp1 += lines[i][0 : st + 1] + "\n"
                                        lines[i] = lines[i][st + 1 :]
                                        st = -1
                                    elif lines[i][st] == "}":
                                        left1 -= 1
                                        temp1 += lines[i][0:st] + "\n}\n"
                                        lines[i] = lines[i][st + 1 :]
                                        st = -1
                                    st += 1
                                if not (left1 <= 0 and st >= len(lines[i])):
                                    temp += temp1 + lines[i]
                                else:
                                    temp += temp1
                                i += 1
                            elif lines[i].replace(" ", "").rstrip().endswith("}"):
                                left1 -= 1
                                temp += lines[i]
                                i += 1
                            elif (
                                lines[i].lstrip().startswith("if ")
                                or lines[i].lstrip().startswith("if(")
                                or lines[i].lstrip().startswith("for ")
                                or (
                                    lines[i].strip().startswith("else")
                                    and not lines[i].lstrip().startswith("else if")
                                )
                                or lines[i].lstrip().startswith("while ")
                                or lines[i].lstrip().startswith("try ")
                                or lines[i].lstrip().startswith("catch ")
                                or lines[i].lstrip().startswith("else if")
                                or lines[i].lstrip().startswith("switch ")
                            ) and not lines[i].replace(" ", "").rstrip().endswith("{"):
                                temp += lines[i][:-1] + "{\n"
                                left1 += 1
                                i += 1
                                be = True
                            elif be and not (
                                lines[i].lstrip().startswith("if ")
                                or lines[i].lstrip().startswith("if(")
                                or lines[i].lstrip().startswith("for ")
                                or (
                                    lines[i].strip().startswith("else")
                                    and not lines[i].lstrip().startswith("else if")
                                )
                                or lines[i].lstrip().startswith("while ")
                                or lines[i].lstrip().startswith("try ")
                                or lines[i].lstrip().startswith("catch ")
                                or lines[i].lstrip().startswith("else if")
                                or lines[i].lstrip().startswith("switch ")
                            ):
                                temp += lines[i] + "}\n"
                                be = False
                                i += 1
                                left1 -= 1
                            else:
                                temp += lines[i]
                                i += 1
                        while lines[i].replace(" ", "") == "\n":
                            temp += lines[i]
                            i += 1
                        while left1 != 0:
                            temp += "}\n"
                            left1 -= 1
                elif lines[i].rstrip().endswith("{"):
                    tmp = i
                    while i < len(lines) and not lines[i].rstrip().endswith("};"):
                        temp += lines[i]
                        i += 1
                    temp += lines[i]
                    i += 1
                elif not (
                    lines[i].lstrip().startswith("if ")
                    or lines[i].lstrip().startswith("if(")
                    or lines[i].lstrip().startswith("for ")
                    or (
                        lines[i].strip().startswith("else")
                        and not lines[i].lstrip().startswith("else if")
                    )
                    or lines[i].lstrip().startswith("while ")
                    or lines[i].lstrip().startswith("try ")
                    or lines[i].lstrip().startswith("catch ")
                    or lines[i].lstrip().startswith("else if")
                    or lines[i].lstrip().startswith("switch ")
                ):
                    temp += lines[i] + "}\n"
                    left -= 1
                    i += 1
                    fl = False
                line = lines[i]
                if line.lstrip().startswith("else") and left != 0 and fl:
                    temp += "}\n"
                    left -= 1
                first = False
            if left > 0:
                temp += "}\n"
                left -= 1

            if (
                not (
                    (
                        lines[i].lstrip().startswith("if ")
                        or lines[i].lstrip().startswith("if(")
                        or lines[i].lstrip().startswith("for ")
                        or (
                            lines[i].strip().startswith("else")
                            and not lines[i].lstrip().startswith("else if")
                        )
                        or lines[i].lstrip().startswith("while ")
                        or lines[i].lstrip().startswith("try ")
                        or lines[i].lstrip().startswith("catch ")
                        or lines[i].lstrip().startswith("else if")
                        or lines[i].lstrip().startswith("switch ")
                    )
                    and not (
                        lines[i].replace(" ", "").rstrip().endswith("{")
                        or lines[i].replace(" ", "").rstrip().endswith(";")
                    )
                )
                and left > 0
            ):
                temp += lines[i] + "}\n"
                i += 1
                left -= 1
            while left != 0:
                temp += "}\n"
                left -= 1
            relines += temp
        else:
            relines += line
    f.close()
    assertLoc = []
    lines = relines.split("\n")
    empty_line = []
    newContent = ""
    annotaionLines = 0
    for i in range(len(lines)):
        line = lines[i]
        if lines[i].strip() in ["{", "}", ""]:
            empty_line.append(i + 1 - annotaionLines)
        lineContent = line.strip().split(" ")
        if (
            len(lineContent) <= 1
            and line.strip().startswith("@")
            and not line.strip().endswith("{")
            and (
                lines[i + 1].strip().startswith("public")
                or lines[i + 1].strip().startswith("private")
                or lines[i + 1].strip().startswith("protected")
                or lines[i + 1].strip().startswith("@")
            )
        ):
            annotaionLines += 1
            continue
        elif line.strip() == "PendingIntent.getService }":
            newContent += "}\n"
            continue
        newContent += line + "\n"
    outputf = open(src, "w")
    outputf.write(newContent)
    outputf.close()
    return empty_line

def remove_comments(string):
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        if match.group(2) is not None:
            return ""
        else:
            return match.group(1)
    return regex.sub(_replacer, string)

def del_comment_java(file_contents):
    c_regex = re.compile(
        r'(?P<comment>//.*?$)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE,
    )
    file_contents = "".join(
        [
            c.group("noncomment")
            for c in c_regex.finditer(file_contents)
            if c.group("noncomment")
        ]
    )
    return file_contents

def format_lambda_java(code: str):
    parser = ASTParser(code, Language.JAVA)
    lambda_nodes = parser.get_all_lambda_expression()
    idx = 0
    while idx < len(lambda_nodes):
        code = format_lambda_java_for_each(code, idx)
        idx += 1
    return code

def format_lambda_java_for_each(code: str, idx: int):
    parser = ASTParser(code, Language.JAVA)
    lambda_nodes = parser.get_all_lambda_expression()
    if not lambda_nodes:
        return code

    original_bytes = code.encode("utf-8")
    edits: list[tuple[str, str, str]] = []

    def body_span_with_brackets(node):
        start = node.start_byte
        end = node.end_byte
        if (
            end - start >= 2
            and original_bytes[start : start + 1] == b"{"
            and original_bytes[end - 1 : end] == b"}"
        ):
            return start, end, True
        return start, end, False

    def collect_replacement(body_text: str, param_node: Node, idx: int, var_dict: dict) -> str:
        replacement = ""
        new_lambda_method = ""
        body_text = body_text.strip()
        final_var_dict = {}
        tmp_var_dict = {}
        for var, modifiers_type in var_dict.items():
            modifiers_text, type_text = modifiers_type
            declaration = f"{modifiers_text} {type_text} {var}".strip()
            if "final" in modifiers_text:
                final_var_dict[var] = declaration
            else:
                tmp_var_dict[var] = declaration

        if param_node is None and not final_var_dict:
            return f"lambda{idx}()", f"private static Object lambda{idx}(){body_text}"


        param_name = ""
        param_declarations = []
        param_names = []
        for var_name, type_var_name in final_var_dict.items():
            param_declarations.append(type_var_name)
            param_names.append(var_name)
        if param_node.type == "identifier":
            param_name = param_node.text.decode("utf-8")
            if param_name in final_var_dict:
                pass
            elif param_name in tmp_var_dict:
                param_names.append(param_name)
                param_declarations.append(tmp_var_dict[param_name])
            else:
                param_names.append(param_name)
                param_declarations.append(f"Object {param_name}")
            
        elif param_node.type == "inferred_parameters":
            for child in param_node.named_children:
                if child.type == "identifier":
                    param_name = child.text.decode("utf-8")
                    param_names.append(param_name)
                    if param_name in final_var_dict:
                        param_declarations.append(final_var_dict[param_name])
                    elif param_name in tmp_var_dict:
                        param_declarations.append(tmp_var_dict[param_name])
                    else:
                        param_declarations.append(f"Object {param_name}")

        elif param_node.type == "formal_parameters":
            for child in param_node.named_children:
                if child.type == "formal_parameter":
                    type_node = child.child_by_field_name("type")
                    name_node = child.child_by_field_name("name")
                    if type_node and name_node:
                        type_text = type_node.text.decode("utf-8")
                        name_text = name_node.text.decode("utf-8")
                        param_declarations.append(f"{type_text} {name_text}")
                        param_names.append(name_text)

        replacement = f"({', '.join(param_names)})"
        new_lambda_method = f"({', '.join(param_declarations)}){body_text}"

        return f"lambda{idx}{replacement}", f"private static Object lambda{idx}{new_lambda_method}"


    for lambda_node in lambda_nodes:
        lambda_text = lambda_node.text.decode("utf-8")
        param_node = None
        for param_child in lambda_node.named_children:
            if param_child.type == "inferred_parameters" or param_child.type == "identifier" or param_child.type == "formal_parameters":
                param_node = param_child
        body_node = lambda_node.child_by_field_name("body")
        if body_node is None:
            if lambda_node.named_children:
                body_node = lambda_node.named_children[-1]
            else:
                return code
        body_start, body_end, has_brackets = body_span_with_brackets(body_node)
        if body_start >= body_end:
            return code

        lambda_bytes = original_bytes[
            lambda_node.start_byte : lambda_node.end_byte
        ].decode("utf-8")
        has_trailing_newline = lambda_bytes.endswith("\n")

        method_node = lambda_node.parent
        while method_node is not None and method_node.type != "method_declaration":
            method_node = method_node.parent
        def DFS_variable_modifiers_type_dict(node: Node, lambda_node: Node, var_dict: dict):
            if node == None or node == lambda_node:
                return
            if node.type == "formal_parameter":
                modifier_text = ""
                for child in node.named_children:
                    if child != None and child.type == "modifiers":
                        modifier_text = child.text.decode("utf-8")
                        break
                type_text = node.child_by_field_name("type").text.decode("utf-8")
                var_dict[node.child_by_field_name("name").text.decode("utf-8")] = (modifier_text, type_text)
            if node.type == "local_variable_declaration":
                modifier_text = ""
                for child in node.named_children:
                    if child != None and child.type == "modifiers":
                        modifier_text = child.text.decode("utf-8")
                        break
                type_text = node.child_by_field_name("type").text.decode("utf-8")
                var_dict[node.child_by_field_name("declarator").child_by_field_name("name").text.decode("utf-8")] = (modifier_text, type_text)
            for child in node.children:
                DFS_variable_modifiers_type_dict(child, lambda_node, var_dict)
        var_dict = {}
        DFS_variable_modifiers_type_dict(method_node, lambda_node, var_dict)

        if has_brackets:
            body_text = original_bytes[body_start:body_end].decode("utf-8")
            replacement, new_lambda_method = collect_replacement(body_text, param_node, idx, var_dict)
        else:
            body_text = f'''{{
            {original_bytes[
                body_node.start_byte : body_node.end_byte
            ].decode("utf-8")}
            }}
            '''
            replacement, new_lambda_method = collect_replacement(body_text, param_node, idx, var_dict)
        if not replacement or not new_lambda_method:
            return code
        if has_trailing_newline and not replacement.endswith("\n"):
            replacement += "\n"

        class_node = lambda_node.parent
        while class_node is not None and class_node.type != "class_declaration":
            class_node = class_node.parent
        if class_node == None:
            return code
        if class_node.text.decode("utf-8").strip().endswith("}"):
            new_class_text = class_node.text.decode("utf-8").strip()[:-1] + new_lambda_method + "\n" + "}"
            code = code.replace(class_node.text.decode("utf-8"), new_class_text)
        code = code.replace(lambda_text, replacement)

        return code


    
def format_and_del_comment_java(code: str, format_lambda: bool):
    code = del_lineBreak_Java(code)
    code = remove_empty_lines(code)
    if format_lambda:
        code = format_lambda_java(code)
    return code