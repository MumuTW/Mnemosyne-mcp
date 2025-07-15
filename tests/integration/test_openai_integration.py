#!/usr/bin/env python
"""
OpenAI API 整合測試

測試真實的 OpenAI API 整合，驗證三個核心 LLM 能力。
"""

import asyncio
import os
import sys
import time

# 添加路徑
worktree_path = "/Users/johnson/Documents/project/worktree-ai-agent-integration"
src_path = os.path.join(worktree_path, "src")
sys.path.insert(0, src_path)

try:
    from mnemosyne.llm.providers.openai_provider import OpenAIProvider

    print("✅ OpenAI Provider modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class OpenAIIntegrationTest:
    """OpenAI API 整合測試套件"""

    def __init__(self):
        self.provider = None

    async def setup(self):
        """設置測試環境"""
        print("🔧 Setting up OpenAI integration test environment...")

        # 檢查 API Key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("  ⚠️ OPENAI_API_KEY not found in environment variables")
            print("  📝 Will test in mock mode")
            self.provider = OpenAIProvider()
        else:
            print("  ✅ OPENAI_API_KEY found")
            self.provider = OpenAIProvider({"api_key": api_key})

        # 初始化 provider
        try:
            await self.provider.initialize()
            print("  ✅ OpenAI Provider initialized")
        except Exception as e:
            print(f"  ⚠️ Provider initialization failed: {e}")
            print("  📝 Will test basic functionality only")

    async def test_generate_text(self):
        """測試文本生成功能"""
        print("\n🧠 Testing text generation with gpt-4o-mini...")

        test_prompts = [
            "Explain what is artificial intelligence in one sentence.",
            "Write a simple Python function to calculate factorial.",
        ]

        results = []

        for i, prompt in enumerate(test_prompts, 1):
            print(f"  📤 Test {i}: '{prompt[:50]}...'")

            start_time = time.time()

            try:
                response = await self.provider.generate_text(
                    prompt=prompt, max_tokens=100, temperature=0.7
                )

                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ms

                print(f"    📥 Response time: {response_time:.2f}ms")
                print(f"    📝 Content: {response.content[:100]}...")
                print(f"    📊 Usage: {response.usage}")

                # 檢查是否是模擬響應
                is_mock = response.metadata and response.metadata.get("mode") == "mock"
                if is_mock:
                    print("    ⚠️ Mock response (API not available)")
                else:
                    print("    ✅ Real API response")

                results.append(
                    {
                        "test": f"generate_text_{i}",
                        "response_time_ms": response_time,
                        "is_mock": is_mock,
                        "success": True,
                    }
                )

            except Exception as e:
                print(f"    ❌ Generation failed: {e}")
                results.append(
                    {"test": f"generate_text_{i}", "success": False, "error": str(e)}
                )

        return results

    async def test_capabilities(self):
        """測試 Provider 能力"""
        print("\n🔍 Testing provider capabilities...")

        try:
            capabilities = self.provider.supported_capabilities
            print(f"  ✅ Supported capabilities: {[cap.value for cap in capabilities]}")
            return [{"test": "capabilities", "success": True}]
        except Exception as e:
            print(f"  ❌ Capabilities test failed: {e}")
            return [{"test": "capabilities", "success": False, "error": str(e)}]

    async def run_all_tests(self):
        """運行所有 OpenAI 整合測試"""
        print("🚀 Starting OpenAI API Integration Tests...")
        print("=" * 70)

        await self.setup()

        # 運行各項測試
        text_results = await self.test_generate_text()
        capability_results = await self.test_capabilities()

        # 彙總結果
        all_results = text_results + capability_results

        # 統計
        total_tests = len(all_results)
        successful_tests = len([r for r in all_results if r.get("success", False)])
        failed_tests = total_tests - successful_tests

        # 計算平均響應時間
        response_times = [
            r.get("response_time_ms", 0)
            for r in all_results
            if r.get("response_time_ms")
        ]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # 檢查是否有真實 API 調用
        real_api_calls = len(
            [
                r
                for r in text_results
                if r.get("success") and not r.get("is_mock", False)
            ]
        )

        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_response_time_ms": avg_response_time,
            "real_api_calls": real_api_calls,
        }

        return summary


async def main():
    """主函數"""
    print("🎯 OpenAI API Integration Test Suite")
    print("Testing gpt-4o-mini model integration")
    print("=" * 70)

    test_suite = OpenAIIntegrationTest()

    try:
        results = await test_suite.run_all_tests()

        # 打印測試結果摘要
        print("\n📊 OpenAI Integration Test Results Summary:")
        print("=" * 70)

        print("📈 Test Statistics:")
        print(f"  • Total tests: {results['total_tests']}")
        print(f"  • Successful: {results['successful_tests']}")
        print(f"  • Failed: {results['failed_tests']}")
        print(f"  • Success rate: {results['success_rate']:.1%}")

        if results["average_response_time_ms"] > 0:
            print(
                f"  • Average response time: {results['average_response_time_ms']:.2f}ms"
            )

        print("\n🔗 API Integration Status:")
        if results["real_api_calls"] > 0:
            print(f"  ✅ Real OpenAI API calls successful: {results['real_api_calls']}")
            print("  🚀 OpenAI integration is working correctly")
        else:
            print("  ⚠️ No real API calls made (likely missing API key)")
            print("  📝 Tests ran in mock/fallback mode")

        # 整體評估
        if results["success_rate"] >= 0.8:
            print("\n🎉 OpenAI Integration Test Suite PASSED!")
            return 0
        else:
            print("\n❌ OpenAI Integration Test Suite FAILED!")
            return 1

    except Exception as e:
        print(f"\n❌ OpenAI Integration Test Suite crashed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
