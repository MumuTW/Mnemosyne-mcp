"""
Cognify 階段：AST 解析器

負責解析 Python 檔案的 AST，提取函數定義和呼叫關係。
"""

import ast
from dataclasses import dataclass
from typing import List, Optional

from ..core.logging import get_logger
from ..schemas.core import File, Function
from ..schemas.relationships import CallsRelationship

logger = get_logger(__name__)


@dataclass
class CognifyResult:
    """認知化結果"""

    functions: List[Function]
    calls: List[CallsRelationship]
    errors: List[str]


class ASTCognifier:
    """
    AST 認知化器

    專注於解析 Python 函數定義和呼叫關係。
    """

    def __init__(self):
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def cognify_files(self, files: List[File]) -> CognifyResult:
        """
        認知化多個檔案

        Args:
            files: 檔案列表

        Returns:
            CognifyResult: 認知化結果
        """
        all_functions = []
        all_calls = []
        all_errors = []

        for file in files:
            try:
                result = self.cognify_file(file)
                all_functions.extend(result.functions)
                all_calls.extend(result.calls)
                all_errors.extend(result.errors)
            except Exception as e:
                error_msg = f"認知化檔案失敗 {file.path}: {str(e)}"
                all_errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(f"認知化完成: {len(all_functions)} 函數, {len(all_calls)} 呼叫關係")

        return CognifyResult(
            functions=all_functions, calls=all_calls, errors=all_errors
        )

    def cognify_file(self, file: File) -> CognifyResult:
        """
        認知化單個檔案

        Args:
            file: 檔案 Entity

        Returns:
            CognifyResult: 認知化結果
        """
        functions = []
        calls = []
        errors = []

        if not file.content:
            self.logger.warning(f"檔案內容為空: {file.path}")
            return CognifyResult(functions=[], calls=[], errors=[])

        try:
            # 解析 AST
            tree = ast.parse(file.content, filename=file.path)

            # 提取函數定義
            function_visitor = FunctionVisitor(file)
            function_visitor.visit(tree)
            functions = function_visitor.functions

            # 提取呼叫關係
            call_visitor = CallVisitor(file, functions)
            call_visitor.visit(tree)
            calls = call_visitor.calls

            self.logger.debug(f"檔案 {file.path}: {len(functions)} 函數, {len(calls)} 呼叫")

        except SyntaxError as e:
            error_msg = f"語法錯誤 {file.path}:{e.lineno}: {e.msg}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"解析錯誤 {file.path}: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

        return CognifyResult(functions=functions, calls=calls, errors=errors)


class FunctionVisitor(ast.NodeVisitor):
    """函數定義訪問器"""

    def __init__(self, file: File):
        self.file = file
        self.functions: List[Function] = []
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
        args = [arg.arg for arg in node.args.args]

        # 處理預設參數
        defaults = [ast.unparse(default) for default in node.args.defaults]

        # 構建完整簽名
        signature_parts = []
        num_defaults = len(defaults)
        for i, arg in enumerate(args):
            if i >= len(args) - num_defaults:
                default_idx = i - (len(args) - num_defaults)
                signature_parts.append(f"{arg}={defaults[default_idx]}")
            else:
                signature_parts.append(arg)

        signature = f"{node.name}({', '.join(signature_parts)})"

        # 創建函數 Entity
        function = Function(
            name=node.name,
            signature=signature,
            file_path=self.file.path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=self.current_class is not None,
            class_name=self.current_class,
            docstring=ast.get_docstring(node),
            parameters=args,
            lines_of_code=node.end_lineno - node.lineno + 1 if node.end_lineno else 1,
        )

        self.functions.append(function)


class CallVisitor(ast.NodeVisitor):
    """函數呼叫訪問器"""

    def __init__(self, file: File, functions: List[Function]):
        self.file = file
        self.functions = functions
        self.calls: List[CallsRelationship] = []
        self.current_function: Optional[Function] = None

        # 建立函數映射，使用 (name, line_start) 作為唯一鍵避免命名衝突
        self.function_map = {(func.name, func.line_start): func for func in functions}
        # 同時保留名稱映射用於簡單查找（處理潛在的多個同名函數）
        self.function_name_map = {}
        for func in functions:
            if func.name not in self.function_name_map:
                self.function_name_map[func.name] = []
            self.function_name_map[func.name].append(func)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """進入函數定義"""
        old_function = self.current_function
        # 使用 (name, line_start) 精確匹配函數
        self.current_function = self.function_map.get((node.name, node.lineno))
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """進入異步函數定義"""
        old_function = self.current_function
        # 使用 (name, line_start) 精確匹配函數
        self.current_function = self.function_map.get((node.name, node.lineno))
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node: ast.Call):
        """訪問函數呼叫"""
        if self.current_function:
            called_name = self._extract_call_name(node)
            if called_name and called_name in self.function_name_map:
                # 處理同名函數的情況，選擇第一個匹配的函數
                # TODO: 未來可以改進為基於作用域的精確匹配
                potential_functions = self.function_name_map[called_name]
                called_function = potential_functions[0]  # 暫時選擇第一個

                # 創建呼叫關係
                call_relationship = CallsRelationship(
                    source_id=self.current_function.id,
                    target_id=called_function.id,
                    call_line=node.lineno,
                    context=(
                        ast.unparse(node) if hasattr(ast, "unparse") else str(node)
                    ),
                    is_conditional=self._is_conditional_call(node),
                )

                self.calls.append(call_relationship)

        self.generic_visit(node)

    def _extract_call_name(self, node: ast.Call) -> Optional[str]:
        """提取呼叫的函數名稱"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _is_conditional_call(self, node: ast.Call) -> bool:
        """判斷是否為條件呼叫（簡化版本）"""
        # 這裡可以實作更複雜的邏輯來判斷呼叫是否在條件語句中
        return False
