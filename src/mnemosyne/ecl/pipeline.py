"""
ECL 管線整合器

整合 Extract、Cognify、Load 三個階段的完整管線。
"""

from dataclasses import dataclass
from typing import List

from ..drivers.falkordb_driver import FalkorDBDriver
from .cognify import ASTCognifier
from .extractor import FileSystemExtractor
from .loader import GraphLoader


@dataclass
class PipelineResult:
    """管線執行結果"""

    files_extracted: int
    functions_found: int
    calls_found: int
    functions_loaded: int
    calls_loaded: int
    errors: List[str]
    success: bool


class ECLPipeline:
    """
    ECL 管線

    整合 Extract、Cognify、Load 三個階段的完整處理流程。
    """

    def __init__(self, driver: FalkorDBDriver):
        """
        初始化管線

        Args:
            driver: FalkorDB 驅動器
        """
        self.driver = driver
        self.extractor = None
        self.cognifier = ASTCognifier()
        self.loader = GraphLoader(driver)

    async def process_project(
        self, project_path: str, clear_existing: bool = False
    ) -> PipelineResult:
        """
        處理專案

        Args:
            project_path: 專案路徑
            clear_existing: 是否清除現有資料

        Returns:
            PipelineResult: 管線執行結果
        """
        all_errors = []

        try:
            # 清除現有資料（如果需要）
            if clear_existing:
                await self.loader.clear_data()

            # Extract 階段
            self.extractor = FileSystemExtractor(project_path)
            python_files = self.extractor.extract_files()

            if not python_files:
                return PipelineResult(
                    files_extracted=0,
                    functions_found=0,
                    calls_found=0,
                    functions_loaded=0,
                    calls_loaded=0,
                    errors=["沒有找到任何 Python 檔案"],
                    success=False,
                )

            # Cognify 階段
            cognify_result = self.cognifier.cognify_files(python_files)
            all_errors.extend(cognify_result.errors)

            # Load 階段
            load_result = await self.loader.load_data(
                cognify_result.functions, cognify_result.calls
            )
            all_errors.extend(load_result.errors)

            # 計算成功狀態
            success = (
                len(python_files) > 0
                and len(cognify_result.functions) > 0
                and len(all_errors) == 0
            )

            return PipelineResult(
                files_extracted=len(python_files),
                functions_found=len(cognify_result.functions),
                calls_found=len(cognify_result.calls),
                functions_loaded=load_result.functions_loaded,
                calls_loaded=load_result.calls_loaded,
                errors=all_errors,
                success=success,
            )

        except Exception as e:
            error_msg = f"管線執行失敗: {str(e)}"
            all_errors.append(error_msg)

            return PipelineResult(
                files_extracted=0,
                functions_found=0,
                calls_found=0,
                functions_loaded=0,
                calls_loaded=0,
                errors=all_errors,
                success=False,
            )
