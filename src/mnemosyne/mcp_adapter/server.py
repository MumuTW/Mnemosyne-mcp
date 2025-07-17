"""
Mnemosyne MCP Server - FastMCP Implementation

Mnemosyne MCP 伺服器主體，使用 FastMCP 框架提供標準的 Model Context Protocol 介面。
支援 stdio 傳輸，與 Claude Desktop 等 MCP 客戶端無縫整合。
"""

import asyncio
import sys
from typing import Optional

import structlog
from fastmcp import FastMCP

from ..core.config import Settings
from .grpc_bridge import GrpcBridge
from .tools import register_tools

logger = structlog.get_logger(__name__)


class MnemosyneMCPServer:
    """
    Mnemosyne MCP 伺服器

    整合 FastMCP 框架與 Mnemosyne gRPC 服務，提供：
    - 標準 MCP 協議支援 (JSON-RPC over stdio)
    - 完整的程式碼搜尋和影響分析功能
    - 健壯的錯誤處理和重試機制
    - 詳細的日誌記錄和監控
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化 MCP 伺服器

        Args:
            settings: 應用配置，如果為 None 則使用預設配置
        """
        self.settings = settings or Settings()
        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

        # 建立 FastMCP 伺服器
        self.mcp = FastMCP(name="Mnemosyne", version="0.1.0")

        # 建立 gRPC 橋接器
        self.grpc_bridge: Optional[GrpcBridge] = None

        # 伺服器狀態
        self._initialized = False
        self._running = False

        self.logger.info("MCP 伺服器初始化", name="Mnemosyne", version="0.1.0")

    async def initialize(self) -> None:
        """
        初始化 MCP 伺服器

        建立 gRPC 連線並註冊所有工具
        """
        if self._initialized:
            self.logger.warning("MCP 伺服器已經初始化")
            return

        try:
            self.logger.info("開始初始化 MCP 伺服器")

            # 建立並連線 gRPC 橋接器
            self.grpc_bridge = GrpcBridge(self.settings)
            await self.grpc_bridge.connect()

            # 註冊 MCP 工具
            register_tools(self.mcp, self.grpc_bridge)

            self._initialized = True
            self.logger.info("MCP 伺服器初始化成功")

        except Exception as e:
            self.logger.error("MCP 伺服器初始化失敗", error=str(e))
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """清理伺服器資源"""
        try:
            self.logger.info("開始清理 MCP 伺服器資源")

            if self.grpc_bridge:
                await self.grpc_bridge.disconnect()
                self.grpc_bridge = None

            self._initialized = False
            self._running = False

            self.logger.info("MCP 伺服器資源清理完成")

        except Exception as e:
            self.logger.error("清理 MCP 伺服器資源時發生錯誤", error=str(e))

    def run(self, transport: str = "stdio") -> None:
        """
        啟動 MCP 伺服器

        Args:
            transport: 傳輸方式，目前支援 "stdio"
        """
        if not self._initialized:
            raise RuntimeError("MCP 伺服器尚未初始化，請先呼叫 initialize()")

        try:
            self._running = True
            self.logger.info("啟動 MCP 伺服器", transport=transport)

            if transport == "stdio":
                # 使用 stdio 傳輸 (標準 MCP 方式)
                self.mcp.run()
            else:
                raise ValueError(f"不支援的傳輸方式: {transport}")

        except KeyboardInterrupt:
            self.logger.info("收到中斷信號，正在停止 MCP 伺服器")
        except Exception as e:
            self.logger.error("MCP 伺服器運行時發生錯誤", error=str(e))
            raise
        finally:
            self._running = False
            self.logger.info("MCP 伺服器已停止")

    async def run_async(self, transport: str = "stdio") -> None:
        """
        非同步啟動 MCP 伺服器

        Args:
            transport: 傳輸方式，目前支援 "stdio"
        """
        if not self._initialized:
            await self.initialize()

        try:
            self._running = True
            self.logger.info("非同步啟動 MCP 伺服器", transport=transport)

            if transport == "stdio":
                # 使用 stdio 傳輸的非同步版本
                await asyncio.to_thread(self.mcp.run)
            else:
                raise ValueError(f"不支援的傳輸方式: {transport}")

        except Exception as e:
            self.logger.error("非同步 MCP 伺服器運行時發生錯誤", error=str(e))
            raise
        finally:
            self._running = False
            await self.cleanup()

    def get_server_info(self) -> dict:
        """
        獲取伺服器資訊

        Returns:
            伺服器狀態和統計資訊
        """
        info = {
            "name": "Mnemosyne MCP Server",
            "version": "0.1.0",
            "initialized": self._initialized,
            "running": self._running,
            "transport": "stdio",
            "tools_count": 4,  # search_code, analyze_impact, health_status, get_system_info
            "tools": [
                "search_code",
                "analyze_impact",
                "health_status",
                "get_system_info",
            ],
        }

        # 如果橋接器可用，添加連線統計
        if self.grpc_bridge:
            info["grpc_stats"] = self.grpc_bridge.get_stats()

        return info


async def create_mcp_server(settings: Optional[Settings] = None) -> MnemosyneMCPServer:
    """
    工廠函數：建立並初始化 MCP 伺服器

    Args:
        settings: 應用配置

    Returns:
        已初始化的 MCP 伺服器實例
    """
    server = MnemosyneMCPServer(settings)
    await server.initialize()
    return server


async def main() -> None:
    """
    主程式入口點

    可以直接執行此檔案來啟動 MCP 伺服器：
    python -m mnemosyne.mcp_adapter.server
    """
    try:
        # 設定日誌格式 (for stdio mode)
        import logging

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,  # 將日誌輸出到 stderr，避免干擾 stdio 通訊
        )

        # 建立並啟動伺服器
        settings = Settings()
        server = await create_mcp_server(settings)

        logger.info("Mnemosyne MCP Server 準備就緒")

        # 啟動伺服器 (阻塞式)
        server.run()

    except KeyboardInterrupt:
        logger.info("收到中斷信號，伺服器正常退出")
    except Exception as e:
        logger.error("伺服器啟動失敗", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    # 直接執行此檔案啟動 MCP 伺服器
    asyncio.run(main())
