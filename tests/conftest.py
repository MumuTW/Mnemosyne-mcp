"""
Pytest 配置和共享 fixtures

提供測試所需的共享配置和 fixtures。
"""

import asyncio
from typing import AsyncGenerator, Generator
# Unused imports removed by linter

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from mnemosyne.api.main import app, get_current_settings, get_graph_client
from mnemosyne.core.config import Settings
from mnemosyne.interfaces.graph_store import (
    ConnectionConfig,
    GraphStoreClient,
    QueryResult,
)


class MockGraphStoreClient(GraphStoreClient):
    """模擬圖資料庫客戶端，用於測試"""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._mock_data = {}
        self._connected = False

    async def connect(self) -> None:
        """模擬連接"""
        self._connected = True

    async def disconnect(self) -> None:
        """模擬斷開連接"""
        self._connected = False

    async def execute_query(
        self, query: str, parameters=None, trace_id=None
    ) -> QueryResult:
        """模擬查詢執行"""
        # 模擬簡單的測試查詢
        if "RETURN 1" in query:
            return QueryResult(
                data=[{"test": 1}],
                execution_time_ms=1.0,
                query=query,
                parameters=parameters,
            )

        return QueryResult(
            data=[], execution_time_ms=1.0, query=query, parameters=parameters
        )

    async def ping(self) -> bool:
        """模擬 ping"""
        return self._connected


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """創建事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """測試配置"""
    from mnemosyne.core.config import APISettings, DatabaseSettings, LoggingSettings

    return Settings(
        environment="testing",
        database=DatabaseSettings(
            host="localhost", port=6379, database="test_mnemosyne"
        ),
        api=APISettings(host="127.0.0.1", port=8001),
        logging=LoggingSettings(level="DEBUG"),
    )


@pytest_asyncio.fixture
async def mock_graph_client(
    test_settings,
) -> AsyncGenerator[MockGraphStoreClient, None]:
    """模擬圖資料庫客戶端 fixture"""
    config = test_settings.database.to_connection_config()
    client = MockGraphStoreClient(config)
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
def test_client(test_settings, mock_graph_client) -> TestClient:
    """測試客戶端 fixture"""

    # 覆蓋依賴
    app.dependency_overrides[get_current_settings] = lambda: test_settings
    app.dependency_overrides[get_graph_client] = lambda: mock_graph_client

    client = TestClient(app)

    yield client

    # 清理依賴覆蓋
    app.dependency_overrides.clear()


@pytest.fixture
def sample_file_entity():
    """示例文件實體"""
    from mnemosyne.schemas.core import File

    return File(
        name="main.py",
        path="/app/main.py",
        extension=".py",
        language="python",
        hash="abc123def456",
    )


@pytest.fixture
def sample_function_entity():
    """示例函數實體"""
    from mnemosyne.schemas.core import Function

    return Function(
        name="main",
        file_path="/app/main.py",
        line_start=1,
        line_end=10,
        parameters=["args", "kwargs"],
        is_async=False,
    )


@pytest.fixture
def sample_calls_relationship():
    """示例調用關係"""
    from mnemosyne.schemas.relationships import CallsRelationship

    return CallsRelationship(
        source_id="func_001", target_id="func_002", call_type="direct", call_line=5
    )


# 標記配置
pytest_plugins = []


# 測試標記
def pytest_configure(config):
    """配置 pytest 標記"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


# 測試收集配置
def pytest_collection_modifyitems(config, items):
    """修改測試收集"""
    for item in items:
        # 為所有測試添加適當的標記
        if (
            "unit" not in item.keywords
            and "integration" not in item.keywords
            and "e2e" not in item.keywords
        ):
            item.add_marker(pytest.mark.unit)


# 異步測試配置
@pytest.fixture(scope="session")
def anyio_backend():
    """配置 anyio 後端"""
    return "asyncio"
