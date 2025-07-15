"""
ECL Extract 階段測試
"""

import tempfile
from pathlib import Path

from mnemosyne.ecl.extract import FileSystemExtractor


class TestFileSystemExtractor:
    """檔案系統提取器測試"""

    def test_extractor_initialization(self):
        """測試提取器初始化"""
        extractor = FileSystemExtractor()
        assert extractor.supported_extensions == [".py"]

        extractor_custom = FileSystemExtractor([".py", ".pyx"])
        assert extractor_custom.supported_extensions == [".py", ".pyx"]

    def test_extract_nonexistent_path(self):
        """測試提取不存在的路徑"""
        extractor = FileSystemExtractor()
        result = extractor.extract_project("/nonexistent/path")

        assert result.files == []
        assert result.total_files == 0
        assert len(result.errors) == 1
        assert "專案路徑不存在" in result.errors[0]

    def test_extract_file_instead_of_directory(self):
        """測試提取檔案而非目錄"""
        with tempfile.NamedTemporaryFile(suffix=".py") as tmp_file:
            extractor = FileSystemExtractor()
            result = extractor.extract_project(tmp_file.name)

            assert result.files == []
            assert result.total_files == 0
            assert len(result.errors) == 1
            assert "專案路徑不是目錄" in result.errors[0]

    def test_extract_empty_directory(self):
        """測試提取空目錄"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            extractor = FileSystemExtractor()
            result = extractor.extract_project(tmp_dir)

            assert result.files == []
            assert result.total_files == 0
            assert result.errors == []

    def test_extract_python_files(self):
        """測試提取 Python 檔案"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 創建測試檔案
            (tmp_path / "test1.py").write_text("def hello(): pass")
            (tmp_path / "test2.py").write_text("def world(): pass")
            (tmp_path / "not_python.txt").write_text("not python")

            # 創建子目錄
            sub_dir = tmp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "test3.py").write_text("def nested(): pass")

            extractor = FileSystemExtractor()
            result = extractor.extract_project(tmp_dir)

            assert len(result.files) == 3
            assert result.total_files == 3
            assert result.errors == []

            # 檢查檔案內容
            file_names = {f.name for f in result.files}
            assert file_names == {"test1.py", "test2.py", "test3.py"}

            # 檢查檔案內容
            for file in result.files:
                assert file.content
                assert file.language == "python"
                assert file.extension == ".py"

    def test_extract_with_ignored_directories(self):
        """測試忽略特定目錄"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 創建正常檔案
            (tmp_path / "normal.py").write_text("def normal(): pass")

            # 創建應該被忽略的目錄
            ignored_dirs = ["__pycache__", ".git", "node_modules", "venv"]
            for ignored_dir in ignored_dirs:
                ignored_path = tmp_path / ignored_dir
                ignored_path.mkdir()
                (ignored_path / "ignored.py").write_text("def ignored(): pass")

            extractor = FileSystemExtractor()
            result = extractor.extract_project(tmp_dir)

            # 只應該找到正常檔案
            assert len(result.files) == 1
            assert result.files[0].name == "normal.py"

    def test_file_entity_creation(self):
        """測試檔案實體創建"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            test_file = tmp_path / "test.py"
            test_content = """def hello_world():
    \"\"\"Hello world function\"\"\"
    print("Hello, World!")
    return "Hello"
"""
            test_file.write_text(test_content)

            extractor = FileSystemExtractor()
            result = extractor.extract_project(tmp_dir)

            assert len(result.files) == 1
            file_entity = result.files[0]

            assert file_entity.name == "test.py"
            assert file_entity.path == "test.py"  # 相對路徑
            assert file_entity.extension == ".py"
            assert file_entity.content == test_content
            assert file_entity.language == "python"
            assert file_entity.encoding == "utf-8"
            assert file_entity.size_bytes > 0
