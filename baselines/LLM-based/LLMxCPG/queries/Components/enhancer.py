from subprocess import call
from typing import Tuple
from Components.c_parser import analyze_c_code, CodeBlock
def format_code(file_name: str):
    lc = ["clang-format", "-i", file_name]
    return call(lc)

def find_block(code_line: int, blocks: list[CodeBlock]) -> Tuple[int, int]:
    block_start = -1
    block_end = -1

    for i in range(len(blocks)):
        block = blocks[i]
        if block.start_line <= code_line and code_line <= block.end_line:
            block_start = block.start_line
            block_end = block.end_line

    return block_start, block_end
def get_context(path: list[int], blocks: list[CodeBlock]) -> set[int]:
    context_lines = set()
    for i in path:
        context_lines.add(i)

    for i in range(len(path)):
        line_number = path[i]
        while line_number >= 0:
            block_start, block_end = find_block(line_number, blocks)
            if block_start != -1:
                context_lines.add(block_start)
                context_lines.add(block_end)

            line_number = block_start - 1
    
    return context_lines
def save_context(context: list[int], source_code: str, file_path: str) -> str:
    lines = source_code.splitlines()
    enhanced_joern = ""

    for line_number, line in enumerate(lines):
        line_number += 1
        
        if line_number not in context:
            continue

        enhanced_joern += line + "\n"

    with open(file_path, 'w') as f:
        f.write(enhanced_joern)

    return enhanced_joern
