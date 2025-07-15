"""
AtlassianMapper 簡化測試

測試 Atlassian 數據映射器的基本功能。
"""

from mnemosyne.clients.atlassian import ConfluencePage, JiraIssue
from mnemosyne.mappers.atlassian_mapper_simple import AtlassianMapper
from mnemosyne.schemas.core import EntityType


class TestAtlassianMapperSimple:
    """測試 AtlassianMapper 基本功能"""

    def test_jira_issue_to_entity_basic(self):
        """測試 Jira Issue 基本映射"""
        issue = JiraIssue(
            id="10123",
            key="DEMO-123",
            summary="測試 Issue",
            status="Open",
        )

        entity = AtlassianMapper.jira_issue_to_entity(issue)

        assert entity.id == "jira_issue_DEMO-123"
        assert entity.name == "測試 Issue"
        assert entity.entity_type == EntityType.ISSUE
        assert entity.extra["jira_key"] == "DEMO-123"
        assert entity.extra["status"] == "Open"

    def test_confluence_page_to_entity_basic(self):
        """測試 Confluence 頁面基本映射"""
        page = ConfluencePage(
            id="123456",
            title="測試頁面",
        )

        entity = AtlassianMapper.confluence_page_to_entity(page)

        assert entity.id == "confluence_page_123456"
        assert entity.name == "測試頁面"
        assert entity.entity_type == EntityType.DOCUMENT
        assert entity.extra["confluence_id"] == "123456"
        assert entity.extra["title"] == "測試頁面"

    def test_create_project_relationship_basic(self):
        """測試創建專案關係"""
        issue = JiraIssue(
            id="10123",
            key="DEMO-123",
            summary="測試 Issue",
            status="Open",
        )

        entity = AtlassianMapper.jira_issue_to_entity(issue)
        relationship = AtlassianMapper.create_project_relationship(entity, "DEMO")

        assert relationship is not None
        assert relationship.source_id == entity.id
        assert relationship.target_id == "jira_project_DEMO"
        assert relationship.extra["project_name"] == "DEMO"
