"""
MCP 主服務 gRPC 伺服器

啟動和管理 MnemosyneMCP 主服務的 gRPC 伺服器。
"""

import asyncio
import logging
import signal
from concurrent import futures
from typing import Optional

import grpc
import structlog

from ..core.config import Settings
from .generated import mcp_pb2_grpc
from .mcp_service import MnemosyneMCPService

logger = structlog.get_logger(__name__)


class MCPGrpcServer:
    """MCP 主服務 gRPC 伺服器"""

    def __init__(
        self,
        settings: Settings,
        port: int = 50052,  # 使用不同的端口避免與 Atlassian 服務衝突
        max_workers: int = 10,
    ):
        """
        初始化 gRPC 伺服器

        Args:
            settings: 應用配置
            port: 伺服器端口
            max_workers: 最大工作線程數
        """
        self.settings = settings
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[grpc.Server] = None
        self.service: Optional[MnemosyneMCPService] = None
        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

    async def start(self) -> None:
        """啟動伺服器"""
        self.logger.info("Starting MCP gRPC server", port=self.port)

        try:
            # 創建 gRPC 伺服器
            self.server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers)
            )

            # 創建服務實例
            self.service = MnemosyneMCPService(self.settings)
            await self.service.initialize()

            # 註冊服務
            mcp_pb2_grpc.add_MnemosyneMCPServicer_to_server(self.service, self.server)

            # 設置監聽地址
            listen_addr = f"[::]:{self.port}"
            self.server.add_insecure_port(listen_addr)

            # 啟動伺服器
            self.server.start()
            self.logger.info("MCP gRPC server started", address=listen_addr)

        except Exception as e:
            self.logger.error("Failed to start MCP gRPC server", error=str(e))
            raise

    async def stop(self) -> None:
        """停止伺服器"""
        self.logger.info("Stopping MCP gRPC server")

        try:
            if self.server:
                self.logger.info("Stopping gRPC server...")
                await asyncio.to_thread(self.server.stop, grace=5)

            if self.service:
                await self.service.cleanup()

            self.logger.info("MCP gRPC server stopped")

        except Exception as e:
            self.logger.error("Error during server shutdown", error=str(e))

    async def wait_for_termination(self) -> None:
        """等待伺服器終止"""
        if self.server:
            await asyncio.to_thread(self.server.wait_for_termination)

    def get_server_stats(self) -> dict:
        """獲取伺服器統計信息"""
        if self.service:
            return {
                "server_port": self.port,
                "max_workers": self.max_workers,
                "service_stats": self.service.get_service_stats(),
            }
        return {"server_port": self.port, "max_workers": self.max_workers}


async def serve_mcp(settings: Settings, port: int = 50052) -> None:
    """
    啟動 MCP gRPC 伺服器

    Args:
        settings: 應用配置
        port: 伺服器端口
    """
    server = MCPGrpcServer(settings, port)

    # 設置信號處理
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info("Received signal, shutting down MCP server", signal=signum)
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start()

        # 等待停止信號
        await stop_event.wait()

    except Exception as e:
        logger.error("MCP server error", error=str(e))
        raise
    finally:
        await server.stop()


class CombinedGrpcServer:
    """
    組合的 gRPC 伺服器

    同時運行 MCP 主服務和 Atlassian 服務。
    """

    def __init__(self, settings: Settings):
        """
        初始化組合伺服器

        Args:
            settings: 應用配置
        """
        self.settings = settings
        self.mcp_server = MCPGrpcServer(settings, port=50052)

        # 導入 Atlassian 服務（如果需要）
        try:
            from .server import AtlassianGrpcServer

            self.atlassian_server = AtlassianGrpcServer(settings, port=50051)
        except ImportError:
            self.atlassian_server = None
            logger.warning("Atlassian gRPC server not available")

        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

    async def start_all(self) -> None:
        """啟動所有服務"""
        self.logger.info("Starting combined gRPC servers")

        try:
            # 啟動 MCP 主服務
            await self.mcp_server.start()

            # 啟動 Atlassian 服務（如果可用）
            if self.atlassian_server:
                await self.atlassian_server.start()

            self.logger.info("All gRPC servers started successfully")

        except Exception as e:
            self.logger.error("Failed to start combined servers", error=str(e))
            await self.stop_all()
            raise

    async def stop_all(self) -> None:
        """停止所有服務"""
        self.logger.info("Stopping combined gRPC servers")

        try:
            # 停止 MCP 主服務
            await self.mcp_server.stop()

            # 停止 Atlassian 服務（如果可用）
            if self.atlassian_server:
                await self.atlassian_server.stop()

            self.logger.info("All gRPC servers stopped")

        except Exception as e:
            self.logger.error("Error during combined server shutdown", error=str(e))

    async def wait_for_termination(self) -> None:
        """等待所有伺服器終止"""
        tasks = []

        # 等待 MCP 服務
        if self.mcp_server.server:
            tasks.append(asyncio.create_task(self.mcp_server.wait_for_termination()))

        # 等待 Atlassian 服務
        if self.atlassian_server and self.atlassian_server.server:
            tasks.append(
                asyncio.create_task(self.atlassian_server.wait_for_termination())
            )

        if tasks:
            await asyncio.gather(*tasks)


async def serve_combined(settings: Settings) -> None:
    """
    啟動組合的 gRPC 伺服器

    Args:
        settings: 應用配置
    """
    server = CombinedGrpcServer(settings)

    # 設置信號處理
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info("Received signal, shutting down combined servers", signal=signum)
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start_all()

        # 等待停止信號
        await stop_event.wait()

    except Exception as e:
        logger.error("Combined server error", error=str(e))
        raise
    finally:
        await server.stop_all()


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 載入配置
    settings = Settings()

    # 啟動組合伺服器
    asyncio.run(serve_combined(settings))
