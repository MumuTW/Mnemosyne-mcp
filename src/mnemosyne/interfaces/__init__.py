"""
Mnemosyne MCP - 介面定義模組

這個模組包含了所有的抽象介面定義，確保系統的可擴展性和插件化架構。
"""

from .graph_store import GraphStoreClient, QueryResult, ConnectionConfig

__all__ = [
    "GraphStoreClient",
    "QueryResult", 
    "ConnectionConfig",
]
