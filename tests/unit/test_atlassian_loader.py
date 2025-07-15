"""
測試 Atlassian 資料載入器
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.mnemosyne.ecl.atlassian_loader import AtlassianGraphLoader, AtlassianLoadResult
from src.mnemosyne.schemas.atlassian import AtlassianEntity, AtlassianRelationship
from src.mnemosyne.schemas.relationships import RelationshipType


class TestAtlassianGraphLoader:
    """測試 AtlassianGraphLoader 類"""

    @pytest.fixture
    def mock_driver(self):
        """建立 mock FalkorDB 驅動器"""
        driver = MagicMock()
        driver.is_connected = True
        driver.execute_query = AsyncMock()
        driver.connect = AsyncMock()
        return driver

    @pytest.fixture
    def loader(self, mock_driver):
        """建立 AtlassianGraphLoader 實例"""
        return AtlassianGraphLoader(mock_driver)

    @pytest.fixture
    def sample_jira_entity(self):
        """建立範例 Jira Issue 實體"""
        return AtlassianEntity(
            id="jira_issue_DEMO-123",
            entity_type="jira_issue",
            properties={
                "key": "DEMO-123",
                "summary": "Test Issue",
                "status": "Open",
                "project_key": "DEMO",
            },
        )

    @pytest.fixture
    def sample_confluence_entity(self):
        """建立範例 Confluence Page 實體"""
        return AtlassianEntity(
            id="confluence_page_123456",
            entity_type="confluence_page",
            properties={
                "title": "Test Page",
                "space_key": "DEMO",
                "space_name": "Demo Space",
            },
        )

    @pytest.fixture
    def sample_relationship(self):
        """建立範例關係"""
        return AtlassianRelationship(
            id="rel_123",
            source_id="jira_issue_DEMO-123",
            target_id="confluence_page_123456",
            relationship_type=RelationshipType.REFERENCES,
            properties={"strength": 0.8},
        )

    @pytest.mark.asyncio
    async def test_load_atlassian_data_success(
        self,
        loader,
        mock_driver,
        sample_jira_entity,
        sample_confluence_entity,
        sample_relationship,
    ):
        """測試成功載入 Atlassian 資料"""
        entities = [sample_jira_entity, sample_confluence_entity]
        relationships = [sample_relationship]

        result = await loader.load_atlassian_data(entities, relationships)

        assert isinstance(result, AtlassianLoadResult)
        assert result.jira_issues_loaded == 1
        assert result.confluence_pages_loaded == 1
        assert result.relationships_loaded == 1
        assert len(result.errors) == 0
        assert result.processing_time_ms >= 0

        # 驗證呼叫次數
        assert mock_driver.execute_query.call_count >= 3  # 至少實體和關係的載入

    @pytest.mark.asyncio
    async def test_load_jira_issue_node(self, loader, mock_driver, sample_jira_entity):
        """測試載入 Jira Issue 節點"""
        await loader._load_jira_issue_node(sample_jira_entity)

        # 驗證執行了 MERGE 查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) >= 1

        # 檢查第一個呼叫是 MERGE JiraIssue
        first_call = calls[0]
        query = first_call[0][0]
        assert "MERGE (issue:JiraIssue" in query
        assert "SET issue +=" in query

    @pytest.mark.asyncio
    async def test_load_confluence_page_node(
        self, loader, mock_driver, sample_confluence_entity
    ):
        """測試載入 Confluence Page 節點"""
        await loader._load_confluence_page_node(sample_confluence_entity)

        # 驗證執行了 MERGE 查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) >= 1

        # 檢查第一個呼叫是 MERGE ConfluencePage
        first_call = calls[0]
        query = first_call[0][0]
        assert "MERGE (page:ConfluencePage" in query
        assert "SET page +=" in query

    @pytest.mark.asyncio
    async def test_load_relationship(self, loader, mock_driver, sample_relationship):
        """測試載入關係"""
        await loader._load_relationship(sample_relationship)

        # 驗證執行了關係查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MATCH (source)" in query
        assert "MATCH (target)" in query
        assert "MERGE (source)-[r:ATLASSIAN_RELATION" in query

    @pytest.mark.asyncio
    async def test_ensure_project_node(self, loader, mock_driver):
        """測試確保 Project 節點存在"""
        await loader._ensure_project_node("DEMO")

        # 驗證執行了 MERGE JiraProject 查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MERGE (project:JiraProject" in query
        assert "ON CREATE SET" in query

    @pytest.mark.asyncio
    async def test_ensure_space_node(self, loader, mock_driver):
        """測試確保 Space 節點存在"""
        await loader._ensure_space_node("DEMO", "Demo Space")

        # 驗證執行了 MERGE ConfluenceSpace 查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MERGE (space:ConfluenceSpace" in query
        assert "ON CREATE SET" in query

    @pytest.mark.asyncio
    async def test_create_project_relationship(self, loader, mock_driver):
        """測試建立 Issue 與 Project 的關係"""
        await loader._create_project_relationship("issue_123", "DEMO")

        # 驗證執行了 BELONGS_TO 關係查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MATCH (issue:JiraIssue" in query
        assert "MATCH (project:JiraProject" in query
        assert "MERGE (issue)-[:BELONGS_TO]->(project)" in query

    @pytest.mark.asyncio
    async def test_create_space_relationship(self, loader, mock_driver):
        """測試建立 Page 與 Space 的關係"""
        await loader._create_space_relationship("page_123", "DEMO")

        # 驗證執行了 BELONGS_TO 關係查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MATCH (page:ConfluencePage" in query
        assert "MATCH (space:ConfluenceSpace" in query
        assert "MERGE (page)-[:BELONGS_TO]->(space)" in query

    @pytest.mark.asyncio
    async def test_clear_atlassian_data_with_filter(self, loader, mock_driver):
        """測試清除特定來源的 Atlassian 資料"""
        await loader.clear_atlassian_data("test_source")

        # 驗證執行了刪除查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MATCH (n)" in query
        assert "WHERE n.entity_type IN" in query
        assert "source_info CONTAINS" in query
        assert "DELETE r, n" in query

    @pytest.mark.asyncio
    async def test_clear_atlassian_data_all(self, loader, mock_driver):
        """測試清除所有 Atlassian 資料"""
        await loader.clear_atlassian_data()

        # 驗證執行了刪除查詢
        calls = mock_driver.execute_query.call_args_list
        assert len(calls) == 1

        query = calls[0][0][0]
        assert "MATCH (n)" in query
        assert "WHERE n.entity_type IN" in query
        assert "DELETE r, n" in query

    @pytest.mark.asyncio
    async def test_get_atlassian_stats(self, loader, mock_driver):
        """測試獲取 Atlassian 資料統計"""
        # Mock 查詢結果
        mock_result = MagicMock()
        mock_result.data = [{"count": 5}]
        mock_driver.execute_query.return_value = mock_result

        stats = await loader.get_atlassian_stats()

        assert isinstance(stats, dict)
        assert "jira_issues" in stats
        assert "confluence_pages" in stats
        assert "jira_projects" in stats
        assert "confluence_spaces" in stats
        assert "relationships" in stats
        assert stats["jira_issues"] == 5

    @pytest.mark.asyncio
    async def test_load_data_with_connection_error(self, loader, mock_driver):
        """測試連接錯誤時的處理"""
        mock_driver.is_connected = False
        mock_driver.connect.side_effect = Exception("Connection failed")

        entities = []
        relationships = []

        result = await loader.load_atlassian_data(entities, relationships)

        assert result.jira_issues_loaded == 0
        assert result.confluence_pages_loaded == 0
        assert result.relationships_loaded == 0
        assert len(result.errors) == 1
        assert "Connection failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_load_data_with_entity_error(
        self, loader, mock_driver, sample_jira_entity
    ):
        """測試實體載入錯誤時的處理"""
        mock_driver.execute_query.side_effect = Exception("Database error")

        entities = [sample_jira_entity]
        relationships = []

        result = await loader.load_atlassian_data(entities, relationships)

        assert result.jira_issues_loaded == 0
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_load_unknown_entity_type(self, loader, mock_driver):
        """測試未知實體類型的處理"""
        unknown_entity = AtlassianEntity(
            id="unknown_123",
            entity_type="unknown_type",
            properties={},
        )

        entities = [unknown_entity]
        relationships = []

        result = await loader.load_atlassian_data(entities, relationships)

        assert result.jira_issues_loaded == 0
        assert result.confluence_pages_loaded == 0
        assert result.relationships_loaded == 0
        assert len(result.errors) == 0  # 未知類型會被忽略但不會報錯

    @pytest.mark.asyncio
    async def test_load_data_performance(self, loader, mock_driver):
        """測試大量資料載入性能"""
        # 建立大量範例資料
        entities = []
        for i in range(100):
            entities.append(
                AtlassianEntity(
                    id=f"jira_issue_{i}",
                    entity_type="jira_issue",
                    properties={"key": f"DEMO-{i}"},
                )
            )

        relationships = []
        for i in range(50):
            relationships.append(
                AtlassianRelationship(
                    id=f"rel_{i}",
                    source_id=f"jira_issue_{i}",
                    target_id=f"jira_issue_{i+1}",
                    relationship_type=RelationshipType.DEPENDS_ON,
                    properties={},
                )
            )

        result = await loader.load_atlassian_data(entities, relationships)

        assert result.jira_issues_loaded == 100
        assert result.relationships_loaded == 50
        assert result.processing_time_ms >= 0
        assert len(result.errors) == 0
