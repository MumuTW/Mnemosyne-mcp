"""
ECL Loader 階段測試
"""

from unittest.mock import MagicMock

import pytest

from mnemosyne.ecl.loader import GraphLoader


class TestGraphLoader:
    """圖資料庫載入器測試"""

    def test_loader_initialization(self):
        """測試載入器初始化"""
        mock_driver = MagicMock()
        loader = GraphLoader(mock_driver)
        assert loader.driver == mock_driver

    @pytest.mark.asyncio
    async def test_load_empty_data(self):
        """測試載入空資料"""
        mock_driver = MagicMock()
        mock_driver.is_connected = True
        loader = GraphLoader(mock_driver)

        result = await loader.load_data([], [])

        assert result.functions_loaded == 0
        assert result.calls_loaded == 0
        assert result.errors == []
