"""
Extract 階段：檔案系統提取器

負責從檔案系統中提取 Python 檔案。
"""

import os
from pathlib import Path
from typing import List


class FileSystemExtractor:
    """
    檔案系統提取器

    專注於 Python 檔案的提取，生成基礎的檔案清單。
    """

    def __init__(self, repo_path: str):
        """
        初始化提取器

        Args:
            repo_path: Git 倉儲路徑
        """
        self.repo_path = Path(repo_path).resolve()

    def extract_files(self) -> List[str]:
        """
        提取倉儲中的所有 Python 檔案

        Returns:
            List[str]: Python 檔案路徑列表
        """
        python_files = []

        if not self.repo_path.exists():
            return python_files

        if not self.repo_path.is_dir():
            return python_files

        # 遍歷檔案系統
        for root, dirs, files in os.walk(self.repo_path):
            # 跳過常見的忽略目錄
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in {
                    "__pycache__",
                    "node_modules",
                    "venv",
                    "env",
                    "build",
                    "dist",
                    ".pytest_cache",
                    "htmlcov",
                }
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def print_files(self) -> None:
        """列印所有找到的 Python 檔案"""
        files = self.extract_files()
        print(f"找到 {len(files)} 個 Python 檔案:")
        for file_path in files:
            print(f"  {file_path}")
