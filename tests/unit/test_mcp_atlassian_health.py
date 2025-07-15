"""
MCP Atlassian 健康檢查功能測試
"""

import pytest
from aiohttp import ClientError
from aioresponses import aioresponses

from mnemosyne.api.main import check_mcp_atlassian_health


class TestMCPAtlassianHealth:
    """測試 MCP Atlassian 健康檢查功能"""

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_success(self):
        """測試成功的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        with aioresponses() as m:
            m.get(f"{test_url}/health", status=200, payload={"status": "ok"})

            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "healthy"
        assert result["url"] == test_url
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_http_error(self):
        """測試 HTTP 錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        with aioresponses() as m:
            m.get(
                f"{test_url}/health",
                status=500,
                payload={"error": "Internal Server Error"},
            )

            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "HTTP 500" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_connection_error(self):
        """測試連接錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        with aioresponses() as m:
            m.get(f"{test_url}/health", exception=ClientError("Connection refused"))

            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_unexpected_error(self):
        """測試意外錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        with aioresponses() as m:
            m.get(f"{test_url}/health", exception=Exception("Unexpected error"))

            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "Unexpected error" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_timeout(self):
        """測試超時配置"""
        test_url = "http://mcp-atlassian:8001"
        timeout = 3

        with aioresponses() as m:
            m.get(f"{test_url}/health", status=200, payload={"status": "ok"})

            result = await check_mcp_atlassian_health(test_url, timeout)

        assert result["status"] == "healthy"
        assert result["url"] == test_url
        assert "response_time_ms" in result
