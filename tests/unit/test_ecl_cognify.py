"""
ECL Cognify 階段測試
"""

import tempfile

from mnemosyne.ecl.cognify import ASTCognifier


class TestASTCognifier:
    """AST 認知化器測試"""

    def test_cognifier_initialization(self):
        """測試認知化器初始化"""
        cognifier = ASTCognifier()
        assert cognifier.functions == []
        assert cognifier.calls == []
        assert cognifier.errors == []

    def test_cognify_empty_file_list(self):
        """測試認知化空檔案列表"""
        cognifier = ASTCognifier()
        result = cognifier.cognify_files([])

        assert result.functions == []
        assert result.calls == []
        assert result.errors == []

    def test_cognify_nonexistent_file(self):
        """測試認知化不存在的檔案"""
        cognifier = ASTCognifier()
        result = cognifier.cognify_files(["/nonexistent/file.py"])

        assert result.functions == []
        assert result.calls == []
        assert len(result.errors) == 1
        assert "讀取檔案失敗" in result.errors[0]

    def test_cognify_simple_function(self):
        """測試認知化簡單函數"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def hello_world():
    print("Hello, World!")
    return "hello"

def greet(name):
    return f"Hello, {name}!"
"""
            )
            f.flush()

            cognifier = ASTCognifier()
            result = cognifier.cognify_files([f.name])

            # 應該找到 2 個函數
            assert len(result.functions) == 2
            assert result.errors == []

            # 檢查函數資訊
            function_names = {func.name for func in result.functions}
            assert function_names == {"hello_world", "greet"}

            # 檢查函數詳細資訊
            hello_func = next(f for f in result.functions if f.name == "hello_world")
            assert hello_func.signature == "hello_world()"
            assert hello_func.is_method is False
            assert hello_func.class_name is None

            greet_func = next(f for f in result.functions if f.name == "greet")
            assert greet_func.signature == "greet(name)"

    def test_cognify_class_methods(self):
        """測試認知化類方法"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def standalone_function():
    pass
"""
            )
            f.flush()

            cognifier = ASTCognifier()
            result = cognifier.cognify_files([f.name])

            # 應該找到 3 個函數
            assert len(result.functions) == 3
            assert result.errors == []

            # 檢查方法
            methods = [f for f in result.functions if f.is_method]
            assert len(methods) == 2

            add_method = next(f for f in result.functions if f.name == "add")
            assert add_method.is_method is True
            assert add_method.class_name == "Calculator"

            # 檢查獨立函數
            standalone = next(
                f for f in result.functions if f.name == "standalone_function"
            )
            assert standalone.is_method is False
            assert standalone.class_name is None

    def test_cognify_function_calls(self):
        """測試認知化函數呼叫"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def helper():
    return "help"

def main():
    result = helper()
    return result

def another():
    main()
    helper()
"""
            )
            f.flush()

            cognifier = ASTCognifier()
            result = cognifier.cognify_files([f.name])

            # 應該找到 3 個函數和一些呼叫關係
            assert len(result.functions) == 3
            assert len(result.calls) > 0
            assert result.errors == []

            # 檢查呼叫關係
            call_pairs = {
                (call.caller_function, call.callee_function) for call in result.calls
            }
            assert ("main", "helper") in call_pairs
            assert ("another", "main") in call_pairs
            assert ("another", "helper") in call_pairs

    def test_cognify_syntax_error(self):
        """測試認知化語法錯誤檔案"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def broken_function(
    # 缺少右括號
    pass
"""
            )
            f.flush()

            cognifier = ASTCognifier()
            result = cognifier.cognify_files([f.name])

            # 應該有錯誤
            assert result.functions == []
            assert result.calls == []
            assert len(result.errors) == 1
            assert "語法錯誤" in result.errors[0]

    def test_cognify_empty_file(self):
        """測試認知化空檔案"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            f.flush()

            cognifier = ASTCognifier()
            result = cognifier.cognify_files([f.name])

            # 空檔案應該沒有函數和呼叫
            assert result.functions == []
            assert result.calls == []
            assert result.errors == []
