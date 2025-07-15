"""
Atlassian ECL 管線整合模組

整合 Atlassian 資料提取、處理和載入的完整管線。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.config import Settings
from ..core.logging import get_logger
from ..drivers.falkordb_driver import FalkorDBDriver
from ..grpc.atlassian_service_simple import AtlassianKnowledgeExtractorService
from ..interfaces.graph_store import ConnectionConfig
from ..mappers.atlassian_mapper_simple import AtlassianMapper
from ..schemas.atlassian import AtlassianEntity, AtlassianRelationship
from .atlassian_loader import AtlassianGraphLoader, AtlassianLoadResult

logger = get_logger(__name__)


@dataclass
class AtlassianPipelineResult:
    """Atlassian 管線執行結果"""

    extraction_success: bool
    entities_extracted: int
    relationships_extracted: int
    load_result: Optional[AtlassianLoadResult]
    processing_time_ms: int
    errors: List[str]


class AtlassianECLPipeline:
    """
    Atlassian ECL (Extract→Cognify→Load) 管線

    整合 Atlassian 知識提取、映射和載入的完整流程。
    """

    def __init__(self, settings: Settings):
        """
        初始化 Atlassian ECL 管線

        Args:
            settings: 系統設定
        """
        self.settings = settings
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # 初始化組件
        self.extractor_service = AtlassianKnowledgeExtractorService(settings)
        self.mapper = AtlassianMapper()

        # 初始化 FalkorDB 驅動器
        self.driver = FalkorDBDriver(
            ConnectionConfig(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                database=settings.falkordb.database,
                username=settings.falkordb.username,
                password=settings.falkordb.password,
            )
        )

        # 初始化資料載入器
        self.loader = AtlassianGraphLoader(self.driver)

    async def extract_and_load_jira_issues(
        self,
        jql_query: str,
        project_filter: Optional[str] = None,
        max_results: int = 100,
        include_relationships: bool = True,
    ) -> AtlassianPipelineResult:
        """
        提取並載入 Jira Issues

        Args:
            jql_query: JQL 查詢語句
            project_filter: 專案過濾器
            max_results: 最大結果數量
            include_relationships: 是否包含關係

        Returns:
            AtlassianPipelineResult: 管線執行結果
        """
        import time

        start_time = time.time()
        errors = []

        try:
            self.logger.info(f"開始提取 Jira Issues: {jql_query}")

            # Extract 階段：從 Atlassian 提取資料
            extraction_result = await self._extract_jira_issues(
                jql_query, project_filter, max_results, include_relationships
            )

            if not extraction_result["success"]:
                return AtlassianPipelineResult(
                    extraction_success=False,
                    entities_extracted=0,
                    relationships_extracted=0,
                    load_result=None,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    errors=extraction_result["errors"],
                )

            # Cognify 階段：映射和轉換資料
            entities, relationships = await self._cognify_jira_data(
                extraction_result["issues"], extraction_result["relationships"]
            )

            # Load 階段：載入到圖資料庫
            load_result = await self.loader.load_atlassian_data(entities, relationships)

            processing_time_ms = int((time.time() - start_time) * 1000)

            self.logger.info(
                f"Jira Issues 管線完成: {len(entities)} 實體, {len(relationships)} 關係"
            )

            return AtlassianPipelineResult(
                extraction_success=True,
                entities_extracted=len(entities),
                relationships_extracted=len(relationships),
                load_result=load_result,
                processing_time_ms=processing_time_ms,
                errors=load_result.errors,
            )

        except Exception as e:
            error_msg = f"Jira Issues 管線執行失敗: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

            return AtlassianPipelineResult(
                extraction_success=False,
                entities_extracted=0,
                relationships_extracted=0,
                load_result=None,
                processing_time_ms=int((time.time() - start_time) * 1000),
                errors=errors,
            )

    async def extract_and_load_confluence_pages(
        self,
        query: str,
        space_filter: Optional[str] = None,
        max_results: int = 100,
        include_relationships: bool = True,
    ) -> AtlassianPipelineResult:
        """
        提取並載入 Confluence Pages

        Args:
            query: 頁面搜尋查詢
            space_filter: 空間過濾器
            max_results: 最大結果數量
            include_relationships: 是否包含關係

        Returns:
            AtlassianPipelineResult: 管線執行結果
        """
        import time

        start_time = time.time()
        errors = []

        try:
            self.logger.info(f"開始提取 Confluence Pages: {query}")

            # Extract 階段：從 Atlassian 提取資料
            extraction_result = await self._extract_confluence_pages(
                query, space_filter, max_results, include_relationships
            )

            if not extraction_result["success"]:
                return AtlassianPipelineResult(
                    extraction_success=False,
                    entities_extracted=0,
                    relationships_extracted=0,
                    load_result=None,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    errors=extraction_result["errors"],
                )

            # Cognify 階段：映射和轉換資料
            entities, relationships = await self._cognify_confluence_data(
                extraction_result["pages"], extraction_result["relationships"]
            )

            # Load 階段：載入到圖資料庫
            load_result = await self.loader.load_atlassian_data(entities, relationships)

            processing_time_ms = int((time.time() - start_time) * 1000)

            self.logger.info(
                f"Confluence Pages 管線完成: {len(entities)} 實體, {len(relationships)} 關係"
            )

            return AtlassianPipelineResult(
                extraction_success=True,
                entities_extracted=len(entities),
                relationships_extracted=len(relationships),
                load_result=load_result,
                processing_time_ms=processing_time_ms,
                errors=load_result.errors,
            )

        except Exception as e:
            error_msg = f"Confluence Pages 管線執行失敗: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

            return AtlassianPipelineResult(
                extraction_success=False,
                entities_extracted=0,
                relationships_extracted=0,
                load_result=None,
                processing_time_ms=int((time.time() - start_time) * 1000),
                errors=errors,
            )

    async def _extract_jira_issues(
        self,
        jql_query: str,
        project_filter: Optional[str],
        max_results: int,
        include_relationships: bool,
    ) -> Dict[str, Any]:
        """提取 Jira Issues 資料"""
        try:
            # 使用 AtlassianClient 調用真實的 MCP Atlassian 服務
            if not self.extractor_service:
                return {
                    "success": False,
                    "issues": [],
                    "relationships": [],
                    "errors": ["Atlassian 提取服務未配置"],
                }

            # 調用 AtlassianClient 搜索 Jira Issues
            search_result = await self.extractor_service.search_jira_issues(
                query=jql_query, project_filter=project_filter, max_results=max_results
            )

            issues = search_result.get("issues", [])
            relationships = []

            # 如果需要包含關係，為每個 Issue 建立與 Project 的關係
            if include_relationships:
                for issue in issues:
                    project_key = issue.get("project", "")
                    if project_key:
                        relationships.append(
                            {
                                "source_id": f"jira_issue_{issue['key']}",
                                "target_id": f"jira_project_{project_key}",
                                "relationship_type": "BELONGS_TO",
                                "properties": {"project_key": project_key},
                            }
                        )

            return {
                "success": True,
                "issues": issues,
                "relationships": relationships,
                "errors": [],
            }
        except Exception as e:
            return {
                "success": False,
                "issues": [],
                "relationships": [],
                "errors": [f"提取 Jira Issues 失敗: {str(e)}"],
            }

    async def _extract_confluence_pages(
        self,
        query: str,
        space_filter: Optional[str],
        max_results: int,
        include_relationships: bool,
    ) -> Dict[str, Any]:
        """提取 Confluence Pages 資料"""
        try:
            # 使用 AtlassianClient 調用真實的 MCP Atlassian 服務
            if not self.extractor_service:
                return {
                    "success": False,
                    "pages": [],
                    "relationships": [],
                    "errors": ["Atlassian 提取服務未配置"],
                }

            # 調用 AtlassianClient 搜索 Confluence Pages
            search_result = await self.extractor_service.search_confluence_pages(
                query=query, space_filter=space_filter, max_results=max_results
            )

            pages = search_result.get("pages", [])
            relationships = []

            # 如果需要包含關係，為每個 Page 建立與 Space 的關係
            if include_relationships:
                for page in pages:
                    space_key = page.get("space", "")
                    if space_key:
                        relationships.append(
                            {
                                "source_id": f"confluence_page_{page['id']}",
                                "target_id": f"confluence_space_{space_key}",
                                "relationship_type": "BELONGS_TO",
                                "properties": {"space_key": space_key},
                            }
                        )

            return {
                "success": True,
                "pages": pages,
                "relationships": relationships,
                "errors": [],
            }
        except Exception as e:
            return {
                "success": False,
                "pages": [],
                "relationships": [],
                "errors": [f"提取 Confluence Pages 失敗: {str(e)}"],
            }

    async def _cognify_jira_data(
        self, issues: List[Any], relationships: List[Any]
    ) -> tuple[List[AtlassianEntity], List[AtlassianRelationship]]:
        """
        Cognify 階段：映射 Jira 資料

        Args:
            issues: Jira Issues 原始資料
            relationships: 關係原始資料

        Returns:
            tuple: (實體列表, 關係列表)
        """
        entities = []
        mapped_relationships = []

        # 映射 Jira Issues
        for issue in issues:
            entity = self.mapper.map_jira_issue_to_entity(issue)
            entities.append(entity)

        # 映射關係
        for relationship in relationships:
            mapped_rel = self.mapper.map_relationship(relationship)
            mapped_relationships.append(mapped_rel)

        return entities, mapped_relationships

    async def _cognify_confluence_data(
        self, pages: List[Any], relationships: List[Any]
    ) -> tuple[List[AtlassianEntity], List[AtlassianRelationship]]:
        """
        Cognify 階段：映射 Confluence 資料

        Args:
            pages: Confluence Pages 原始資料
            relationships: 關係原始資料

        Returns:
            tuple: (實體列表, 關係列表)
        """
        entities = []
        mapped_relationships = []

        # 映射 Confluence Pages
        for page in pages:
            entity = self.mapper.map_confluence_page_to_entity(page)
            entities.append(entity)

        # 映射關係
        for relationship in relationships:
            mapped_rel = self.mapper.map_relationship(relationship)
            mapped_relationships.append(mapped_rel)

        return entities, mapped_relationships

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        獲取管線狀態

        Returns:
            Dict: 管線狀態資訊
        """
        try:
            # 檢查資料庫連接
            db_status = await self.driver.ping()

            # 獲取統計資訊
            stats = await self.loader.get_atlassian_stats()

            return {
                "database_connected": db_status,
                "statistics": stats,
                "components": {
                    "extractor": "ready",
                    "mapper": "ready",
                    "loader": "ready",
                },
            }
        except Exception as e:
            return {
                "database_connected": False,
                "error": str(e),
                "components": {
                    "extractor": "unknown",
                    "mapper": "unknown",
                    "loader": "error",
                },
            }

    async def clear_data(self, source_filter: Optional[str] = None) -> None:
        """
        清除管線資料

        Args:
            source_filter: 資料源過濾器
        """
        await self.loader.clear_atlassian_data(source_filter)
        self.logger.info(f"管線資料清除完成: {source_filter or '全部'}")

    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.driver.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.driver.disconnect()
