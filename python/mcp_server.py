#!/usr/bin/env python3
"""
Mnemosyne MCP Server Entry Point

This script serves as the main entry point for the Mnemosyne MCP server
when launched via the Node.js wrapper.
"""

import asyncio
import os
import sys
from pathlib import Path


def setup_python_path():
    """Setup Python path to include the Mnemosyne source code."""
    # 添加專案根目錄的 src 到 Python 路徑
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    src_path = project_root / "src"

    if src_path.exists():
        sys.path.insert(0, str(src_path))
        return True

    # 如果在開發環境中，src 可能在不同位置
    alt_src_path = project_root.parent / "src"
    if alt_src_path.exists():
        sys.path.insert(0, str(alt_src_path))
        return True

    return False


async def main():
    """Main entry point for the MCP server."""
    try:
        # 設置 Python 路徑
        if not setup_python_path():
            print("Error: Could not find Mnemosyne source code", file=sys.stderr)
            print("Please ensure the package is properly installed", file=sys.stderr)
            sys.exit(1)

        # 導入 Mnemosyne MCP 伺服器
        from mnemosyne.core.config import get_settings
        from mnemosyne.mcp_adapter.server import create_mcp_server

        # 獲取配置
        settings = get_settings()

        # 創建 MCP 伺服器
        server = await create_mcp_server(settings)

        # 啟動伺服器 (使用 stdio transport)
        server.run(transport="stdio")

    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        print("Please ensure all Python dependencies are installed", file=sys.stderr)
        print("Run: pip install -r python/requirements.txt", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        if os.getenv("MCP_DEBUG") == "true":
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 設置事件循環策略 (Windows 兼容性)
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # 運行主程式
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
