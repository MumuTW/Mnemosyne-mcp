"""
MCP Adapter 工具函數

提供 MCP 工具的通用功能，包括錯誤處理、日誌記錄、效能監控等。
"""

import functools
import time
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


def mcp_tool_wrapper(func: Callable) -> Callable:
    """
    MCP 工具的通用錯誤處理裝飾器

    提供：
    - 統一的錯誤處理和日誌記錄
    - 執行時間監控
    - 優雅的錯誤回應格式
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        start_time = time.time()
        tool_name = func.__name__

        try:
            logger.info(
                "MCP tool execution started",
                tool=tool_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                "MCP tool executed successfully",
                tool=tool_name,
                duration_ms=round(duration * 1000, 2),
                result_length=len(str(result)) if result else 0,
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "MCP tool execution failed",
                tool=tool_name,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
            )

            # 返回用戶友好的錯誤訊息
            return f"⚠️ 工具 '{tool_name}' 執行失敗: {str(e)}"

    return wrapper


def format_search_results(results: list, total: int, summary: str) -> str:
    """
    格式化搜尋結果為用戶友好的顯示格式

    Args:
        results: 搜尋結果列表
        total: 總結果數
        summary: 搜尋摘要

    Returns:
        格式化的搜尋結果字串
    """
    if not results:
        return f"❌ 沒有找到相關結果\n📋 摘要: {summary}"

    # 限制顯示結果數量，避免輸出過長
    display_results = results[:5]

    formatted_items = []
    for i, item in enumerate(display_results, 1):
        content_preview = item.get("content", "")
        if len(content_preview) > 200:
            content_preview = content_preview[:200] + "..."

        formatted_items.append(
            f"{i}. 📁 {item.get('type', 'Unknown')}: {item.get('id', 'N/A')}\n"
            f"   💯 相似度: {item.get('score', 0):.2f}\n"
            f"   📝 內容: {content_preview}"
        )

    result_text = f"🔍 搜尋結果 (顯示前 {len(display_results)} 個，共 {total} 個結果):\n\n"
    result_text += "\n\n".join(formatted_items)
    result_text += f"\n\n📋 摘要: {summary}"

    if total > len(display_results):
        result_text += f"\n\n💡 提示: 還有 {total - len(display_results)} 個結果未顯示"

    return result_text


def format_impact_analysis(result: dict) -> str:
    """
    格式化影響分析結果為用戶友好的顯示格式

    Args:
        result: 影響分析結果字典

    Returns:
        格式化的影響分析字串
    """
    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "UNKNOWN": "⚪"}

    risk_level = result.get("risk_level", "UNKNOWN")
    risk_icon = risk_emoji.get(risk_level, "⚪")

    impact_text = "🎯 影響力分析結果:\n\n"
    impact_text += f"{risk_icon} 風險等級: {risk_level}\n"
    impact_text += f"📊 影響節點數: {result.get('impact_nodes', 0)}\n\n"
    impact_text += f"📝 分析摘要:\n{result.get('summary', '無摘要資訊')}"

    return impact_text


def validate_tool_params(**validators) -> Callable:
    """
    參數驗證裝飾器

    Args:
        **validators: 參數名稱到驗證函數的映射

    Returns:
        裝飾器函數
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 驗證參數
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    try:
                        validator(kwargs[param_name])
                    except Exception as e:
                        raise ValueError(f"參數 '{param_name}' 驗證失敗: {str(e)}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def validate_non_empty_string(value: Any) -> None:
    """驗證非空字串"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("必須是非空字串")


def validate_positive_integer(value: Any) -> None:
    """驗證正整數"""
    if not isinstance(value, int) or value <= 0:
        raise ValueError("必須是正整數")


def validate_query_length(value: str, max_length: int = 1000) -> None:
    """驗證查詢字串長度"""
    if len(value) > max_length:
        raise ValueError(f"查詢字串長度不能超過 {max_length} 字元")
