import os
import tempfile

from . import format_code
from .parse_tools import parseutility as parser
from .common import Language

class CodeFile:
    def __init__(self, file_path: str, code: str, language: Language, isformat: bool = True, loader=None, format_lambda: bool = False):
        self.file_path = file_path
        self._code = code
        self.language = language
        self.isformat = isformat
        self.loader = loader
        self.format_lambda = format_lambda
        self._formated_code = None

    @property
    def code(self):
        if self._code is None and self.loader:
            self._code = self.loader(self.file_path)
        return self._code
    
    @code.setter
    def code(self, value):
        self._code = value

    @property
    def formated_code(self):
        if self._formated_code is None:
            raw_code = self.code
            if self.isformat:
                if self.language == Language.C or self.language == Language.CPP:
                    self._formated_code = format_code.format_and_del_comment_c_cpp(raw_code)
                elif self.language == Language.JAVA:
                    self._formated_code = format_code.format_and_del_comment_java(raw_code, self.format_lambda)
            else:
                self._formated_code = raw_code
        return self._formated_code
    
    @formated_code.setter
    def formated_code(self, value):
        self._formated_code = value


def create_code_tree(
    code_files: list[CodeFile], dir: str, overwrite: bool = False
) -> str:
    code_dir = os.path.join(dir, "code")
    if os.path.exists(code_dir) and not overwrite:
        return code_dir
    os.makedirs(code_dir, exist_ok=True)

    for file in code_files:
        code = file.formated_code
        path = file.file_path
        assert path is not None
        os.makedirs(os.path.dirname(os.path.join(code_dir, path)), exist_ok=True)
        with open(os.path.join(code_dir, path), "w") as f:
            f.write(code)
    return code_dir
