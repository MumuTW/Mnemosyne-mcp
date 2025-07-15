"""
Logging 模組的 smoke test

測試 Logging 模組的基本功能。
"""

from unittest.mock import MagicMock, patch

import pytest


def test_logging_module_import():
    """測試 Logging 模組可以正常導入"""
    try:
        from mnemosyne.core import logging as mnemosyne_logging

        assert mnemosyne_logging is not None
    except ImportError as e:
        pytest.fail(f"Logging 模組導入失敗: {e}")


def test_get_logger_function():
    """測試 get_logger 函數"""
    from mnemosyne.core.logging import get_logger

    logger = get_logger("test_logger")
    assert logger is not None
    # structlog 返回的是 BoundLoggerLazyProxy，不是標準的 logging.Logger
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_setup_logging_function_exists():
    """測試 setup_logging 函數存在"""
    from mnemosyne.core.logging import setup_logging

    assert callable(setup_logging)


@patch("mnemosyne.core.logging.logging.basicConfig")
def test_setup_logging_basic(mock_basic_config):
    """測試基本的 logging 設置"""
    from mnemosyne.core.logging import setup_logging

    # 測試基本調用不會拋出異常
    try:
        setup_logging(level="INFO", format_type="simple")
        mock_basic_config.assert_called()
    except Exception as e:
        pytest.fail(f"setup_logging 基本調用失敗: {e}")


def test_logging_middleware_import():
    """測試 LoggingMiddleware 可以導入"""
    try:
        from mnemosyne.core.logging import LoggingMiddleware

        assert LoggingMiddleware is not None
    except ImportError as e:
        pytest.fail(f"LoggingMiddleware 導入失敗: {e}")


def test_logging_middleware_creation():
    """測試 LoggingMiddleware 可以創建"""
    from mnemosyne.core.logging import LoggingMiddleware

    # 創建一個模擬的 app
    mock_app = MagicMock()

    try:
        middleware = LoggingMiddleware(mock_app)
        assert middleware is not None
        assert middleware.app == mock_app
    except Exception as e:
        pytest.fail(f"LoggingMiddleware 創建失敗: {e}")


def test_logger_levels():
    """測試不同的日誌級別"""
    from mnemosyne.core.logging import get_logger

    logger = get_logger("test_levels")

    # 測試不同級別的日誌方法存在
    assert hasattr(logger, "debug")
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "critical")


@patch("mnemosyne.core.logging.structlog")
def test_structured_logging_setup(mock_structlog):
    """測試結構化日誌設置"""
    from mnemosyne.core.logging import setup_logging

    # 模擬 structlog
    mock_structlog.configure = MagicMock()

    try:
        setup_logging(level="INFO", format_type="json")
        # 如果使用 structlog，應該會調用 configure
        # 這裡只是確保不會拋出異常
    except Exception as e:
        # 如果 structlog 不可用，這是可以接受的
        if "structlog" not in str(e):
            pytest.fail(f"結構化日誌設置失敗: {e}")


def test_logging_config_validation():
    """測試日誌配置驗證"""
    from mnemosyne.core.logging import setup_logging

    # 測試有效的配置
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    valid_formats = ["simple", "json"]

    for level in valid_levels:
        for format_type in valid_formats:
            try:
                setup_logging(level=level, format_type=format_type)
            except Exception as e:
                pytest.fail(f"有效配置 {level}/{format_type} 失敗: {e}")
