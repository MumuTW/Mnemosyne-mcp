"""
Atlassian 客戶端

提供與 MCP Atlassian 服務的防禦性封裝，包含數據驗證、錯誤處理和監控。
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from pydantic import BaseModel, Field, ValidationError

from ..core.config import MCPAtlassianSettings

logger = structlog.get_logger(__name__)


class AtlassianServiceType(str, Enum):
    """Atlassian 服務類型"""

    JIRA = "jira"
    CONFLUENCE = "confluence"


@dataclass
class AtlassianResponse:
    """Atlassian API 響應封裝"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time_ms: Optional[float] = None
    service_type: Optional[AtlassianServiceType] = None


class JiraIssue(BaseModel):
    """Jira Issue 數據模型"""

    id: str = Field(description="Issue ID")
    key: str = Field(description="Issue Key")
    summary: str = Field(description="Issue 摘要")
    description: Optional[str] = Field(default=None, description="Issue 描述")
    status: str = Field(description="Issue 狀態")
    priority: Optional[str] = Field(default=None, description="優先級")
    assignee: Optional[str] = Field(default=None, description="指派人")
    reporter: Optional[str] = Field(default=None, description="報告人")
    project: Optional[str] = Field(default=None, description="專案")
    created: Optional[str] = Field(default=None, description="創建時間")
    updated: Optional[str] = Field(default=None, description="更新時間")
    labels: List[str] = Field(default_factory=list, description="標籤")


class ConfluencePage(BaseModel):
    """Confluence 頁面數據模型"""

    id: str = Field(description="頁面 ID")
    title: str = Field(description="頁面標題")
    content: Optional[str] = Field(default=None, description="頁面內容")
    space: Optional[str] = Field(default=None, description="空間")
    author: Optional[str] = Field(default=None, description="作者")
    created: Optional[str] = Field(default=None, description="創建時間")
    updated: Optional[str] = Field(default=None, description="更新時間")
    version: Optional[int] = Field(default=None, description="版本號")
    url: Optional[str] = Field(default=None, description="頁面 URL")


class AtlassianClient:
    """
    Atlassian 客戶端

    提供防禦性封裝，包含：
    - 數據驗證
    - 錯誤處理
    - 監控和日誌
    - 重試機制
    """

    def __init__(self, settings: MCPAtlassianSettings):
        """
        初始化 Atlassian 客戶端

        Args:
            settings: MCP Atlassian 配置
        """
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        self._base_url = settings.service_url.rstrip("/")

        # 統計信息
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0

        logger.info(
            "Atlassian client initialized",
            service_url=self._base_url,
            read_only_mode=settings.read_only_mode,
            enabled_tools=settings.enabled_tools,
        )

    async def __aenter__(self) -> "AtlassianClient":
        """異步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        service_type: Optional[AtlassianServiceType] = None,
    ) -> AtlassianResponse:
        """
        發送請求到 MCP Atlassian 服務

        Args:
            method: HTTP 方法
            endpoint: API 端點
            data: 請求數據
            service_type: 服務類型

        Returns:
            AtlassianResponse: 封裝的響應
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use async context manager."
            )

        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        start_time = time.monotonic()

        try:
            self.request_count += 1

            logger.debug(
                "Making request to MCP Atlassian",
                method=method,
                url=url,
                data=data,
                service_type=service_type.value if service_type else None,
            )

            async with self.session.request(method, url, json=data) as response:
                response_time_ms = (time.monotonic() - start_time) * 1000
                self.total_response_time += response_time_ms

                if response.status == 200:
                    response_data = await response.json()

                    logger.debug(
                        "Request successful",
                        url=url,
                        status=response.status,
                        response_time_ms=response_time_ms,
                    )

                    return AtlassianResponse(
                        success=True,
                        data=response_data,
                        response_time_ms=response_time_ms,
                        service_type=service_type,
                    )
                else:
                    error_text = await response.text()
                    self.error_count += 1

                    logger.warning(
                        "Request failed",
                        url=url,
                        status=response.status,
                        error=error_text,
                        response_time_ms=response_time_ms,
                    )

                    return AtlassianResponse(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        response_time_ms=response_time_ms,
                        service_type=service_type,
                    )

        except aiohttp.ClientError as e:
            self.error_count += 1
            response_time_ms = (time.monotonic() - start_time) * 1000

            logger.error(
                "Request failed with client error",
                url=url,
                error=str(e),
                response_time_ms=response_time_ms,
            )

            return AtlassianResponse(
                success=False,
                error=f"Client error: {str(e)}",
                response_time_ms=response_time_ms,
                service_type=service_type,
            )
        except Exception as e:
            self.error_count += 1
            response_time_ms = (time.monotonic() - start_time) * 1000

            logger.error(
                "Request failed with unexpected error",
                url=url,
                error=str(e),
                response_time_ms=response_time_ms,
                exc_info=True,
            )

            return AtlassianResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                response_time_ms=response_time_ms,
                service_type=service_type,
            )

    async def search_jira_issues(
        self, query: str, project_filter: Optional[str] = None, max_results: int = 50
    ) -> List[JiraIssue]:
        """
        搜索 Jira Issues

        Args:
            query: 搜索查詢
            project_filter: 專案過濾器
            max_results: 最大結果數

        Returns:
            List[JiraIssue]: Jira Issue 列表
        """
        if "jira_search" not in self.settings.enabled_tools:
            logger.warning("Jira search tool not enabled")
            return []

        search_params = {
            "query": query,
            "max_results": max_results,
        }

        if project_filter:
            search_params["project_filter"] = project_filter
        elif self.settings.jira_projects_filter:
            search_params["project_filter"] = self.settings.jira_projects_filter

        response = await self._make_request(
            "POST",
            "/jira/search",
            data=search_params,
            service_type=AtlassianServiceType.JIRA,
        )

        if not response.success:
            logger.error("Jira search failed", error=response.error)
            return []

        try:
            issues = []
            for issue_data in response.data.get("issues", []):
                try:
                    issue = JiraIssue(**issue_data)
                    issues.append(issue)
                except ValidationError as e:
                    logger.warning(
                        "Failed to parse Jira issue",
                        issue_data=issue_data,
                        error=str(e),
                    )
                    continue

            logger.info(
                "Jira search completed",
                query=query,
                found_issues=len(issues),
                response_time_ms=response.response_time_ms,
            )

            return issues

        except Exception as e:
            logger.error(
                "Failed to process Jira search response",
                error=str(e),
                response_data=response.data,
            )
            return []

    async def get_jira_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """
        獲取特定 Jira Issue

        Args:
            issue_key: Issue Key

        Returns:
            Optional[JiraIssue]: Jira Issue 或 None
        """
        if "jira_get_issue" not in self.settings.enabled_tools:
            logger.warning("Jira get issue tool not enabled")
            return None

        response = await self._make_request(
            "GET",
            f"/jira/issue/{issue_key}",
            service_type=AtlassianServiceType.JIRA,
        )

        if not response.success:
            logger.error(
                "Get Jira issue failed", issue_key=issue_key, error=response.error
            )
            return None

        try:
            issue = JiraIssue(**response.data)

            logger.info(
                "Jira issue retrieved",
                issue_key=issue_key,
                response_time_ms=response.response_time_ms,
            )

            return issue

        except ValidationError as e:
            logger.error(
                "Failed to parse Jira issue",
                issue_key=issue_key,
                error=str(e),
                response_data=response.data,
            )
            return None

    async def search_confluence_pages(
        self, query: str, space_filter: Optional[str] = None, max_results: int = 50
    ) -> List[ConfluencePage]:
        """
        搜索 Confluence 頁面

        Args:
            query: 搜索查詢
            space_filter: 空間過濾器
            max_results: 最大結果數

        Returns:
            List[ConfluencePage]: Confluence 頁面列表
        """
        if "confluence_search" not in self.settings.enabled_tools:
            logger.warning("Confluence search tool not enabled")
            return []

        search_params = {
            "query": query,
            "max_results": max_results,
        }

        if space_filter:
            search_params["space_filter"] = space_filter
        elif self.settings.confluence_spaces_filter:
            search_params["space_filter"] = self.settings.confluence_spaces_filter

        response = await self._make_request(
            "POST",
            "/confluence/search",
            data=search_params,
            service_type=AtlassianServiceType.CONFLUENCE,
        )

        if not response.success:
            logger.error("Confluence search failed", error=response.error)
            return []

        try:
            pages = []
            for page_data in response.data.get("pages", []):
                try:
                    page = ConfluencePage(**page_data)
                    pages.append(page)
                except ValidationError as e:
                    logger.warning(
                        "Failed to parse Confluence page",
                        page_data=page_data,
                        error=str(e),
                    )
                    continue

            logger.info(
                "Confluence search completed",
                query=query,
                found_pages=len(pages),
                response_time_ms=response.response_time_ms,
            )

            return pages

        except Exception as e:
            logger.error(
                "Failed to process Confluence search response",
                error=str(e),
                response_data=response.data,
            )
            return []

    async def health_check(self) -> Dict[str, Any]:
        """
        健康檢查

        Returns:
            Dict[str, Any]: 健康狀態信息
        """
        response = await self._make_request("GET", "/health")

        if response.success:
            return {
                "status": "healthy",
                "response_time_ms": response.response_time_ms,
                "data": response.data,
            }
        else:
            return {
                "status": "unhealthy",
                "error": response.error,
                "response_time_ms": response.response_time_ms,
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        獲取客戶端統計信息

        Returns:
            Dict[str, Any]: 統計信息
        """
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0
            else 0
        )

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count * 100
                if self.request_count > 0
                else 0
            ),
            "average_response_time_ms": avg_response_time,
            "total_response_time_ms": self.total_response_time,
        }

    @property
    def is_configured(self) -> bool:
        """檢查客戶端是否已正確配置"""
        return self.settings.is_configured
