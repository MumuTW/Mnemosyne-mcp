"""
Cognify 階段：AST 解析器

負責解析 Python 檔案的 AST，提取函數定義和呼叫關係。
"""

import ast
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class FunctionInfo:
    """函數資訊"""

    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    is_method: bool = False
    class_name: Optional[str] = None


@dataclass
class CallInfo:
    """呼叫關係資訊"""

    caller_function: str
    callee_function: str
    call_line: int
    file_path: str


@dataclass
class CognifyResult:
    """認知化結果"""

    functions: List[FunctionInfo]
    calls: List[CallInfo]
    errors: List[str]


class ASTCognifier:
    """
    AST 認知化器

    專注於解析 Python 函數定義和呼叫關係。
    """

    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.calls: List[CallInfo] = []
        self.errors: List[str] = []

    def cognify_files(self, file_paths: List[str]) -> CognifyResult:
        """
        認知化多個檔案

        Args:
            file_paths: 檔案路徑列表

        Returns:
            CognifyResult: 認知化結果
        """
        self.functions = []
        self.calls = []
        self.errors = []

        for file_path in file_paths:
            try:
                self._cognify_file(file_path)
            except Exception as e:
                error_msg = f"認知化檔案失敗 {file_path}: {str(e)}"
                self.errors.append(error_msg)

        return CognifyResult(
            functions=self.functions, calls=self.calls, errors=self.errors
        )

    def _cognify_file(self, file_path: str) -> None:
        """
        認知化單個檔案

        Args:
            file_path: 檔案路徑
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"讀取檔案失敗 {file_path}: {str(e)}")
            return

        if not content.strip():
            return

        try:
            # 解析 AST
            tree = ast.parse(content, filename=file_path)

            # 提取函數定義
            function_visitor = FunctionVisitor(file_path)
            function_visitor.visit(tree)
            self.functions.extend(function_visitor.functions)

            # 提取呼叫關係
            call_visitor = CallVisitor(file_path, function_visitor.function_names)
            call_visitor.visit(tree)
            self.calls.extend(call_visitor.calls)

        except SyntaxError as e:
            error_msg = f"語法錯誤 {file_path}:{e.lineno}: {e.msg}"
            self.errors.append(error_msg)
        except Exception as e:
            error_msg = f"解析錯誤 {file_path}: {str(e)}"
            self.errors.append(error_msg)


class FunctionVisitor(ast.NodeVisitor):
    """函數定義訪問器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions: List[FunctionInfo] = []
        self.function_names: Set[str] = set()
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """訪問類定義"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """訪問函數定義"""
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """訪問異步函數定義"""
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node):
        """處理函數節點"""
        # 計算函數簽名
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        signature = f"{node.name}({', '.join(args)})"

        function_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            is_method=self.current_class is not None,
            class_name=self.current_class,
        )

        self.functions.append(function_info)
        self.function_names.add(node.name)


class CallVisitor(ast.NodeVisitor):
    """函數呼叫訪問器"""

    def __init__(self, file_path: str, function_names: Set[str]):
        self.file_path = file_path
        self.function_names = function_names
        self.calls: List[CallInfo] = []
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """進入函數定義"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """進入異步函數定義"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node: ast.Call):
        """訪問函數呼叫"""
        if self.current_function:
            called_name = self._extract_call_name(node)
            if called_name and called_name in self.function_names:
                call_info = CallInfo(
                    caller_function=self.current_function,
                    callee_function=called_name,
                    call_line=node.lineno,
                    file_path=self.file_path,
                )
                self.calls.append(call_info)

        self.generic_visit(node)

    def _extract_call_name(self, node: ast.Call) -> Optional[str]:
        """提取呼叫的函數名稱"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
