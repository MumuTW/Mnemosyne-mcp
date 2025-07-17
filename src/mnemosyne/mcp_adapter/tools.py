"""
FastMCP 工具定義

定義 Mnemosyne MCP 提供的所有工具，使用 FastMCP 框架註冊到 MCP 伺服器。
每個工具都包含詳細的文檔和參數驗證。
"""

import structlog
from fastmcp import FastMCP

from .grpc_bridge import GrpcBridge
from .utils import (
    format_impact_analysis,
    format_search_results,
    mcp_tool_wrapper,
    validate_non_empty_string,
    validate_positive_integer,
    validate_query_length,
    validate_tool_params,
)

logger = structlog.get_logger(__name__)


def register_tools(mcp: FastMCP, bridge: GrpcBridge) -> None:
    """
    註冊所有 MCP 工具到 FastMCP 伺服器

    Args:
        mcp: FastMCP 伺服器實例
        bridge: gRPC 橋接器實例
    """

    @mcp.tool()
    @mcp_tool_wrapper
    @validate_tool_params(
        query=lambda x: (validate_non_empty_string(x), validate_query_length(x)),
        limit=validate_positive_integer,
    )
    async def search_code(query: str, limit: int = 10) -> str:
        """
        在 Mnemosyne 知識圖譜中搜尋程式碼

        這個工具可以幫助您找到與特定查詢相關的程式碼片段、函數、類別或檔案。
        它使用語義搜尋技術，能理解自然語言查詢並返回最相關的結果。

        Args:
            query: 搜尋查詢 (自然語言或關鍵字)
                  例如：「處理用戶登入的函數」、「database connection」、「error handling」
            limit: 返回結果的最大數量 (1-50，預設 10)

        Returns:
            格式化的搜尋結果，包含相關程式碼片段、檔案位置和相似度分數

        Examples:
            - search_code("user authentication functions", 5)
            - search_code("SQL query builders", 15)
            - search_code("錯誤處理機制")
        """
        try:
            # 參數範圍驗證
            limit = max(1, min(limit, 50))  # 限制在合理範圍內

            logger.info("執行程式碼搜尋", query=query, limit=limit)

            # 呼叫 gRPC 服務
            result = await bridge.search_code(query, limit)

            # 格式化回應
            return format_search_results(
                results=result["results"],
                total=result["total"],
                summary=result["summary"],
            )

        except Exception as e:
            logger.error("程式碼搜尋失敗", query=query, error=str(e))
            return f"⚠️ 搜尋失敗: {str(e)}"

    @mcp.tool()
    @mcp_tool_wrapper
    @validate_tool_params(project_id=validate_non_empty_string)
    async def analyze_impact(project_id: str, pr_number: str = "") -> str:
        """
        分析程式碼變更的影響範圍和風險等級

        這個工具分析特定 Pull Request 或程式碼變更對整個專案的潛在影響，
        幫助開發者和審核者了解變更的風險和範圍。

        Args:
            project_id: 專案識別符
                       例如：「my-web-app」、「backend-api」、「mobile-client」
            pr_number: Pull Request 編號 (選填)
                      例如：「123」、「pr-456」
                      如果不提供，將分析最新的變更

        Returns:
            詳細的影響分析報告，包含風險等級、影響的元件數量和建議

        Examples:
            - analyze_impact("backend-api", "123")
            - analyze_impact("web-frontend")  # 分析最新變更
            - analyze_impact("mobile-app", "pr-456")
        """
        try:
            logger.info(
                "執行影響分析", project_id=project_id, pr_number=pr_number or "latest"
            )

            # 呼叫 gRPC 服務
            result = await bridge.analyze_impact(project_id, pr_number)

            # 格式化回應
            return format_impact_analysis(result)

        except Exception as e:
            logger.error(
                "影響分析失敗", project_id=project_id, pr_number=pr_number, error=str(e)
            )
            return f"⚠️ 影響分析失敗: {str(e)}"

    @mcp.tool()
    @mcp_tool_wrapper
    async def health_status() -> str:
        """
        檢查 Mnemosyne 系統的健康狀態

        這個工具檢查系統各個組件的運行狀態，包括：
        - gRPC 服務連線狀態
        - 資料庫連線狀態
        - 系統效能指標
        - 最近的錯誤統計

        Returns:
            系統健康狀態報告

        Examples:
            - health_status()  # 簡單的健康檢查
        """
        try:
            logger.info("執行系統健康檢查")

            # 執行健康檢查
            is_healthy = await bridge.health_check()

            # 獲取統計資訊
            stats = bridge.get_stats()

            if is_healthy:
                status_text = "✅ **Mnemosyne 系統運行正常**\n\n"
                status_text += "🔗 **連線狀態:**\n"
                status_text += f"   • gRPC 服務: {stats['connection_status']}\n"
                status_text += f"   • 總請求數: {stats['total_requests']}\n"
                status_text += f"   • 成功率: {stats['success_rate']}%\n"
                status_text += f"   • 健康檢查次數: {stats['health_checks']}\n\n"

                if stats["failed_requests"] > 0:
                    status_text += f"⚠️ **注意**: 有 {stats['failed_requests']} 個失敗的請求\n"

                status_text += "💡 **系統就緒，可以處理查詢和分析請求**"
            else:
                status_text = "❌ **Mnemosyne 系統異常**\n\n"
                status_text += "🔗 **連線狀態:**\n"
                status_text += f"   • gRPC 服務: {stats['connection_status']}\n"
                status_text += f"   • 連線錯誤數: {stats['connection_errors']}\n"
                status_text += f"   • 失敗請求數: {stats['failed_requests']}\n\n"
                status_text += "🔧 **建議動作:**\n"
                status_text += "   1. 檢查 gRPC 服務是否運行\n"
                status_text += "   2. 驗證網路連線\n"
                status_text += "   3. 查看系統日誌獲取詳細錯誤資訊"

            return status_text

        except Exception as e:
            logger.error("健康檢查失敗", error=str(e))
            return f"⚠️ 健康檢查失敗: {str(e)}"

    @mcp.tool()
    @mcp_tool_wrapper
    async def get_system_info() -> str:
        """
        獲取 Mnemosyne 系統資訊和使用說明

        這個工具提供系統的基本資訊、功能概覽和使用指南。

        Returns:
            系統資訊和使用說明
        """
        try:
            info_text = """🚀 **Mnemosyne MCP - 智能程式碼知識圖譜**

📋 **系統概覽:**
Mnemosyne 是一個主動的、有狀態的軟體知識圖譜引擎，專為 AI 代理和開發者協作而設計。
它使用圖資料庫技術和語義搜尋，幫助您快速理解和導航大型程式碼庫。

🛠️ **可用工具:**

1. **search_code** - 程式碼搜尋
   • 使用自然語言或關鍵字搜尋相關程式碼
   • 支援語義理解，能找到概念相關的程式碼
   • 範例: `search_code("user authentication", 10)`

2. **analyze_impact** - 影響分析
   • 分析程式碼變更對專案的影響範圍
   • 評估變更風險等級 (LOW/MEDIUM/HIGH)
   • 範例: `analyze_impact("my-project", "PR-123")`

3. **health_status** - 系統健康檢查
   • 檢查所有系統組件的運行狀態
   • 提供效能統計和錯誤資訊
   • 範例: `health_status()`

4. **get_system_info** - 系統資訊 (當前工具)
   • 顯示系統概覽和使用說明

💡 **使用建議:**
- 搜尋時使用描述性的查詢，例如「處理付款的函數」而不只是「payment」
- 影響分析適合在程式碼審核時使用，幫助評估變更風險
- 定期使用健康檢查確保系統運行正常

🔗 **技術架構:**
- gRPC-First 設計，確保高效能和可靠性
- FastMCP 協議適配，與 Claude Desktop 等客戶端無縫整合
- FalkorDB 圖資料庫，提供強大的圖查詢能力

📞 **需要幫助?**
使用任何工具時，您都會收到詳細的回饋和建議。如果遇到問題，請先執行 `health_status()` 檢查系統狀態。
"""

            logger.info("提供系統資訊")
            return info_text

        except Exception as e:
            logger.error("獲取系統資訊失敗", error=str(e))
            return f"⚠️ 無法獲取系統資訊: {str(e)}"

    # 記錄工具註冊完成
    tools_registered = [
        "search_code",
        "analyze_impact",
        "health_status",
        "get_system_info",
    ]
    logger.info("MCP 工具註冊完成", tools_count=len(tools_registered), tools=tools_registered)
