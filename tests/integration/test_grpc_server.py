"""
gRPC 伺服器整合測試

測試 gRPC 伺服器的完整啟動和基本功能。
"""

import asyncio

import grpc
import pytest

from mnemosyne.core.config import MCPAtlassianSettings, Settings
from mnemosyne.grpc import atlassian_pb2, atlassian_pb2_grpc
from mnemosyne.grpc.server import AtlassianGrpcServer


class TestAtlassianGrpcServer:
    """測試 AtlassianGrpcServer"""

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

    @pytest.mark.asyncio
    async def test_server_initialization(self, settings):
        """測試伺服器初始化"""
        server = AtlassianGrpcServer(settings, port=50052)

        assert server.settings == settings
        assert server.port == 50052
        assert server.server is None
        assert server.service is None

    @pytest.mark.asyncio
    async def test_server_start_stop(self, settings):
        """測試伺服器啟動和停止"""
        server = AtlassianGrpcServer(settings, port=50053)

        # 啟動伺服器
        await server.start()

        try:
            assert server.server is not None
            assert server.service is not None

            # 給伺服器一些時間來啟動
            await asyncio.sleep(0.1)

            # 測試基本的 gRPC 連接
            channel = grpc.insecure_channel("localhost:50053")
            stub = atlassian_pb2_grpc.AtlassianKnowledgeExtractorStub(channel)

            # 測試健康檢查
            request = atlassian_pb2.HealthCheckRequest(check_connectivity=False)
            response = stub.CheckHealth(request)

            assert response.status == atlassian_pb2.HealthCheckResponse.Status.HEALTHY
            assert response.message == "Service is running"

            # 關閉通道
            channel.close()

        finally:
            # 停止伺服器
            await server.stop()

    @pytest.mark.asyncio
    async def test_server_grpc_stats(self, settings):
        """測試伺服器 gRPC 統計端點"""
        server = AtlassianGrpcServer(settings, port=50054)

        # 啟動伺服器
        await server.start()

        try:
            # 給伺服器一些時間來啟動
            await asyncio.sleep(0.1)

            # 測試基本的 gRPC 連接
            channel = grpc.insecure_channel("localhost:50054")
            stub = atlassian_pb2_grpc.AtlassianKnowledgeExtractorStub(channel)

            # 測試統計端點
            request = atlassian_pb2.GetExtractionStatsRequest()
            response = stub.GetExtractionStats(request)

            assert response.total_requests == 0
            assert response.successful_requests == 0
            assert response.failed_requests == 0
            assert response.success_rate == 0.0

            # 關閉通道
            channel.close()

        finally:
            # 停止伺服器
            await server.stop()

    @pytest.mark.asyncio
    async def test_server_unconfigured_service(self):
        """測試未配置的服務"""
        # 創建未配置的設定
        unconfigured_settings = Settings(mcp_atlassian=MCPAtlassianSettings())

        server = AtlassianGrpcServer(unconfigured_settings, port=50055)

        # 啟動伺服器
        await server.start()

        try:
            # 給伺服器一些時間來啟動
            await asyncio.sleep(0.1)

            # 測試基本的 gRPC 連接
            channel = grpc.insecure_channel("localhost:50055")
            stub = atlassian_pb2_grpc.AtlassianKnowledgeExtractorStub(channel)

            # 測試健康檢查應該顯示不健康
            request = atlassian_pb2.HealthCheckRequest(check_connectivity=False)
            response = stub.CheckHealth(request)

            assert response.status == atlassian_pb2.HealthCheckResponse.Status.UNHEALTHY
            assert "not configured" in response.message

            # 關閉通道
            channel.close()

        finally:
            # 停止伺服器
            await server.stop()

    @pytest.mark.asyncio
    async def test_server_jira_extraction_unconfigured(self):
        """測試未配置時的 Jira 提取"""
        # 創建未配置的設定
        unconfigured_settings = Settings(mcp_atlassian=MCPAtlassianSettings())

        server = AtlassianGrpcServer(unconfigured_settings, port=50056)

        # 啟動伺服器
        await server.start()

        try:
            # 給伺服器一些時間來啟動
            await asyncio.sleep(0.1)

            # 測試基本的 gRPC 連接
            channel = grpc.insecure_channel("localhost:50056")
            stub = atlassian_pb2_grpc.AtlassianKnowledgeExtractorStub(channel)

            # 測試 Jira 提取應該返回錯誤
            request = atlassian_pb2.ExtractJiraIssuesRequest(query="test")

            try:
                response = stub.ExtractJiraIssues(request)
                # 應該返回空結果
                assert len(response.issues) == 0
            except grpc.RpcError as e:
                # 或者返回 gRPC 錯誤
                assert e.code() == grpc.StatusCode.UNAVAILABLE

            # 關閉通道
            channel.close()

        finally:
            # 停止伺服器
            await server.stop()
