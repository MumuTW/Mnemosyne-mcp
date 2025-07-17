"""
gRPC Bridge for MCP Adapter

提供 FastMCP 與 gRPC 服務之間的橋接功能，處理協議轉換和連線管理。
"""

import asyncio
from typing import Any, Dict, Optional

import grpc
import structlog

from ..core.config import Settings
from ..grpc.generated import mcp_pb2, mcp_pb2_grpc

logger = structlog.get_logger(__name__)


class GrpcBridge:
    """
    FastMCP 與 gRPC 服務的橋接器

    負責：
    - 管理 gRPC 連線和連線池
    - 處理 JSON 參數到 Protobuf 訊息的轉換
    - 提供錯誤處理和重試機制
    - 實作健康檢查和監控
    """

    def __init__(self, settings: Settings):
        """
        初始化 gRPC 橋接器

        Args:
            settings: 應用配置
        """
        self.settings = settings
        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

        # gRPC 連線相關
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[mcp_pb2_grpc.MnemosyneMCPStub] = None
        self._connection_lock = asyncio.Lock()
        self._is_connected = False

        # 重試和超時配置
        self.max_retries = 3
        self.timeout_seconds = 30.0
        self.health_check_timeout = 2.0

        # 統計資訊
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "connection_errors": 0,
            "health_checks": 0,
        }

    async def connect(self) -> None:
        """連接到 gRPC 服務"""
        async with self._connection_lock:
            if self._is_connected:
                return

            try:
                # 建立 gRPC 頻道
                grpc_host = getattr(self.settings, "grpc_host", "localhost")
                grpc_port = getattr(self.settings, "grpc_port", 50052)
                server_address = f"{grpc_host}:{grpc_port}"

                self.logger.info("Connecting to gRPC service", address=server_address)

                # 設置連線選項以提升可靠性
                options = [
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 5000),
                    ("grpc.keepalive_permit_without_calls", True),
                    ("grpc.http2.max_pings_without_data", 0),
                    ("grpc.http2.min_time_between_pings_ms", 10000),
                    ("grpc.http2.min_ping_interval_without_data_ms", 300000),
                ]

                self.channel = grpc.aio.insecure_channel(
                    server_address, options=options
                )
                self.stub = mcp_pb2_grpc.MnemosyneMCPStub(self.channel)

                # 測試連線
                await self.health_check()

                self._is_connected = True
                self.logger.info("gRPC bridge connected successfully")

            except Exception as e:
                self.stats["connection_errors"] += 1
                self.logger.error("Failed to connect to gRPC service", error=str(e))
                await self._cleanup_connection()
                raise

    async def disconnect(self) -> None:
        """斷開 gRPC 連線"""
        async with self._connection_lock:
            await self._cleanup_connection()

    async def _cleanup_connection(self) -> None:
        """清理連線資源"""
        try:
            if self.channel:
                await self.channel.close()
        except Exception as e:
            self.logger.warning("Error closing gRPC channel", error=str(e))
        finally:
            self.channel = None
            self.stub = None
            self._is_connected = False

    async def _ensure_connected(self) -> None:
        """確保 gRPC 連線可用"""
        if not self._is_connected:
            await self.connect()

    async def health_check(self) -> bool:
        """
        精確的健康檢查 - 只測試 gRPC 通道

        Returns:
            True 如果服務健康，False 否則
        """
        self.stats["health_checks"] += 1

        try:
            if not self.stub:
                return False

            request = mcp_pb2.HealthCheckRequest()
            response = await self.stub.HealthCheck(
                request, timeout=self.health_check_timeout
            )

            is_healthy = response.status == mcp_pb2.HealthCheckResponse.Status.SERVING

            if is_healthy:
                self.logger.debug("gRPC health check passed")
            else:
                self.logger.warning(
                    "gRPC service reports unhealthy", message=response.message
                )

            return is_healthy

        except grpc.RpcError as e:
            self.logger.error(
                "gRPC health check failed",
                code=e.code().name if e.code() else "UNKNOWN",
                details=e.details(),
            )
            return False
        except Exception as e:
            self.logger.error("Unexpected health check error", error=str(e))
            return False

    async def search_code(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        搜尋程式碼

        Args:
            query: 搜尋查詢字串
            limit: 最大結果數量

        Returns:
            搜尋結果字典
        """
        self.stats["total_requests"] += 1

        try:
            await self._ensure_connected()

            # 建立 gRPC 請求
            request = mcp_pb2.SearchRequest(query_text=query, top_k=limit)

            # 執行搜尋
            response = await self.stub.Search(request, timeout=self.timeout_seconds)

            # 轉換回應格式
            result = {
                "summary": response.summary,
                "results": [
                    {
                        "id": node.node_id,
                        "type": node.node_type,
                        "content": node.content,
                        "score": node.similarity_score,
                        "properties": dict(node.properties) if node.properties else {},
                        "labels": list(node.labels) if node.labels else [],
                    }
                    for node in response.relevant_nodes
                ],
                "total": len(response.relevant_nodes),
                "suggested_next_step": response.suggested_next_step,
            }

            self.stats["successful_requests"] += 1
            self.logger.info(
                "Search completed successfully",
                query=query,
                results_count=len(result["results"]),
            )

            return result

        except grpc.RpcError as e:
            self.stats["failed_requests"] += 1
            self.logger.error(
                "gRPC search failed",
                query=query,
                code=e.code().name if e.code() else "UNKNOWN",
                details=e.details(),
            )

            return {
                "summary": "搜尋服務暫時無法使用",
                "results": [],
                "total": 0,
                "error": f"gRPC Error: {e.code().name if e.code() else 'UNKNOWN'}",
                "error_details": e.details(),
            }
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error("Unexpected search error", query=query, error=str(e))

            return {
                "summary": "搜尋過程中發生未預期的錯誤",
                "results": [],
                "total": 0,
                "error": str(e),
            }

    async def analyze_impact(
        self, project_id: str, pr_number: str = ""
    ) -> Dict[str, Any]:
        """
        分析程式碼變更的影響範圍

        Args:
            project_id: 專案 ID
            pr_number: Pull Request 編號

        Returns:
            影響分析結果字典
        """
        self.stats["total_requests"] += 1

        try:
            await self._ensure_connected()

            # 建立 gRPC 請求
            request = mcp_pb2.ImpactAnalysisRequest(
                project_id=project_id, pr_number=pr_number or "latest"
            )

            # 執行影響分析
            response = await self.stub.RunImpactAnalysis(request, timeout=60.0)

            # 轉換回應格式
            result = {
                "summary": response.summary,
                "risk_level": response.risk_level.name,
                "impact_nodes": (
                    len(response.impact_subgraph.nodes)
                    if response.impact_subgraph
                    else 0
                ),
                "impact_edges": (
                    len(response.impact_subgraph.edges)
                    if response.impact_subgraph
                    else 0
                ),
            }

            self.stats["successful_requests"] += 1
            self.logger.info(
                "Impact analysis completed successfully",
                project_id=project_id,
                pr_number=pr_number,
                risk_level=result["risk_level"],
            )

            return result

        except grpc.RpcError as e:
            self.stats["failed_requests"] += 1
            self.logger.error(
                "gRPC impact analysis failed",
                project_id=project_id,
                pr_number=pr_number,
                code=e.code().name if e.code() else "UNKNOWN",
                details=e.details(),
            )

            return {
                "summary": "影響分析服務暫時無法使用",
                "risk_level": "UNKNOWN",
                "impact_nodes": 0,
                "error": f"gRPC Error: {e.code().name if e.code() else 'UNKNOWN'}",
                "error_details": e.details(),
            }
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(
                "Unexpected impact analysis error",
                project_id=project_id,
                pr_number=pr_number,
                error=str(e),
            )

            return {
                "summary": "影響分析過程中發生未預期的錯誤",
                "risk_level": "UNKNOWN",
                "impact_nodes": 0,
                "error": str(e),
            }

    def get_stats(self) -> Dict[str, Any]:
        """獲取橋接器統計資訊"""
        total_requests = max(self.stats["total_requests"], 1)

        return {
            **self.stats,
            "success_rate": round(
                self.stats["successful_requests"] / total_requests * 100, 2
            ),
            "is_connected": self._is_connected,
            "connection_status": "connected" if self._is_connected else "disconnected",
        }
