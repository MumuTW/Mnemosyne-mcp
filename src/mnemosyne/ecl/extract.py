"""
Extract 階段：檔案系統提取器

負責從檔案系統中提取 Python 檔案並生成基礎 Entity。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

from ..core.logging import get_logger
from ..schemas.core import File

logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    """提取結果"""

    files: List[File]
    total_files: int
    errors: List[str]


class FileSystemExtractor:
    """
    檔案系統提取器

    專注於 Python 檔案的提取，生成基礎的 File Entity。
    """

    def __init__(self, supported_extensions: Optional[List[str]] = None):
        """
        初始化提取器

        Args:
            supported_extensions: 支援的檔案副檔名，預設為 ['.py']
        """
        self.supported_extensions = supported_extensions or [".py"]
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def extract_project(self, project_path: str) -> ExtractionResult:
        """
        提取專案中的所有 Python 檔案

        Args:
            project_path: 專案路徑（相對或絕對）

        Returns:
            ExtractionResult: 提取結果
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            error_msg = f"專案路徑不存在: {project_path}"
            self.logger.error(error_msg)
            return ExtractionResult(files=[], total_files=0, errors=[error_msg])

        if not project_path.is_dir():
            error_msg = f"專案路徑不是目錄: {project_path}"
            self.logger.error(error_msg)
            return ExtractionResult(files=[], total_files=0, errors=[error_msg])

        self.logger.info(f"開始提取專案: {project_path}")

        files = []
        errors = []
        total_files = 0

        try:
            for file_path in self._find_python_files(project_path):
                total_files += 1
                try:
                    file_entity = self._create_file_entity(file_path, project_path)
                    files.append(file_entity)
                    self.logger.debug(f"成功提取檔案: {file_path}")
                except Exception as e:
                    error_msg = f"提取檔案失敗 {file_path}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"專案提取過程發生錯誤: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

        self.logger.info(f"提取完成: {len(files)}/{total_files} 檔案成功")

        return ExtractionResult(files=files, total_files=total_files, errors=errors)

    def _find_python_files(self, project_path: Path) -> Iterator[Path]:
        """
        遞迴尋找所有 Python 檔案

        Args:
            project_path: 專案根目錄

        Yields:
            Path: Python 檔案路徑
        """
        for root, dirs, files in os.walk(project_path):
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
                    ".git",
                    "build",
                    "dist",
                    ".pytest_cache",
                    "htmlcov",
                }
            ]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.supported_extensions:
                    yield file_path

    def _create_file_entity(self, file_path: Path, project_root: Path) -> File:
        """
        創建 File Entity

        Args:
            file_path: 檔案絕對路徑
            project_root: 專案根目錄

        Returns:
            File: File Entity
        """
        # 計算相對路徑
        try:
            relative_path = file_path.relative_to(project_root)
        except ValueError:
            # 如果檔案不在專案根目錄下，使用絕對路徑
            relative_path = file_path

        # 讀取檔案內容以計算 hash
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 嘗試其他編碼
            try:
                content = file_path.read_text(encoding="latin-1")
            except Exception:
                content = ""
        except Exception:
            content = ""

        # 獲取檔案統計資訊
        stat = file_path.stat()

        return File(
            name=file_path.name,
            path=str(relative_path),
            extension=file_path.suffix,
            content=content,  # 傳遞文件內容
            size_bytes=stat.st_size,
            encoding="utf-8",  # 預設編碼
            language="python",  # 目前只支援 Python
        )
