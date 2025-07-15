"""
gRPC 伺服器啟動腳本

啟動 Atlassian 知識提取的 gRPC 伺服器。
"""

import asyncio
import logging
import signal
from concurrent import futures
from typing import Optional

import grpc

from mnemosyne.core.config import Settings
from mnemosyne.grpc.atlassian_service_simple import AtlassianKnowledgeExtractorService

from . import atlassian_pb2_grpc

logger = logging.getLogger(__name__)


class AtlassianGrpcServer:
    """Atlassian gRPC 伺服器"""

    def __init__(
        self,
        settings: Settings,
        port: int = 50051,
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
        self.service: Optional[AtlassianKnowledgeExtractorService] = None

    async def start(self) -> None:
        """啟動伺服器"""
        logger.info(f"Starting Atlassian gRPC server on port {self.port}")

        # 創建 gRPC 伺服器
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers)
        )

        # 創建服務實例
        self.service = AtlassianKnowledgeExtractorService(self.settings)
        await self.service.init_client()

        # 註冊服務
        atlassian_pb2_grpc.add_AtlassianKnowledgeExtractorServicer_to_server(
            self.service, self.server
        )

        # 設置監聽地址
        listen_addr = f"[::]:{self.port}"
        self.server.add_insecure_port(listen_addr)

        # 啟動伺服器
        self.server.start()
        logger.info(f"gRPC server started on {listen_addr}")

    async def stop(self) -> None:
        """停止伺服器"""
        if self.server:
            logger.info("Stopping gRPC server...")
            self.server.stop(grace=5)

        if self.service:
            await self.service.close_client()

        logger.info("gRPC server stopped")

    async def wait_for_termination(self) -> None:
        """等待伺服器終止"""
        if self.server:
            self.server.wait_for_termination()


async def serve(settings: Settings, port: int = 50051) -> None:
    """
    啟動 gRPC 伺服器

    Args:
        settings: 應用配置
        port: 伺服器端口
    """
    server = AtlassianGrpcServer(settings, port)

    # 設置信號處理
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start()

        # 等待停止信號
        await stop_event.wait()

    finally:
        await server.stop()


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 載入配置
    settings = Settings()

    # 啟動伺服器
    asyncio.run(serve(settings))
