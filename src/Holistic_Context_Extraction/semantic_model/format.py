import os
import re
import cpu_heater

class CodeFile:
    def __init__(self, file_path: str, code: str, isformat: bool):
        self.file_path = file_path
        self.code = code
        if isformat:
                self.formated_code = format_and_del_comment_java(code)
        else:
            self.formated_code = code

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

def get_comment(code):
    c_regex = re.compile(
        r'(?P<comment>//.*?$)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE,
    )
    comment = [c.group("comment") for c in c_regex.finditer(code) if c.group("comment")]
    multilinecomment = [
        c.group("multilinecomment")
        for c in c_regex.finditer(code)
        if c.group("multilinecomment")
    ]
    all_comment = set()
    for comma in comment:
        all_comment.add(comma)
    for comma in multilinecomment:
        all_comment.add(comma)
    return all_comment

def del_lineBreak_Java(code: str):
    comments = get_comment(code)
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
    
    code = code.replace("import lambok.Getter;", "").replace("@Getter", "").replace("@Setter", "").replace("@Data", "").replace("@AllArgsConstructor", "").replace("@NoArgsConstructor", "").replace("@Builder", "").replace("import lambok.Setter;", "").replace("import lombok.*", "")

    return code


def remove_empty_lines(string) -> str:
    return re.sub(r"^\s*$\n", "", string, flags=re.MULTILINE)

def format_and_del_comment_java(code: str):
    code = del_comment_java(code)
    code = del_lineBreak_Java(code)
    code = remove_empty_lines(code)
    return code

def format(file_path, code_path):
    if not code_path.endswith("/"):
        code_path += "/"
    file_path = file_path.replace(code_path, "")


    content_files = {}
    for root, _, files in os.walk(code_path):
        for file in files:
            if file.endswith(".java"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", errors="replace") as f:
                        content = f.read()
                    path = path.replace(code_path, "")
                    content_files[path] = content
                except FileNotFoundError:
                    print(f"Error: File {path} not found")
                    continue
    
    codes = content_files[file_path]

    extracted_macros_codes = codes

    assert extracted_macros_codes is not None
    source_code_before = format_and_del_comment_java(
        extracted_macros_codes  
    )
    assert source_code_before is not None

    codefile = CodeFile(file_path, source_code_before, isformat=True)
    return codefile

def analysis_files(code_path):
    results = set()
    worker_list = []
    for root, _, files in os.walk(code_path):
        for file in files:
            if file.endswith(".java"):
                results.add(os.path.join(root, file))
    
    for file in results:
        worker_list.append((file, code_path))

    code_results = cpu_heater.multithreads(
        format, worker_list, max_workers=64, show_progress=False
    )

    return code_results

def create_code_tree(
    code_path: str, cache_dir: str
) -> str:
    code_files = analysis_files(code_path)
    code_dir = os.path.join(cache_dir, "code")

    os.makedirs(code_dir, exist_ok=True)

    for file in code_files:
        code = file.formated_code
        path = file.file_path
        assert path is not None
        os.makedirs(os.path.dirname(os.path.join(code_dir, path)), exist_ok=True)
        with open(os.path.join(code_dir, path), "w") as f:
            f.write(code)
