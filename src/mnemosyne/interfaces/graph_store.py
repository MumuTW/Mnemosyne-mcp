"""
GraphStoreClient 抽象介面定義

這個模組定義了圖資料庫操作的抽象介面，確保不同的圖資料庫驅動可以無縫替換。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ConnectionConfig:
    """資料庫連接配置"""

    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    connection_pool_size: int = 10
    connection_timeout: int = 30
    query_timeout: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "connection_pool_size": self.connection_pool_size,
            "connection_timeout": self.connection_timeout,
            "query_timeout": self.query_timeout,
        }


@dataclass
class QueryResult:
    """查詢結果封裝"""

    data: List[Dict[str, Any]]
    execution_time_ms: float
    query: str
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_empty(self) -> bool:
        """檢查結果是否為空"""
        return len(self.data) == 0

    @property
    def count(self) -> int:
        """返回結果數量"""
        return len(self.data)

    def first(self) -> Optional[Dict[str, Any]]:
        """返回第一個結果"""
        return self.data[0] if self.data else None


class GraphStoreClient(ABC):
    """
    圖資料庫客戶端抽象介面

    這個抽象類定義了所有圖資料庫驅動必須實現的核心方法。
    設計原則：
    1. 簡單性：只暴露必要的操作
    2. 一致性：所有驅動返回相同的數據結構
    3. 可觀測性：內建查詢追蹤和日誌
    4. 錯誤處理：統一的異常處理機制
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connected = False
        self._connection = None
        self.logger = structlog.get_logger(self.__class__.__name__)

    @abstractmethod
    async def connect(self) -> None:
        """
        建立資料庫連接

        Raises:
            ConnectionError: 連接失敗時拋出
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """關閉資料庫連接"""
        pass

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> QueryResult:
        """
        執行 Cypher 查詢

        Args:
            query: Cypher 查詢語句
            parameters: 查詢參數
            trace_id: 追蹤 ID，用於調試和監控

        Returns:
            QueryResult: 查詢結果

        Raises:
            QueryError: 查詢執行失敗時拋出
            ConnectionError: 連接問題時拋出
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """
        檢查資料庫連接狀態

        Returns:
            bool: 連接正常返回 True，否則返回 False
        """
        pass

    async def healthcheck(self) -> Dict[str, Any]:
        """
        執行健康檢查

        Returns:
            Dict: 包含連接狀態、版本信息等的健康檢查結果
        """
        try:
            start_time = datetime.now()
            is_connected = await self.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if is_connected:
                # 執行簡單查詢獲取版本信息
                result = await self.execute_query("RETURN 1 as test")

                return {
                    "status": "healthy",
                    "connected": True,
                    "response_time_ms": response_time,
                    "database": self.config.database,
                    "host": self.config.host,
                    "port": self.config.port,
                    "test_query_success": not result.is_empty,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "response_time_ms": response_time,
                    "database": self.config.database,
                    "host": self.config.host,
                    "port": self.config.port,
                    "error": "Connection failed",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "connected": False,
                "database": self.config.database,
                "host": self.config.host,
                "port": self.config.port,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @property
    def is_connected(self) -> bool:
        """檢查是否已連接"""
        return self._connected

    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.disconnect()


class GraphStoreError(Exception):
    """圖資料庫操作基礎異常"""

    pass


class ConnectionError(GraphStoreError):
    """連接相關異常"""

    pass


class QueryError(GraphStoreError):
    """查詢相關異常"""

    pass


class ConfigurationError(GraphStoreError):
    """配置相關異常"""

    pass
