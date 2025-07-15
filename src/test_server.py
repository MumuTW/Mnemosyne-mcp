#!/usr/bin/env python
"""
測試 gRPC 服務器

在 src 目錄中直接測試 gRPC 服務器。
"""

import asyncio
import logging
import sys
from concurrent import futures

import grpc

# 導入生成的 proto 模組
sys.path.insert(0, "mnemosyne/grpc/generated")
import mcp_pb2
import mcp_pb2_grpc


class MnemosyneMCPServicer(mcp_pb2_grpc.MnemosyneMCPServicer):
    """簡單的 MnemosyneMCP 服務實作"""

    async def Search(self, request, context):
        """搜索 RPC 實作"""
        print(
            f"✅ Search request received: '{request.query_text}' (top_k={request.top_k})"
        )

        # 返回模擬響應
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


async def serve():
    """啟動 gRPC 服務器"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    # 添加服務
    servicer = MnemosyneMCPServicer()
    mcp_pb2_grpc.add_MnemosyneMCPServicer_to_server(servicer, server)

    # 綁定地址
    listen_addr = "localhost:50051"
    server.add_insecure_port(listen_addr)

    print(f"🚀 Starting gRPC server on {listen_addr}")

    # 啟動服務器
    await server.start()
    print("✅ gRPC server started successfully")
    print("📡 Server is ready to accept connections")
    print("Press Ctrl+C to stop the server")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gRPC server...")
        await server.stop(grace=5)
        print("✅ gRPC server stopped")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)

    # 運行服務器
    asyncio.run(serve())
