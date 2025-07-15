"""
MCP Atlassian 健康檢查功能測試
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError

from mnemosyne.api.main import check_mcp_atlassian_health


class TestMCPAtlassianHealth:
    """測試 MCP Atlassian 健康檢查功能"""

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_success(self):
        """測試成功的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        # Mock aiohttp ClientSession
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "healthy"
        assert result["url"] == test_url
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_http_error(self):
        """測試 HTTP 錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        # Mock aiohttp ClientSession with error status
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "HTTP 500" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_connection_error(self):
        """測試連接錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        # Mock aiohttp ClientSession with connection error
        mock_session = AsyncMock()
        mock_session.get.side_effect = ClientError("Connection refused")

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_unexpected_error(self):
        """測試意外錯誤的健康檢查"""
        test_url = "http://mcp-atlassian:8001"

        # Mock aiohttp ClientSession with unexpected error
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Unexpected error")

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await check_mcp_atlassian_health(test_url)

        assert result["status"] == "unhealthy"
        assert result["url"] == test_url
        assert "Unexpected error" in result["error"]

    @pytest.mark.asyncio
    async def test_check_mcp_atlassian_health_timeout(self):
        """測試超時配置"""
        test_url = "http://mcp-atlassian:8001"
        timeout = 3

        mock_response = AsyncMock()
        mock_response.status = 200

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session) as mock_client:
            with patch("aiohttp.ClientTimeout") as mock_timeout:
                await check_mcp_atlassian_health(test_url, timeout)

                # 驗證 timeout 設置
                mock_timeout.assert_called_once_with(total=timeout)
                mock_client.assert_called_once_with(timeout=mock_timeout.return_value)
