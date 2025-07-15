"""
CLI 模組的 smoke test

測試 CLI 模組的基本功能和導入。
"""


import pytest


def test_cli_module_import():
    """測試 CLI 模組可以正常導入"""
    try:
        from mnemosyne.cli import main

        assert main is not None
    except ImportError as e:
        pytest.fail(f"CLI 模組導入失敗: {e}")


def test_cli_main_function_exists():
    """測試 CLI main 函數存在"""
    from mnemosyne.cli.main import main

    assert callable(main)


def test_cli_group_creation():
    """測試 CLI group 可以正常創建"""
    try:
        from mnemosyne.cli.main import cli

        assert cli is not None
        # 檢查是否是 click.Group 實例
        import click

        assert isinstance(cli, click.Group)
    except ImportError as e:
        pytest.fail(f"CLI group 創建失敗: {e}")


def test_cli_basic_functionality():
    """測試 CLI 基本功能"""
    from mnemosyne.cli.main import cli

    # 測試 CLI 群組的基本屬性
    assert cli is not None
    assert hasattr(cli, "commands")
    assert hasattr(cli, "name")


def test_cli_dependencies_import():
    """測試 CLI 依賴模組可以導入"""
    try:
        from mnemosyne.cli.main import get_settings, setup_logging

        assert get_settings is not None
        assert setup_logging is not None
    except ImportError as e:
        pytest.fail(f"CLI 依賴導入失敗: {e}")
