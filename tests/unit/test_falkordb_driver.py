"""
FalkorDB 驅動測試

測試 FalkorDBDriver 的基本功能。
"""

from unittest.mock import Mock, patch

import pytest

from mnemosyne.drivers.falkordb_driver import FalkorDBDriver
from mnemosyne.interfaces.graph_store import ConnectionConfig, ConnectionError


@pytest.mark.unit
class TestFalkorDBDriver:
    """測試 FalkorDBDriver 類"""

    def test_driver_initialization(self):
        """測試驅動初始化"""
        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)

        assert driver.config == config
        assert not driver.is_connected
        assert driver._client is None
        assert driver._graph is None

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_falkordb):
        """測試成功連接"""
        # 設置 mock
        mock_client = Mock()
        mock_graph = Mock()
        mock_result = Mock()
        mock_result.result_set = [[1]]
        mock_result.header = ["test"]

        mock_falkordb.FalkorDB.return_value = mock_client
        mock_client.select_graph.return_value = mock_graph
        mock_graph.query.return_value = mock_result

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)

        # 測試連接
        await driver.connect()

        assert driver.is_connected
        assert driver._client == mock_client
        assert driver._graph == mock_graph

        # 驗證調用
        mock_falkordb.FalkorDB.assert_called_once_with(
            host="localhost", port=6379, username=None, password=None
        )
        mock_client.select_graph.assert_called_once_with("test")
        mock_graph.query.assert_called_once_with("RETURN 1 as test")

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_falkordb):
        """測試連接失敗"""
        # 設置 mock 拋出異常
        mock_falkordb.FalkorDB.side_effect = Exception("Connection failed")

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)

        # 測試連接失敗
        with pytest.raises(ConnectionError, match="Failed to connect to FalkorDB"):
            await driver.connect()

        assert not driver.is_connected

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_execute_query_success(self, mock_falkordb):
        """測試查詢執行成功"""
        # 設置 mock
        mock_client = Mock()
        mock_graph = Mock()
        mock_result = Mock()
        mock_result.result_set = [[1]]
        mock_result.header = ["test"]
        mock_result.nodes_created = 0
        mock_result.relationships_created = 0

        mock_falkordb.FalkorDB.return_value = mock_client
        mock_client.select_graph.return_value = mock_graph
        mock_graph.query.return_value = mock_result

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)
        await driver.connect()

        # 執行查詢
        result = await driver.execute_query("RETURN 1")

        assert not result.is_empty
        assert result.count == 1
        assert result.query == "RETURN 1"
        assert result.execution_time_ms > 0
        assert len(result.data) == 1

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_ping_success(self, mock_falkordb):
        """測試 ping 成功"""
        # 設置 mock
        mock_client = Mock()
        mock_graph = Mock()
        mock_result = Mock()
        mock_result.result_set = [[1]]
        mock_result.header = ["1"]

        mock_falkordb.FalkorDB.return_value = mock_client
        mock_client.select_graph.return_value = mock_graph
        mock_graph.query.return_value = mock_result

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)
        await driver.connect()

        # 測試 ping
        is_alive = await driver.ping()

        assert is_alive is True

    @pytest.mark.asyncio
    async def test_ping_not_connected(self):
        """測試未連接時的 ping"""
        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)

        # 測試未連接時的 ping
        is_alive = await driver.ping()

        assert is_alive is False

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_falkordb):
        """測試斷開連接"""
        # 設置 mock
        mock_client = Mock()
        mock_graph = Mock()
        mock_result = Mock()
        mock_result.result_set = [[1]]
        mock_result.header = ["test"]

        mock_falkordb.FalkorDB.return_value = mock_client
        mock_client.select_graph.return_value = mock_graph
        mock_graph.query.return_value = mock_result

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)
        await driver.connect()

        assert driver.is_connected

        # 測試斷開連接
        await driver.disconnect()

        assert not driver.is_connected
        assert driver._client is None
        assert driver._graph is None
        mock_client.close.assert_called_once()

    @patch("mnemosyne.drivers.falkordb_driver.falkordb")
    @pytest.mark.asyncio
    async def test_healthcheck(self, mock_falkordb):
        """測試健康檢查"""
        # 設置 mock
        mock_client = Mock()
        mock_graph = Mock()
        mock_result = Mock()
        mock_result.result_set = [[1]]
        mock_result.header = ["test"]

        mock_falkordb.FalkorDB.return_value = mock_client
        mock_client.select_graph.return_value = mock_graph
        mock_graph.query.return_value = mock_result

        config = ConnectionConfig(host="localhost", port=6379, database="test")

        driver = FalkorDBDriver(config)
        await driver.connect()

        # 測試健康檢查
        health = await driver.healthcheck()

        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["database"] == "test"
        assert health["host"] == "localhost"
        assert health["port"] == 6379
        assert "response_time_ms" in health
        assert "timestamp" in health
