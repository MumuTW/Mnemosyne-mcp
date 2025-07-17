#!/usr/bin/env python3
"""
MCP 協議相容性測試腳本

測試 Mnemosyne MCP 伺服器是否正確實作 Model Context Protocol 規範。
這個腳本模擬 MCP 客戶端，透過 stdio 與伺服器通訊。
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

# 測試案例定義
TEST_CASES = [
    {
        "name": "tools_list",
        "description": "列出可用工具",
        "request": {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        "expected_tools": [
            "search_code",
            "analyze_impact",
            "health_status",
            "get_system_info",
        ],
    },
    {
        "name": "tool_call_health",
        "description": "呼叫健康檢查工具",
        "request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "health_status", "arguments": {}},
        },
        "expected_contains": ["Mnemosyne", "系統"],
    },
    {
        "name": "tool_call_system_info",
        "description": "呼叫系統資訊工具",
        "request": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_system_info", "arguments": {}},
        },
        "expected_contains": ["Mnemosyne MCP", "工具"],
    },
    {
        "name": "tool_call_search",
        "description": "呼叫程式碼搜尋工具",
        "request": {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_code",
                "arguments": {"query": "test function", "limit": 5},
            },
        },
        "expected_contains": ["搜尋"],
    },
    {
        "name": "invalid_tool",
        "description": "呼叫不存在的工具",
        "request": {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        },
        "expect_error": True,
    },
]


class MCPTester:
    """MCP 協議測試器"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.test_results: List[Dict[str, Any]] = []

    async def start_mcp_server(self, timeout: float = 10.0) -> bool:
        """啟動 MCP 伺服器"""
        try:
            print("🚀 啟動 MCP 伺服器...")

            # 啟動伺服器進程
            cmd = [sys.executable, "-m", "mnemosyne.cli.main", "serve-mcp"]
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
            )

            # 等待伺服器初始化
            print("⏳ 等待伺服器初始化...")
            time.sleep(3)  # 使用同步 sleep 避免 asyncio 問題

            # 檢查進程是否正常運行
            if self.process.poll() is not None:
                stderr_output = (
                    self.process.stderr.read() if self.process.stderr else ""
                )
                print("❌ 伺服器啟動失敗")
                print(f"錯誤輸出: {stderr_output}")
                return False

            print("✅ MCP 伺服器啟動成功")
            return True

        except Exception as e:
            print(f"❌ 啟動 MCP 伺服器失敗: {e}")
            return False

    def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """發送 JSON-RPC 請求"""
        if not self.process or not self.process.stdin:
            return None

        try:
            # 發送請求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # 讀取回應
            response_line = self.process.stdout.readline()
            if not response_line:
                return None

            return json.loads(response_line.strip())

        except Exception as e:
            print(f"❌ 請求發送失敗: {e}")
            return None

    def validate_response(
        self, test_case: Dict[str, Any], response: Dict[str, Any]
    ) -> bool:
        """驗證回應是否符合預期"""
        try:
            # 基本 JSON-RPC 格式檢查
            if "jsonrpc" not in response or response["jsonrpc"] != "2.0":
                print("   ❌ 錯誤的 JSON-RPC 版本")
                return False

            if "id" not in response or response["id"] != test_case["request"]["id"]:
                print("   ❌ ID 不匹配")
                return False

            # 檢查錯誤預期
            if test_case.get("expect_error"):
                if "error" in response:
                    print("   ✅ 正確返回錯誤")
                    return True
                else:
                    print("   ❌ 預期錯誤但返回成功")
                    return False

            # 檢查成功回應
            if "result" not in response:
                print("   ❌ 缺少 result 欄位")
                return False

            # 特定內容檢查
            if "expected_tools" in test_case:
                tools = response["result"].get("tools", [])
                tool_names = [tool["name"] for tool in tools]
                for expected_tool in test_case["expected_tools"]:
                    if expected_tool not in tool_names:
                        print(f"   ❌ 缺少預期工具: {expected_tool}")
                        return False
                print(f"   ✅ 找到所有預期工具: {tool_names}")

            if "expected_contains" in test_case:
                content = str(response["result"])
                for expected_text in test_case["expected_contains"]:
                    if expected_text not in content:
                        print(f"   ❌ 回應中缺少預期文字: {expected_text}")
                        return False
                print("   ✅ 回應包含所有預期內容")

            return True

        except Exception as e:
            print(f"   ❌ 驗證過程發生錯誤: {e}")
            return False

    async def run_test_case(self, test_case: Dict[str, Any]) -> bool:
        """執行單個測試案例"""
        print(f"\n📋 測試: {test_case['name']} - {test_case['description']}")

        try:
            # 發送請求
            response = self.send_request(test_case["request"])

            if response is None:
                print("   ❌ 沒有收到回應")
                return False

            # 驗證回應
            is_valid = self.validate_response(test_case, response)

            # 記錄結果
            self.test_results.append(
                {
                    "name": test_case["name"],
                    "description": test_case["description"],
                    "success": is_valid,
                    "request": test_case["request"],
                    "response": response,
                }
            )

            return is_valid

        except Exception as e:
            print(f"   ❌ 測試執行失敗: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試案例"""
        print("🧪 開始 MCP 協議相容性測試")
        print("=" * 50)

        # 啟動伺服器
        if not await self.start_mcp_server():
            return {"success": False, "error": "伺服器啟動失敗"}

        try:
            # 執行測試案例
            passed = 0
            total = len(TEST_CASES)

            for test_case in TEST_CASES:
                success = await self.run_test_case(test_case)
                if success:
                    passed += 1

                # 短暫延遲避免過快請求
                time.sleep(0.5)

            # 生成報告
            success_rate = (passed / total) * 100

            print("\n" + "=" * 50)
            print("📊 測試結果摘要")
            print(f"   總測試數: {total}")
            print(f"   通過數: {passed}")
            print(f"   失敗數: {total - passed}")
            print(f"   成功率: {success_rate:.1f}%")

            if passed == total:
                print("🎉 所有測試通過！MCP 協議相容性良好")
            else:
                print("⚠️ 部分測試失敗，請檢查實作")

            return {
                "success": passed == total,
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": success_rate,
                "test_results": self.test_results,
            }

        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理資源"""
        if self.process:
            try:
                print("\n🧹 清理測試環境...")
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                print(f"⚠️ 清理過程警告: {e}")
                try:
                    self.process.kill()
                except Exception:
                    pass


async def main():
    """主測試函數"""
    tester = MCPTester()

    try:
        results = await tester.run_all_tests()

        # 根據測試結果設定退出碼
        exit_code = 0 if results.get("success", False) else 1

        return exit_code

    except KeyboardInterrupt:
        print("\n👋 測試被用戶中斷")
        return 1
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        return 1


if __name__ == "__main__":
    # 執行測試
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
