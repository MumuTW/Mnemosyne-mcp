"""
AtlassianClient 契約測試

測試 AtlassianClient 與 MCP Atlassian 服務的 API 契約，
使用模擬伺服器確保測試的獨立性和穩定性。
"""

import pytest
from aioresponses import aioresponses

from mnemosyne.clients.atlassian import AtlassianClient
from mnemosyne.core.config import MCPAtlassianSettings
from tests.mocks.mcp_atlassian_mock import MCPAtlassianMockServer


class TestAtlassianClientContract:
    """測試 AtlassianClient 與 MCP Atlassian 的 API 契約"""

    @pytest.fixture
    def settings(self):
        """創建測試用配置"""
        return MCPAtlassianSettings(
            service_url="http://mcp-atlassian:8001",
            read_only_mode=True,
            enabled_tools=[
                "confluence_search",
                "jira_search",
                "jira_get_issue",
            ],
            jira_url="https://company.atlassian.net",
            jira_username="test@company.com",
            jira_api_token="test-token",
            confluence_url="https://company.atlassian.net/wiki",
            confluence_username="test@company.com",
            confluence_api_token="test-token",
        )

    @pytest.fixture
    def mock_server(self):
        """創建模擬伺服器"""
        return MCPAtlassianMockServer()

    @pytest.mark.asyncio
    async def test_client_initialization(self, settings):
        """測試客戶端初始化"""
        client = AtlassianClient(settings)

        assert client.settings == settings
        assert client._base_url == "http://mcp-atlassian:8001"
        assert client.is_configured is True
        assert client.request_count == 0
        assert client.error_count == 0

    @pytest.mark.asyncio
    async def test_health_check_success(self, settings, mock_server):
        """測試成功的健康檢查"""
        with aioresponses() as m:
            mock_server.setup_successful_responses(m)

            async with AtlassianClient(settings) as client:
                result = await client.health_check()

            assert result["status"] == "healthy"
            assert "response_time_ms" in result
            assert "data" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, settings, mock_server):
        """測試失敗的健康檢查"""
        with aioresponses() as m:
            mock_server.setup_error_responses(m)

            async with AtlassianClient(settings) as client:
                result = await client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_search_jira_issues_success(self, settings, mock_server):
        """測試成功的 Jira Issue 搜尋"""
        with aioresponses() as m:
            mock_server.setup_successful_responses(m)

            async with AtlassianClient(settings) as client:
                issues = await client.search_jira_issues("bug fix")

            assert len(issues) == 2
            assert issues[0].key == "DEMO-123"
            assert issues[0].summary == "修復登入功能錯誤"
            assert issues[1].key == "DEMO-124"
            assert issues[1].summary == "新增用戶註冊 API"

            # 驗證統計信息
            stats = client.get_stats()
            assert stats["request_count"] == 1
            assert stats["error_count"] == 0
            assert stats["success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_search_jira_issues_with_project_filter(self, settings, mock_server):
        """測試帶專案過濾器的 Jira Issue 搜尋"""
        with aioresponses() as m:
            # 設置自定義響應，驗證過濾器參數
            mock_server.setup_custom_response(
                m,
                "POST",
                "http://mcp-atlassian:8001/jira/search",
                200,
                mock_server.mock_data.create_jira_search_response(),
            )

            async with AtlassianClient(settings) as client:
                issues = await client.search_jira_issues("bug", project_filter="DEMO")

            assert len(issues) == 2

    @pytest.mark.asyncio
    async def test_search_jira_issues_tool_disabled(self, settings):
        """測試工具被禁用時的行為"""
        # 修改設定，禁用 jira_search
        settings.enabled_tools = ["confluence_search"]

        async with AtlassianClient(settings) as client:
            issues = await client.search_jira_issues("bug fix")

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_get_jira_issue_success(self, settings, mock_server):
        """測試成功獲取 Jira Issue"""
        with aioresponses() as m:
            mock_server.setup_successful_responses(m)

            async with AtlassianClient(settings) as client:
                issue = await client.get_jira_issue("DEMO-123")

            assert issue is not None
            assert issue.key == "DEMO-123"
            assert issue.summary == "示例 Jira Issue"
            assert issue.status == "In Progress"
            assert issue.priority == "Medium"

    @pytest.mark.asyncio
    async def test_get_jira_issue_not_found(self, settings, mock_server):
        """測試獲取不存在的 Jira Issue"""
        with aioresponses() as m:
            mock_server.setup_error_responses(m)

            async with AtlassianClient(settings) as client:
                issue = await client.get_jira_issue("NOTFOUND-999")

            assert issue is None

    @pytest.mark.asyncio
    async def test_search_confluence_pages_success(self, settings, mock_server):
        """測試成功的 Confluence 頁面搜尋"""
        with aioresponses() as m:
            mock_server.setup_successful_responses(m)

            async with AtlassianClient(settings) as client:
                pages = await client.search_confluence_pages("API")

            assert len(pages) == 2
            assert pages[0].title == "API 開發指南"
            assert pages[0].space == "DEV"
            assert pages[1].title == "系統架構設計"
            assert pages[1].space == "ARCH"

    @pytest.mark.asyncio
    async def test_search_confluence_pages_with_space_filter(
        self, settings, mock_server
    ):
        """測試帶空間過濾器的 Confluence 頁面搜尋"""
        with aioresponses() as m:
            mock_server.setup_custom_response(
                m,
                "POST",
                "http://mcp-atlassian:8001/confluence/search",
                200,
                mock_server.mock_data.create_confluence_search_response(),
            )

            async with AtlassianClient(settings) as client:
                pages = await client.search_confluence_pages("API", space_filter="DEV")

            assert len(pages) == 2

    @pytest.mark.asyncio
    async def test_search_confluence_pages_tool_disabled(self, settings):
        """測試工具被禁用時的行為"""
        # 修改設定，禁用 confluence_search
        settings.enabled_tools = ["jira_search"]

        async with AtlassianClient(settings) as client:
            pages = await client.search_confluence_pages("API")

        assert len(pages) == 0

    @pytest.mark.asyncio
    async def test_error_handling_and_statistics(self, settings, mock_server):
        """測試錯誤處理和統計信息"""
        with aioresponses() as m:
            # 設置錯誤響應
            mock_server.setup_error_responses(m)

            async with AtlassianClient(settings) as client:
                # 執行多次失敗的請求
                await client.search_jira_issues("test")
                await client.search_confluence_pages("test")
                await client.health_check()

                # 檢查統計信息
                stats = client.get_stats()
                assert stats["request_count"] == 3
                assert stats["error_count"] == 3
                assert stats["success_rate"] == 0.0
                assert stats["average_response_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self, settings):
        """測試會話未初始化的錯誤"""
        client = AtlassianClient(settings)

        with pytest.raises(RuntimeError, match="Client session not initialized"):
            await client._make_request("GET", "/health")

    @pytest.mark.asyncio
    async def test_data_validation_error_handling(self, settings):
        """測試數據驗證錯誤處理"""
        with aioresponses() as m:
            # 返回無效的 Jira Issue 數據
            invalid_data = {
                "issues": [
                    {
                        "id": "123",
                        # 缺少必需的 'key' 字段
                        "summary": "Test",
                        "status": "Open",
                    }
                ]
            }
            m.post(
                "http://mcp-atlassian:8001/jira/search",
                status=200,
                payload=invalid_data,
            )

            async with AtlassianClient(settings) as client:
                issues = await client.search_jira_issues("test")

            # 應該優雅地處理驗證錯誤，返回空列表
            assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_configuration_check(self):
        """測試配置檢查"""
        # 未配置的設定
        unconfigured_settings = MCPAtlassianSettings()
        client = AtlassianClient(unconfigured_settings)
        assert client.is_configured is False

        # 已配置的設定
        configured_settings = MCPAtlassianSettings(
            jira_url="https://company.atlassian.net",
            jira_username="test@company.com",
            jira_api_token="test-token",
        )
        client = AtlassianClient(configured_settings)
        assert client.is_configured is True
