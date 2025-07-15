"""
Mnemosyne MCP - gRPC 服務器實作

提供 MnemosyneMCP gRPC 服務的實作。
"""

import asyncio
import logging
from concurrent import futures

import grpc
import structlog

from .generated import mcp_pb2, mcp_pb2_grpc

logger = structlog.get_logger(__name__)


class MnemosyneMCPServicer(mcp_pb2_grpc.MnemosyneMCPServicer):
    """
    MnemosyneMCP gRPC 服務實作

    實作 Protocol Buffers 中定義的所有 RPC 方法。
    """

    def __init__(self, search_engine=None):
        """
        初始化服務器

        Args:
            search_engine: 搜索引擎實例，如果為 None 則使用模擬實作
        """
        self.search_engine = search_engine
        logger.info("MnemosyneMCP servicer initialized")

    async def Search(self, request, context):
        """
        搜索 RPC 實作

        Args:
            request: SearchRequest
            context: gRPC 上下文

        Returns:
            SearchResponse: 搜索結果
        """
        logger.info(
            "Search request received",
            query_text=request.query_text,
            top_k=request.top_k,
        )

        try:
            if self.search_engine:
                # 使用真實的搜索引擎
                result = await self.search_engine.search(
                    request.query_text, request.top_k
                )
                return result
            else:
                # 模擬實作，用於測試
                return mcp_pb2.SearchResponse(
                    summary=f"Mock search results for: {request.query_text}",
                    relevant_nodes=[
                        mcp_pb2.SearchResult(
                            node_id="mock-node-1",
                            node_type="Function",
                            content=f"Mock function related to: {request.query_text}",
                            similarity_score=0.95,
                            properties={"name": "mock_function", "file": "mock.py"},
                            labels=["Function", "Python"],
                        )
                    ],
                    suggested_next_step="Try refining your search query",
                )
        except Exception as e:
            logger.error("Search request failed", error=str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Search failed: {str(e)}")
            return mcp_pb2.SearchResponse()


async def start_grpc_server(
    host: str = "localhost",
    port: int = 50051,
    search_engine=None,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """
    啟動 gRPC 服務器

    Args:
        host: 服務器主機地址
        port: 服務器端口
        search_engine: 搜索引擎實例
        max_workers: 最大工作線程數

    Returns:
        grpc.aio.Server: gRPC 服務器實例
    """
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    # 添加服務
    servicer = MnemosyneMCPServicer(search_engine)
    mcp_pb2_grpc.add_MnemosyneMCPServicer_to_server(servicer, server)

    # 綁定地址
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)

    logger.info("Starting gRPC server", address=listen_addr)

    # 啟動服務器
    await server.start()
    logger.info("gRPC server started successfully")

    return server


async def main():
    """主函數，用於直接運行 gRPC 服務器"""
    server = await start_grpc_server()

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(grace=5)
        logger.info("gRPC server stopped")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)

    # 運行服務器
    asyncio.run(main())
