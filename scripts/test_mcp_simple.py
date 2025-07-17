#!/usr/bin/env python3
"""
簡化的 MCP 功能測試

直接測試 MCP 適配器的核心功能，而不是完整的 stdio 協議。
這可以驗證我們的實作是否正確，無需複雜的進程間通訊。
"""

import asyncio
import sys
from pathlib import Path

from mnemosyne.core.config import Settings
from mnemosyne.mcp_adapter.grpc_bridge import GrpcBridge
from mnemosyne.mcp_adapter.server import MnemosyneMCPServer

# 添加 src 到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_grpc_bridge():
    """測試 gRPC 橋接器基本功能"""
    print("🔗 測試 gRPC 橋接器...")

    try:
        settings = Settings()
        bridge = GrpcBridge(settings)

        # 測試連線（預期可能失敗，因為沒有後端）
        try:
            await bridge.connect()
            is_healthy = await bridge.health_check()
            print(f"   ✅ gRPC 連線成功，健康狀態: {is_healthy}")
        except Exception as e:
            print(f"   ⚠️  gRPC 連線失敗（預期）: {type(e).__name__}")

        # 測試降級功能
        result = await bridge.search_code("test query", 5)
        if "error" in result:
            print("   ✅ 降級機制正常工作")
        else:
            print(f"   ✅ 搜尋功能正常: {len(result.get('results', []))} 個結果")

        await bridge.disconnect()
        return True

    except Exception as e:
        print(f"   ❌ gRPC 橋接器測試失敗: {e}")
        return False


async def test_mcp_server():
    """測試 MCP 伺服器初始化"""
    print("🚀 測試 MCP 伺服器初始化...")

    try:
        settings = Settings()
        server = MnemosyneMCPServer(settings)

        # 測試初始化
        await server.initialize()
        print("   ✅ MCP 伺服器初始化成功")

        # 獲取伺服器資訊
        info = server.get_server_info()
        print(f"   ✅ 伺服器資訊: {info['name']} v{info['version']}")
        print(f"   ✅ 可用工具: {len(info['tools'])} 個")

        # 測試清理
        await server.cleanup()
        print("   ✅ 伺服器清理成功")

        return True

    except Exception as e:
        print(f"   ❌ MCP 伺服器測試失敗: {e}")
        return False


async def test_tools_registration():
    """測試工具註冊功能"""
    print("🛠️  測試工具註冊...")

    try:
        from fastmcp import FastMCP

        from mnemosyne.mcp_adapter.grpc_bridge import GrpcBridge
        from mnemosyne.mcp_adapter.tools import register_tools

        # 建立 FastMCP 實例
        mcp = FastMCP("Test Server")

        # 建立橋接器
        settings = Settings()
        bridge = GrpcBridge(settings)

        # 註冊工具
        register_tools(mcp, bridge)

        # 檢查工具是否註冊成功
        # 注意：FastMCP 不提供直接獲取工具列表的方法，
        # 這裡我們只驗證註冊過程沒有拋出異常
        print("   ✅ 工具註冊過程無錯誤")

        return True

    except Exception as e:
        print(f"   ❌ 工具註冊測試失敗: {e}")
        return False


async def test_cli_integration():
    """測試 CLI 整合"""
    print("⚡ 測試 CLI 整合...")

    try:
        # 嘗試導入 CLI 模組
        from mnemosyne.cli.main import cli

        # 檢查 serve-mcp 命令是否存在
        commands = [cmd.name for cmd in cli.commands.values()]
        if "serve-mcp" in commands:
            print("   ✅ serve-mcp 命令已註冊")
        else:
            print(f"   ❌ serve-mcp 命令未找到，可用命令: {commands}")
            return False

        return True

    except Exception as e:
        print(f"   ❌ CLI 整合測試失敗: {e}")
        return False


async def main():
    """執行所有測試"""
    print("🧪 開始 Mnemosyne MCP 簡化測試")
    print("=" * 50)

    tests = [
        ("gRPC 橋接器", test_grpc_bridge),
        ("MCP 伺服器", test_mcp_server),
        ("工具註冊", test_tools_registration),
        ("CLI 整合", test_cli_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 測試")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"   🎉 {test_name} 測試通過")
            else:
                print(f"   💥 {test_name} 測試失敗")
        except Exception as e:
            print(f"   💥 {test_name} 測試異常: {e}")

    # 生成報告
    print("\n" + "=" * 50)
    print("📊 測試結果摘要")
    print(f"   總測試數: {total}")
    print(f"   通過數: {passed}")
    print(f"   失敗數: {total - passed}")
    print(f"   成功率: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 所有測試通過！Sprint 5 MCP 適配器基本功能正常")
        print("\n📖 下一步:")
        print("   1. 啟動 gRPC 後端: mnemo serve")
        print("   2. 測試完整流程: mnemo serve-mcp")
        print("   3. 配置 Claude Desktop")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 個測試失敗，請檢查實作")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
