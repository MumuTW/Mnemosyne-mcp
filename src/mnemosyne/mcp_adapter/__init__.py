"""
MCP Adapter for Mnemosyne - FastMCP Implementation

這個模組提供 Mnemosyne 與 Model Context Protocol (MCP) 的適配層，
使用 FastMCP 框架實作標準的 JSON-RPC over stdio 通訊協議。

架構設計：
- FastMCP 處理 MCP 協議細節
- GrpcBridge 橋接到現有 gRPC 服務
- 模組化設計，便於未來擴展或替換底層實作

主要組件：
- server.py: FastMCP 伺服器主體
- grpc_bridge.py: gRPC 服務橋接器
- tools.py: MCP 工具定義
- utils.py: 工具函數和裝飾器
"""

__version__ = "0.1.0"
__author__ = "Mnemosyne Team"

from .server import MnemosyneMCPServer

__all__ = ["MnemosyneMCPServer"]
