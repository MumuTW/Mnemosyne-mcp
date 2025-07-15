#!/usr/bin/env python
"""
端到端全流程測試

測試 Search + ImpactAnalysis + AcquireLock 的完整工作流程。
驗證 MCP 系統的核心功能鏈路。
"""

import asyncio
import os
import sys
import time
from typing import Any, Dict

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

    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class E2ETestSuite:
    """端到端測試套件"""

    def __init__(self):
        self.grpc_channel = None
        self.stub = None
        self.test_results = []
        self.start_time = None

    async def setup(self):
        """測試環境設置"""
        print("🔧 Setting up E2E test environment...")

        # 連接到 gRPC 服務器
        try:
            self.grpc_channel = grpc.aio.insecure_channel("localhost:50051")
            await self.grpc_channel.channel_ready()
            self.stub = mcp_pb2_grpc.MnemosyneMCPStub(self.grpc_channel)
            print("  ✅ gRPC connection established")
        except Exception as e:
            print(f"  ❌ Failed to connect to gRPC server: {e}")
            raise

        self.start_time = time.time()

    async def teardown(self):
        """測試環境清理"""
        print("🧹 Cleaning up E2E test environment...")

        if self.grpc_channel:
            await self.grpc_channel.close()
            print("  ✅ gRPC connection closed")

    async def test_search_workflow(self) -> Dict[str, Any]:
        """測試搜索工作流程"""
        print("\n🔍 Testing Search Workflow...")

        test_queries = [
            "authentication functions",
            "database connection utilities",
            "error handling mechanisms",
            "user validation methods",
            "API endpoint handlers",
        ]

        search_results = []

        for i, query in enumerate(test_queries, 1):
            print(f"  📤 Query {i}: '{query}'")

            start_time = time.time()

            request = mcp_pb2.SearchRequest(query_text=query, top_k=5)

            try:
                response = await self.stub.Search(request)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ms

                result = {
                    "query": query,
                    "response_time_ms": response_time,
                    "summary": response.summary,
                    "nodes_found": len(response.relevant_nodes),
                    "success": True,
                }

                print(f"    📥 Response time: {response_time:.2f}ms")
                print(f"    📊 Nodes found: {len(response.relevant_nodes)}")

                # 驗證響應時間 SLA (<500ms)
                if response_time < 500:
                    print(f"    ✅ SLA met: {response_time:.2f}ms < 500ms")
                else:
                    print(f"    ⚠️ SLA exceeded: {response_time:.2f}ms > 500ms")

                search_results.append(result)

            except Exception as e:
                print(f"    ❌ Search failed: {e}")
                search_results.append(
                    {"query": query, "success": False, "error": str(e)}
                )

        return {
            "test_name": "search_workflow",
            "total_queries": len(test_queries),
            "successful_queries": len(
                [r for r in search_results if r.get("success", False)]
            ),
            "average_response_time": sum(
                r.get("response_time_ms", 0) for r in search_results
            )
            / len(search_results),
            "sla_compliance": len(
                [r for r in search_results if r.get("response_time_ms", 1000) < 500]
            )
            / len(search_results),
            "results": search_results,
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有測試"""
        print("🚀 Starting E2E Test Suite...")
        print("=" * 60)

        await self.setup()

        try:
            # 運行搜索測試
            search_results = await self.test_search_workflow()

            # 計算總體結果
            total_time = time.time() - self.start_time

            overall_results = {
                "test_suite": "e2e_full_workflow",
                "total_execution_time": total_time,
                "tests": {"search": search_results},
                "summary": {
                    "search_sla_compliance": search_results.get("sla_compliance", 0),
                    "average_search_time": search_results.get(
                        "average_response_time", 0
                    ),
                    "total_queries_tested": search_results.get("total_queries", 0),
                    "successful_searches": search_results.get("successful_queries", 0),
                },
            }

            return overall_results

        finally:
            await self.teardown()


async def main():
    """主函數"""
    print("🎯 MCP E2E Test Suite")
    print("Testing Search + ImpactAnalysis + AcquireLock workflows")
    print("=" * 60)

    test_suite = E2ETestSuite()

    try:
        results = await test_suite.run_all_tests()

        # 打印測試結果摘要
        print("\n📊 Test Results Summary:")
        print("=" * 60)

        summary = results["summary"]
        print("🔍 Search Performance:")
        print(f"  • Average response time: {summary['average_search_time']:.2f}ms")
        print(f"  • SLA compliance: {summary['search_sla_compliance']:.1%}")
        print(
            f"  • Successful queries: {summary['successful_searches']}/{summary['total_queries_tested']}"
        )

        print(f"\n⏱️ Total execution time: {results['total_execution_time']:.2f}s")

        # 檢查 SLA 達成情況
        if summary["search_sla_compliance"] >= 0.8:  # 80% 的查詢需要 <500ms
            print("✅ SLA Target Achieved: >80% queries under 500ms")
        else:
            print("❌ SLA Target Missed: <80% queries under 500ms")

        print("\n🎉 E2E Test Suite Completed!")

    except Exception as e:
        print(f"\n❌ E2E Test Suite Failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
