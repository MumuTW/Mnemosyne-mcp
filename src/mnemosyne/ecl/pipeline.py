"""
ECL 管線整合器

整合 Extract、Cognify、Load 三個階段的完整管線。
"""

from dataclasses import dataclass

from ..core.logging import get_logger
from ..drivers.falkordb_driver import FalkorDBDriver
from .cognify import ASTCognifier, CognifyResult
from .extract import ExtractionResult, FileSystemExtractor
from .load import GraphLoader, LoadResult

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """管線執行結果"""

    extraction_result: ExtractionResult
    cognify_result: CognifyResult
    load_result: LoadResult
    success: bool
    total_errors: int


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
        self.extractor = FileSystemExtractor()
        self.cognifier = ASTCognifier()
        self.loader = GraphLoader(driver)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

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
        self.logger.info(f"開始處理專案: {project_path}")

        # 清除現有資料（如果需要）
        if clear_existing:
            await self.loader.clear_project_data(project_path)

        # Extract 階段
        self.logger.info("執行 Extract 階段")
        extraction_result = self.extractor.extract_project(project_path)

        if not extraction_result.files:
            self.logger.warning("沒有找到任何檔案")
            return PipelineResult(
                extraction_result=extraction_result,
                cognify_result=CognifyResult(functions=[], calls=[], errors=[]),
                load_result=LoadResult(
                    files_loaded=0, functions_loaded=0, calls_loaded=0, errors=[]
                ),
                success=False,
                total_errors=len(extraction_result.errors),
            )

        # Cognify 階段
        self.logger.info("執行 Cognify 階段")
        cognify_result = self.cognifier.cognify_files(extraction_result.files)

        # Load 階段
        self.logger.info("執行 Load 階段")
        load_result = await self.loader.load_project_data(
            files=extraction_result.files,
            functions=cognify_result.functions,
            calls=cognify_result.calls,
        )

        # 計算總錯誤數
        total_errors = (
            len(extraction_result.errors)
            + len(cognify_result.errors)
            + len(load_result.errors)
        )

        success = extraction_result.files and total_errors == 0

        self.logger.info(
            "管線執行完成",
            success=success,
            files=len(extraction_result.files),
            functions=len(cognify_result.functions),
            calls=len(cognify_result.calls),
            errors=total_errors,
        )

        return PipelineResult(
            extraction_result=extraction_result,
            cognify_result=cognify_result,
            load_result=load_result,
            success=success,
            total_errors=total_errors,
        )
