"""
ECL Extractor 測試
"""

import tempfile
from pathlib import Path

from mnemosyne.ecl.extractor import FileSystemExtractor


class TestFileSystemExtractor:
    """檔案系統提取器測試"""

    def test_extractor_initialization(self):
        """測試提取器初始化"""
        extractor = FileSystemExtractor("/tmp")
        assert extractor.repo_path == Path("/tmp").resolve()

    def test_extract_nonexistent_path(self):
        """測試提取不存在的路徑"""
        extractor = FileSystemExtractor("/nonexistent/path")
        result = extractor.extract_files()
        assert result == []

    def test_extract_empty_directory(self):
        """測試提取空目錄"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            extractor = FileSystemExtractor(tmp_dir)
            result = extractor.extract_files()
            assert result == []

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

            extractor = FileSystemExtractor(tmp_dir)
            result = extractor.extract_files()

            # 應該找到 3 個 Python 檔案
            assert len(result) == 3

            # 檢查檔案名稱
            file_names = {Path(f).name for f in result}
            assert file_names == {"test1.py", "test2.py", "test3.py"}

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

            extractor = FileSystemExtractor(tmp_dir)
            result = extractor.extract_files()

            # 只應該找到正常檔案
            assert len(result) == 1
            assert Path(result[0]).name == "normal.py"

    def test_print_files_method(self):
        """測試列印檔案方法"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "test.py").write_text("def test(): pass")

            extractor = FileSystemExtractor(tmp_dir)
            # 這個方法應該不會拋出異常
            extractor.print_files()
