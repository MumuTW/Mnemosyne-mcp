"""
AtlassianKnowledgeExtractorService gRPC 服務測試

測試 gRPC 服務的基本功能和契約。
"""

from unittest.mock import Mock

import pytest
from aioresponses import aioresponses

from mnemosyne.core.config import MCPAtlassianSettings, Settings
from mnemosyne.grpc import atlassian_pb2
from mnemosyne.grpc.atlassian_service_simple import AtlassianKnowledgeExtractorService
from tests.mocks.mcp_atlassian_mock import MCPAtlassianMockServer


class TestAtlassianKnowledgeExtractorService:
    """測試 AtlassianKnowledgeExtractorService"""

    @pytest.fixture
    def settings(self):
        """創建測試用配置"""
        return Settings(
            mcp_atlassian=MCPAtlassianSettings(
                service_url="http://mcp-atlassian:8001",
                read_only_mode=True,
                enabled_tools=["confluence_search", "jira_search", "jira_get_issue"],
                jira_url="https://company.atlassian.net",
                jira_username="test@company.com",
                jira_api_token="test-token",
                confluence_url="https://company.atlassian.net/wiki",
                confluence_username="test@company.com",
                confluence_api_token="test-token",
            )
        )

    @pytest.fixture
    def mock_context(self):
        """創建模擬的 gRPC 上下文"""
        context = Mock()
        context.set_code = Mock()
        context.set_details = Mock()
        return context

    @pytest.fixture
    def mock_server(self):
        """創建模擬伺服器"""
        return MCPAtlassianMockServer()

    @pytest.mark.asyncio
    async def test_service_initialization(self, settings):
        """測試服務初始化"""
        service = AtlassianKnowledgeExtractorService(settings)

        assert service.settings == settings
        assert service.client is None
        assert service.mapper is not None
        assert service.stats["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_client_initialization(self, settings):
        """測試客戶端初始化"""
        service = AtlassianKnowledgeExtractorService(settings)

        await service.init_client()

        assert service.client is not None
        assert service.client.is_configured is True

        await service.close_client()

    @pytest.mark.asyncio
    async def test_health_check_without_connectivity(self, settings, mock_context):
        """測試不檢查連通性的健康檢查"""
        service = AtlassianKnowledgeExtractorService(settings)
        await service.init_client()

        try:
            request = atlassian_pb2.HealthCheckRequest(check_connectivity=False)
            response = await service.CheckHealth(request, mock_context)

            assert response.status == atlassian_pb2.HealthCheckResponse.Status.HEALTHY
            assert response.message == "Service is running"
            assert response.response_time_ms > 0
        finally:
            await service.close_client()

    @pytest.mark.asyncio
    async def test_health_check_with_connectivity(
        self, settings, mock_context, mock_server
    ):
        """測試檢查連通性的健康檢查"""
        service = AtlassianKnowledgeExtractorService(settings)
        await service.init_client()

        try:
            with aioresponses() as m:
                mock_server.setup_successful_responses(m)

                request = atlassian_pb2.HealthCheckRequest(check_connectivity=True)
                response = await service.CheckHealth(request, mock_context)

                assert (
                    response.status == atlassian_pb2.HealthCheckResponse.Status.HEALTHY
                )
                assert response.response_time_ms > 0
        finally:
            await service.close_client()

    @pytest.mark.asyncio
    async def test_extract_jira_issues_success(
        self, settings, mock_context, mock_server
    ):
        """測試成功提取 Jira Issues"""
        service = AtlassianKnowledgeExtractorService(settings)
        await service.init_client()

        try:
            with aioresponses() as m:
                mock_server.setup_successful_responses(m)

                request = atlassian_pb2.ExtractJiraIssuesRequest(
                    query="bug fix",
                    max_results=10,
                    include_relationships=True,
                )
                response = await service.ExtractJiraIssues(request, mock_context)

                assert len(response.issues) == 2
                assert response.issues[0].key == "DEMO-123"
                assert response.issues[0].summary == "修復登入功能錯誤"
                assert response.metadata.total_entities == 2
                assert response.metadata.processing_time_ms > 0

                # 驗證統計更新
                assert service.stats["total_requests"] == 1
                assert service.stats["successful_requests"] == 1
                assert service.stats["issues_extracted"] == 2
        finally:
            await service.close_client()

    @pytest.mark.asyncio
    async def test_extract_confluence_pages_success(
        self, settings, mock_context, mock_server
    ):
        """測試成功提取 Confluence Pages"""
        service = AtlassianKnowledgeExtractorService(settings)
        await service.init_client()

        try:
            with aioresponses() as m:
                mock_server.setup_successful_responses(m)

                request = atlassian_pb2.ExtractConfluencePagesRequest(
                    query="API",
                    max_results=10,
                    include_relationships=True,
                )
                response = await service.ExtractConfluencePages(request, mock_context)

                assert len(response.pages) == 2
                assert response.pages[0].title == "API 開發指南"
                assert response.pages[0].space_key == "DEV"
                assert response.metadata.total_entities == 2
                assert response.metadata.processing_time_ms > 0

                # 驗證統計更新
                assert service.stats["total_requests"] == 1
                assert service.stats["successful_requests"] == 1
                assert service.stats["pages_extracted"] == 2
        finally:
            await service.close_client()

    @pytest.mark.asyncio
    async def test_extract_jira_issues_not_configured(self, mock_context):
        """測試未配置時的行為"""
        unconfigured_settings = Settings(mcp_atlassian=MCPAtlassianSettings())

        service = AtlassianKnowledgeExtractorService(unconfigured_settings)

        request = atlassian_pb2.ExtractJiraIssuesRequest(query="test")
        response = await service.ExtractJiraIssues(request, mock_context)

        assert len(response.issues) == 0
        mock_context.set_code.assert_called_once()
        mock_context.set_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_extraction_stats(self, settings, mock_context):
        """測試獲取提取統計"""
        service = AtlassianKnowledgeExtractorService(settings)

        # 模擬一些統計數據
        service.stats["total_requests"] = 10
        service.stats["successful_requests"] = 8
        service.stats["failed_requests"] = 2
        service.stats["issues_extracted"] = 15
        service.stats["pages_extracted"] = 12

        request = atlassian_pb2.GetExtractionStatsRequest()
        response = await service.GetExtractionStats(request, mock_context)

        assert response.total_requests == 10
        assert response.successful_requests == 8
        assert response.failed_requests == 2
        assert response.success_rate == 80.0
        assert response.issues_extracted == 15
        assert response.pages_extracted == 12

    @pytest.mark.asyncio
    async def test_error_handling(self, settings, mock_context, mock_server):
        """測試錯誤處理"""
        service = AtlassianKnowledgeExtractorService(settings)
        await service.init_client()

        try:
            with aioresponses() as m:
                mock_server.setup_error_responses(m)

                request = atlassian_pb2.ExtractJiraIssuesRequest(query="test")
                response = await service.ExtractJiraIssues(request, mock_context)

                assert len(response.issues) == 0
                # 在這個測試中，服務實際上成功處理了請求，但 AtlassianClient 返回空結果
                # 這不算作失敗，因為 gRPC 服務本身沒有出錯
                assert service.stats["total_requests"] == 1
                assert service.stats["successful_requests"] == 1
        finally:
            await service.close_client()

    def test_convert_relationship_to_grpc(self, settings):
        """測試關係轉換為 gRPC 格式"""
        from mnemosyne.schemas.relationships import BaseRelationship, RelationshipType

        service = AtlassianKnowledgeExtractorService(settings)

        # 創建測試關係
        relationship = BaseRelationship(
            id="rel_test_123",
            source_id="jira_issue_DEMO-123",
            target_id="jira_project_DEMO",
            relationship_type=RelationshipType.BELONGS_TO,
            extra={"project_name": "DEMO"},
        )

        grpc_rel = service._convert_relationship_to_grpc(relationship)

        assert grpc_rel.id == "rel_test_123"
        assert grpc_rel.source_id == "jira_issue_DEMO-123"
        assert grpc_rel.target_id == "jira_project_DEMO"
        assert grpc_rel.type == atlassian_pb2.RelationshipType.BELONGS_TO
        assert grpc_rel.properties["project_name"] == "DEMO"
        assert grpc_rel.strength == 1.0
