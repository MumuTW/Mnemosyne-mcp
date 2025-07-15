"""
AtlassianKnowledgeExtractorService gRPC 服務實現 - 簡化版

基於 AtlassianClient 和 AtlassianMapper 的簡化 gRPC 服務實現。
"""

import logging
import time
from typing import Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from mnemosyne.clients.atlassian import AtlassianClient
from mnemosyne.core.config import Settings
from mnemosyne.mappers.atlassian_mapper_simple import AtlassianMapper

from . import atlassian_pb2, atlassian_pb2_grpc

logger = logging.getLogger(__name__)


class AtlassianKnowledgeExtractorService(
    atlassian_pb2_grpc.AtlassianKnowledgeExtractorServicer
):
    """簡化的 AtlassianKnowledgeExtractorService 實現"""

    def __init__(self, settings: Settings):
        """初始化服務"""
        self.settings = settings
        self.client: Optional[AtlassianClient] = None
        self.mapper = AtlassianMapper()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "issues_extracted": 0,
            "pages_extracted": 0,
        }

    async def init_client(self) -> None:
        """初始化客戶端"""
        if self.settings.mcp_atlassian.is_configured:
            self.client = AtlassianClient(self.settings.mcp_atlassian)
            await self.client.__aenter__()

    async def close_client(self) -> None:
        """關閉客戶端"""
        if self.client:
            await self.client.__aexit__(None, None, None)

    async def ExtractJiraIssues(self, request, context):
        """提取 Jira Issues"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            if not self.client or not self.client.is_configured:
                logger.warning("AtlassianClient not configured")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Atlassian service not configured")
                return atlassian_pb2.ExtractJiraIssuesResponse()

            # 提取 Jira Issues
            issues = await self.client.search_jira_issues(
                query=request.query,
                project_filter=(
                    request.project_filter if request.project_filter else None
                ),
            )

            # 轉換為 gRPC 實體
            grpc_issues = []
            relationships = []

            for issue in issues[: request.max_results or 100]:
                # 映射為內部實體
                entity = self.mapper.jira_issue_to_entity(issue)

                # 轉換為 gRPC 實體
                grpc_issue = atlassian_pb2.JiraIssueEntity(
                    id=entity.id,
                    jira_id=issue.id,
                    key=issue.key,
                    summary=issue.summary,
                    description=getattr(issue, "description", ""),
                    status=issue.status,
                    priority=getattr(issue, "priority", ""),
                    issue_type=getattr(issue, "issue_type", ""),
                    project_key=getattr(issue, "project", ""),
                    assignee=getattr(issue, "assignee", ""),
                    reporter=getattr(issue, "reporter", ""),
                    url=getattr(issue, "url", ""),
                )
                grpc_issues.append(grpc_issue)

                # 如果需要包含關聯關係
                if request.include_relationships:
                    project_key = getattr(issue, "project", "")
                    if project_key:
                        rel = self.mapper.create_project_relationship(
                            entity, project_key
                        )
                        if rel:
                            relationships.append(
                                self._convert_relationship_to_grpc(rel)
                            )

            # 創建提取元數據
            processing_time = max(1, int((time.time() - start_time) * 1000))
            metadata = atlassian_pb2.ExtractionMetadata(
                extractor_version="1.0.0",
                total_entities=len(grpc_issues),
                total_relationships=len(relationships),
                processing_time_ms=processing_time,
            )

            # 設置提取時間
            extraction_time = Timestamp()
            extraction_time.GetCurrentTime()
            metadata.extraction_time.CopyFrom(extraction_time)

            # 更新統計
            self.stats["successful_requests"] += 1
            self.stats["issues_extracted"] += len(grpc_issues)

            return atlassian_pb2.ExtractJiraIssuesResponse(
                issues=grpc_issues,
                relationships=relationships,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error extracting Jira issues: {e}")
            self.stats["failed_requests"] += 1
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return atlassian_pb2.ExtractJiraIssuesResponse()

    async def ExtractConfluencePages(self, request, context):
        """提取 Confluence Pages"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            if not self.client or not self.client.is_configured:
                logger.warning("AtlassianClient not configured")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Atlassian service not configured")
                return atlassian_pb2.ExtractConfluencePagesResponse()

            # 提取 Confluence Pages
            pages = await self.client.search_confluence_pages(
                query=request.query,
                space_filter=request.space_filter if request.space_filter else None,
            )

            # 轉換為 gRPC 實體
            grpc_pages = []
            relationships = []

            for page in pages[: request.max_results or 100]:
                # 映射為內部實體
                entity = self.mapper.confluence_page_to_entity(page)

                # 轉換為 gRPC 實體
                grpc_page = atlassian_pb2.ConfluencePageEntity(
                    id=entity.id,
                    confluence_id=page.id,
                    title=page.title,
                    content=getattr(page, "content", ""),
                    space_key=getattr(page, "space", ""),
                    space_name=getattr(page, "space", ""),
                    author=getattr(page, "author", ""),
                    url=getattr(page, "url", ""),
                )
                grpc_pages.append(grpc_page)

                # 如果需要包含關聯關係
                if request.include_relationships:
                    space_key = getattr(page, "space", "")
                    if space_key:
                        rel = self.mapper.create_space_relationship(entity, space_key)
                        if rel:
                            relationships.append(
                                self._convert_relationship_to_grpc(rel)
                            )

            # 創建提取元數據
            processing_time = max(1, int((time.time() - start_time) * 1000))
            metadata = atlassian_pb2.ExtractionMetadata(
                extractor_version="1.0.0",
                total_entities=len(grpc_pages),
                total_relationships=len(relationships),
                processing_time_ms=processing_time,
            )

            # 設置提取時間
            extraction_time = Timestamp()
            extraction_time.GetCurrentTime()
            metadata.extraction_time.CopyFrom(extraction_time)

            # 更新統計
            self.stats["successful_requests"] += 1
            self.stats["pages_extracted"] += len(grpc_pages)

            return atlassian_pb2.ExtractConfluencePagesResponse(
                pages=grpc_pages,
                relationships=relationships,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error extracting Confluence pages: {e}")
            self.stats["failed_requests"] += 1
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return atlassian_pb2.ExtractConfluencePagesResponse()

    async def CheckHealth(self, request, context):
        """健康檢查"""
        start_time = time.time()

        try:
            if not self.client or not self.client.is_configured:
                response_time = max(1, int((time.time() - start_time) * 1000))
                return atlassian_pb2.HealthCheckResponse(
                    status=atlassian_pb2.HealthCheckResponse.Status.UNHEALTHY,
                    message="Atlassian service not configured",
                    response_time_ms=response_time,
                )

            # 執行健康檢查
            if request.check_connectivity:
                health_result = await self.client.health_check()
                status = (
                    atlassian_pb2.HealthCheckResponse.Status.HEALTHY
                    if health_result.get("status") == "healthy"
                    else atlassian_pb2.HealthCheckResponse.Status.UNHEALTHY
                )
                message = health_result.get("message", "")
            else:
                status = atlassian_pb2.HealthCheckResponse.Status.HEALTHY
                message = "Service is running"

            response_time = max(1, int((time.time() - start_time) * 1000))

            return atlassian_pb2.HealthCheckResponse(
                status=status,
                message=message,
                response_time_ms=response_time,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            response_time = max(1, int((time.time() - start_time) * 1000))
            return atlassian_pb2.HealthCheckResponse(
                status=atlassian_pb2.HealthCheckResponse.Status.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def GetExtractionStats(self, request, context):
        """獲取提取統計"""
        try:
            total_requests = self.stats["total_requests"]
            successful_requests = self.stats["successful_requests"]
            failed_requests = self.stats["failed_requests"]

            success_rate = (
                successful_requests / total_requests * 100.0
                if total_requests > 0
                else 0.0
            )

            return atlassian_pb2.ExtractionStatsResponse(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=success_rate,
                average_response_time_ms=0.0,  # 簡化版本
                issues_extracted=self.stats["issues_extracted"],
                pages_extracted=self.stats["pages_extracted"],
            )

        except Exception as e:
            logger.error(f"Error getting extraction stats: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return atlassian_pb2.ExtractionStatsResponse()

    def _convert_relationship_to_grpc(self, relationship):
        """將內部關係轉換為 gRPC 關係"""
        # 映射關係類型
        relationship_type_map = {
            "BELONGS_TO": atlassian_pb2.RelationshipType.BELONGS_TO,
            "ASSIGNED_TO": atlassian_pb2.RelationshipType.ASSIGNED_TO,
            "AUTHORED_BY": atlassian_pb2.RelationshipType.AUTHORED_BY,
            "CONTAINS": atlassian_pb2.RelationshipType.CONTAINS,
        }

        grpc_type = relationship_type_map.get(
            str(relationship.relationship_type), atlassian_pb2.RelationshipType.UNKNOWN
        )

        # 設置創建時間
        created_time = Timestamp()
        created_time.GetCurrentTime()

        return atlassian_pb2.KnowledgeRelationship(
            id=relationship.id,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            type=grpc_type,
            properties=relationship.extra or {},
            created_at=created_time,
            strength=1.0,  # 預設強度
        )
