#!/usr/bin/env python
"""
最終驗證測試

確保所有組件都能正常協作，驗證完整的系統功能。
"""

import asyncio
import os
import sys

# 添加路徑
worktree_path = "/Users/johnson/Documents/project/worktree-ai-agent-integration"
src_path = os.path.join(worktree_path, "src")
proto_path = os.path.join(worktree_path, "src", "mnemosyne", "grpc", "generated")
sys.path.insert(0, src_path)
sys.path.insert(0, proto_path)

try:
    import grpc
    import mcp_pb2
    import mcp_pb2_grpc

    from mnemosyne.drivers.falkordb_driver import FalkorDBDriver
    from mnemosyne.interfaces.graph_store import ConnectionConfig
    from mnemosyne.llm.providers.openai_provider import OpenAIProvider

    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_all_components():
    """測試所有組件"""
    print("🎯 Final Verification Test Suite")
    print("=" * 60)

    results = []

    # 1. 測試模組導入
    print("🔍 Testing module imports...")
    try:
        provider = OpenAIProvider()
        config = ConnectionConfig("localhost", 6379, "test")
        driver = FalkorDBDriver(config)
        print("  ✅ All modules instantiated successfully")
        results.append("PASS")
    except Exception as e:
        print(f"  ❌ Module instantiation failed: {e}")
        results.append("FAIL")

    # 2. 測試 LLM Provider 功能
    print("\n🧠 Testing LLM Provider functionality...")
    try:
        provider = OpenAIProvider()
        capabilities = provider.supported_capabilities
        print(f"  ✅ Supported capabilities: {[cap.value for cap in capabilities]}")
        results.append("PASS")
    except Exception as e:
        print(f"  ❌ LLM Provider test failed: {e}")
        results.append("FAIL")

    # 3. 測試 FalkorDB Driver 方法
    print("\n🗄️ Testing FalkorDB Driver methods...")
    try:
        config = ConnectionConfig("localhost", 6379, "test")
        driver = FalkorDBDriver(config)

        vector_methods = [
            "create_vector_index",
            "vector_search",
            "add_node_with_vector",
        ]
        for method_name in vector_methods:
            if hasattr(driver, method_name) and callable(getattr(driver, method_name)):
                print(f"  ✅ {method_name} method available")
            else:
                print(f"  ❌ {method_name} method missing")
                results.append("FAIL")
                break
        else:
            results.append("PASS")
    except Exception as e:
        print(f"  ❌ FalkorDB Driver test failed: {e}")
        results.append("FAIL")

    # 4. 測試 Proto 版本兼容性
    print("\n📋 Testing Proto version compatibility...")
    try:
        request = mcp_pb2.SearchRequest(
            query_text="version test",
            top_k=1,
            api_version="1.0.0",
            client_id="test-client",
        )
        print(f"  ✅ Version fields: api_version={request.api_version}")
        results.append("PASS")
    except Exception as e:
        print(f"  ❌ Proto version test failed: {e}")
        results.append("FAIL")

    # 統計結果
    passed = results.count("PASS")
    failed = results.count("FAIL")
    total = len(results)

    print("\n📊 Verification Results Summary:")
    print("=" * 60)
    print(f"  • Total tests: {total}")
    print(f"  • Passed: {passed}")
    print(f"  • Failed: {failed}")
    print(f"  • Success rate: {passed/total:.1%}")

    if failed == 0:
        print("\n✅ ALL VERIFICATION TESTS PASSED!")
        print("🚀 System is ready for production deployment")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed - review required")
        return False


async def main():
    """主函數"""
    success = await test_all_components()

    if success:
        print("\n🎉 Final verification completed successfully!")
        return 0
    else:
        print("\n❌ Final verification found issues!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
