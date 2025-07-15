"""
Atlassian 資料載入器 (Atlassian Data Loader)

擴展 ECL 管線以支援 Atlassian 知識圖譜資料載入。
"""

import time
from dataclasses import dataclass
from typing import List, Optional

from ..core.logging import get_logger
from ..drivers.falkordb_driver import FalkorDBDriver
from ..schemas.atlassian import AtlassianEntity, AtlassianRelationship

logger = get_logger(__name__)


@dataclass
class AtlassianLoadResult:
    """Atlassian 資料載入結果"""

    jira_issues_loaded: int
    confluence_pages_loaded: int
    relationships_loaded: int
    errors: List[str]
    processing_time_ms: int


class AtlassianGraphLoader:
    """
    Atlassian 圖資料庫載入器

    負責將 Atlassian 知識圖譜資料載入到 FalkorDB 中。
    支援 Jira Issues, Confluence Pages 和它們之間的關係。
    """

    def __init__(self, driver: FalkorDBDriver):
        """
        初始化 Atlassian 載入器

        Args:
            driver: FalkorDB 驅動器
        """
        self.driver = driver
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    async def load_atlassian_data(
        self,
        entities: List[AtlassianEntity],
        relationships: List[AtlassianRelationship],
    ) -> AtlassianLoadResult:
        """
        載入 Atlassian 知識圖譜資料

        Args:
            entities: Atlassian 實體列表 (Jira Issues + Confluence Pages)
            relationships: Atlassian 關係列表

        Returns:
            AtlassianLoadResult: 載入結果
        """
        start_time = time.time()
        errors = []
        jira_issues_loaded = 0
        confluence_pages_loaded = 0
        relationships_loaded = 0

        try:
            # 確保連接
            if not self.driver.is_connected:
                await self.driver.connect()

            # 載入實體節點
            for entity in entities:
                try:
                    if entity.entity_type == "jira_issue":
                        await self._load_jira_issue_node(entity)
                        jira_issues_loaded += 1
                        self.logger.debug(f"載入 Jira Issue: {entity.id}")
                    elif entity.entity_type == "confluence_page":
                        await self._load_confluence_page_node(entity)
                        confluence_pages_loaded += 1
                        self.logger.debug(f"載入 Confluence Page: {entity.id}")
                    else:
                        self.logger.warning(f"未知實體類型: {entity.entity_type}")
                except Exception as e:
                    error_msg = f"載入實體節點失敗 {entity.id}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # 載入關係
            for relationship in relationships:
                try:
                    await self._load_relationship(relationship)
                    relationships_loaded += 1
                    self.logger.debug(
                        f"載入關係: {relationship.source_id} -> {relationship.target_id}"
                    )
                except Exception as e:
                    error_msg = f"載入關係失敗 {relationship.source_id} -> {relationship.target_id}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            processing_time_ms = int((time.time() - start_time) * 1000)

            self.logger.info(
                f"Atlassian 資料載入完成: {jira_issues_loaded} Jira Issues, "
                f"{confluence_pages_loaded} Confluence Pages, {relationships_loaded} 關係"
            )

        except Exception as e:
            error_msg = f"Atlassian 資料載入過程發生錯誤: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            processing_time_ms = int((time.time() - start_time) * 1000)

        return AtlassianLoadResult(
            jira_issues_loaded=jira_issues_loaded,
            confluence_pages_loaded=confluence_pages_loaded,
            relationships_loaded=relationships_loaded,
            errors=errors,
            processing_time_ms=processing_time_ms,
        )

    async def _load_jira_issue_node(self, entity: AtlassianEntity) -> None:
        """載入 Jira Issue 節點"""
        properties = entity.to_graph_properties()

        # 使用 MERGE 確保節點唯一性
        query = """
        MERGE (issue:JiraIssue {id: $id})
        SET issue += $properties
        RETURN issue
        """

        await self.driver.execute_query(
            query, parameters={"id": entity.id, "properties": properties}
        )

        # 如果有 project_key，建立與 Project 的關係
        if hasattr(entity, "project_key") and entity.project_key:
            await self._ensure_project_node(entity.project_key)
            await self._create_project_relationship(entity.id, entity.project_key)

    async def _load_confluence_page_node(self, entity: AtlassianEntity) -> None:
        """載入 Confluence Page 節點"""
        properties = entity.to_graph_properties()

        # 使用 MERGE 確保節點唯一性
        query = """
        MERGE (page:ConfluencePage {id: $id})
        SET page += $properties
        RETURN page
        """

        await self.driver.execute_query(
            query, parameters={"id": entity.id, "properties": properties}
        )

        # 如果有 space_key，建立與 Space 的關係
        if hasattr(entity, "space_key") and entity.space_key:
            await self._ensure_space_node(
                entity.space_key, getattr(entity, "space_name", "")
            )
            await self._create_space_relationship(entity.id, entity.space_key)

    async def _load_relationship(self, relationship: AtlassianRelationship) -> None:
        """載入關係"""
        properties = relationship.to_graph_properties()

        # 建立關係
        query = """
        MATCH (source) WHERE source.id = $source_id
        MATCH (target) WHERE target.id = $target_id
        MERGE (source)-[r:ATLASSIAN_RELATION {type: $relationship_type}]->(target)
        SET r += $properties
        RETURN r
        """

        await self.driver.execute_query(
            query,
            parameters={
                "source_id": relationship.source_id,
                "target_id": relationship.target_id,
                "relationship_type": str(relationship.relationship_type),
                "properties": properties,
            },
        )

    async def _ensure_project_node(self, project_key: str) -> None:
        """確保 Project 節點存在"""
        query = """
        MERGE (project:JiraProject {key: $project_key})
        ON CREATE SET project.name = $project_key,
                      project.entity_type = 'jira_project',
                      project.created_at = datetime()
        RETURN project
        """

        await self.driver.execute_query(query, parameters={"project_key": project_key})

    async def _ensure_space_node(self, space_key: str, space_name: str) -> None:
        """確保 Space 節點存在"""
        query = """
        MERGE (space:ConfluenceSpace {key: $space_key})
        ON CREATE SET space.name = $space_name,
                      space.entity_type = 'confluence_space',
                      space.created_at = datetime()
        RETURN space
        """

        await self.driver.execute_query(
            query, parameters={"space_key": space_key, "space_name": space_name}
        )

    async def _create_project_relationship(
        self, issue_id: str, project_key: str
    ) -> None:
        """建立 Issue 與 Project 的關係"""
        query = """
        MATCH (issue:JiraIssue {id: $issue_id})
        MATCH (project:JiraProject {key: $project_key})
        MERGE (issue)-[:BELONGS_TO]->(project)
        """

        await self.driver.execute_query(
            query, parameters={"issue_id": issue_id, "project_key": project_key}
        )

    async def _create_space_relationship(self, page_id: str, space_key: str) -> None:
        """建立 Page 與 Space 的關係"""
        query = """
        MATCH (page:ConfluencePage {id: $page_id})
        MATCH (space:ConfluenceSpace {key: $space_key})
        MERGE (page)-[:BELONGS_TO]->(space)
        """

        await self.driver.execute_query(
            query, parameters={"page_id": page_id, "space_key": space_key}
        )

    async def clear_atlassian_data(self, source_filter: Optional[str] = None) -> None:
        """
        清除 Atlassian 資料

        Args:
            source_filter: 資料源過濾器，如果提供則只清除該來源的資料
        """
        if source_filter:
            # 清除特定來源的資料
            query = """
            MATCH (n)
            WHERE n.entity_type IN ['jira_issue', 'confluence_page', 'jira_project', 'confluence_space']
            AND (n.source_info IS NULL OR n.source_info CONTAINS $source_filter)
            OPTIONAL MATCH (n)-[r]-()
            DELETE r, n
            """
            await self.driver.execute_query(
                query, parameters={"source_filter": source_filter}
            )
        else:
            # 清除所有 Atlassian 資料
            query = """
            MATCH (n)
            WHERE n.entity_type IN ['jira_issue', 'confluence_page', 'jira_project', 'confluence_space']
            OPTIONAL MATCH (n)-[r]-()
            DELETE r, n
            """
            await self.driver.execute_query(query)

        self.logger.info(f"清除 Atlassian 資料完成: {source_filter or '全部'}")

    async def get_atlassian_stats(self) -> dict:
        """
        獲取 Atlassian 資料統計

        Returns:
            dict: 統計資訊
        """
        stats = {}

        # 統計各類型節點數量
        count_queries = {
            "jira_issues": "MATCH (n:JiraIssue) RETURN count(n) as count",
            "confluence_pages": "MATCH (n:ConfluencePage) RETURN count(n) as count",
            "jira_projects": "MATCH (n:JiraProject) RETURN count(n) as count",
            "confluence_spaces": "MATCH (n:ConfluenceSpace) RETURN count(n) as count",
            "relationships": "MATCH ()-[r:ATLASSIAN_RELATION]-() RETURN count(r) as count",
        }

        for stat_name, query in count_queries.items():
            result = await self.driver.execute_query(query)
            stats[stat_name] = result.data[0]["count"] if result.data else 0

        return stats
