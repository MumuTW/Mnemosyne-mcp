"""
MCP Atlassian 模擬伺服器

提供與 mcp-atlassian API 契約一致的模擬響應，用於單元測試。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class MCPAtlassianMockData:
    """MCP Atlassian 模擬數據生成器"""

    @staticmethod
    def create_jira_issue(
        issue_id: str = "DEMO-123",
        key: str = "DEMO-123",
        summary: str = "示例 Jira Issue",
        description: str = "這是一個測試用的 Jira Issue",
        status: str = "In Progress",
        priority: str = "Medium",
        assignee: str = "john.doe",
        reporter: str = "jane.smith",
        project: str = "DEMO",
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """創建模擬 Jira Issue 數據"""
        if labels is None:
            labels = ["backend", "api"]

        return {
            "id": issue_id,
            "key": key,
            "summary": summary,
            "description": description,
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "reporter": reporter,
            "project": project,
            "created": "2024-01-15T10:30:00.000+0000",
            "updated": "2024-01-16T14:45:00.000+0000",
            "labels": labels,
        }

    @staticmethod
    def create_confluence_page(
        page_id: str = "123456789",
        title: str = "示例 Confluence 頁面",
        content: str = "這是一個測試用的 Confluence 頁面內容",
        space: str = "DEMO",
        author: str = "john.doe",
        version: int = 1,
    ) -> Dict[str, Any]:
        """創建模擬 Confluence 頁面數據"""
        return {
            "id": page_id,
            "title": title,
            "content": content,
            "space": space,
            "author": author,
            "created": "2024-01-15T10:30:00.000+0000",
            "updated": "2024-01-16T14:45:00.000+0000",
            "version": version,
            "url": f"https://company.atlassian.net/wiki/spaces/{space}/pages/{page_id}",
        }

    @staticmethod
    def create_jira_search_response(
        issues: Optional[List[Dict[str, Any]]] = None,
        total: int = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """創建模擬 Jira 搜尋響應"""
        if issues is None:
            issues = [
                MCPAtlassianMockData.create_jira_issue(
                    issue_id="DEMO-123",
                    key="DEMO-123",
                    summary="修復登入功能錯誤",
                    status="In Progress",
                ),
                MCPAtlassianMockData.create_jira_issue(
                    issue_id="DEMO-124",
                    key="DEMO-124",
                    summary="新增用戶註冊 API",
                    status="To Do",
                ),
            ]

        if total is None:
            total = len(issues)

        return {
            "issues": issues,
            "total": total,
            "max_results": max_results,
            "start_at": 0,
        }

    @staticmethod
    def create_confluence_search_response(
        pages: Optional[List[Dict[str, Any]]] = None,
        total: int = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """創建模擬 Confluence 搜尋響應"""
        if pages is None:
            pages = [
                MCPAtlassianMockData.create_confluence_page(
                    page_id="123456789",
                    title="API 開發指南",
                    space="DEV",
                ),
                MCPAtlassianMockData.create_confluence_page(
                    page_id="123456790",
                    title="系統架構設計",
                    space="ARCH",
                ),
            ]

        if total is None:
            total = len(pages)

        return {
            "pages": pages,
            "total": total,
            "max_results": max_results,
            "start_at": 0,
        }

    @staticmethod
    def create_health_response(status: str = "healthy") -> Dict[str, Any]:
        """創建模擬健康檢查響應"""
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "jira": {"status": "connected", "url": "https://company.atlassian.net"},
                "confluence": {
                    "status": "connected",
                    "url": "https://company.atlassian.net/wiki",
                },
            },
        }

    @staticmethod
    def create_error_response(
        error_type: str = "ValidationError",
        message: str = "Invalid request parameters",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """創建模擬錯誤響應"""
        return {
            "error": error_type,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }


class MCPAtlassianMockServer:
    """
    MCP Atlassian 模擬伺服器

    提供與真實 MCP Atlassian API 契約一致的模擬端點，
    用於 AtlassianClient 的單元測試。
    """

    def __init__(self):
        """初始化模擬伺服器"""
        self.mock_data = MCPAtlassianMockData()

    def setup_successful_responses(self, mock_session):
        """設置成功響應的模擬"""
        # 健康檢查
        mock_session.get(
            "http://mcp-atlassian:8001/health",
            status=200,
            payload=self.mock_data.create_health_response(),
        )

        # Jira 搜尋
        mock_session.post(
            "http://mcp-atlassian:8001/jira/search",
            status=200,
            payload=self.mock_data.create_jira_search_response(),
        )

        # Jira 單一 Issue
        mock_session.get(
            "http://mcp-atlassian:8001/jira/issue/DEMO-123",
            status=200,
            payload=self.mock_data.create_jira_issue(),
        )

        # Confluence 搜尋
        mock_session.post(
            "http://mcp-atlassian:8001/confluence/search",
            status=200,
            payload=self.mock_data.create_confluence_search_response(),
        )

    def setup_error_responses(self, mock_session):
        """設置錯誤響應的模擬"""
        # 健康檢查失敗
        mock_session.get(
            "http://mcp-atlassian:8001/health",
            status=503,
            payload=self.mock_data.create_error_response(
                error_type="ServiceUnavailable",
                message="MCP Atlassian service is temporarily unavailable",
            ),
        )

        # Jira 搜尋失敗
        mock_session.post(
            "http://mcp-atlassian:8001/jira/search",
            status=400,
            payload=self.mock_data.create_error_response(
                error_type="BadRequest",
                message="Invalid search query",
                details={"field": "query", "issue": "Query cannot be empty"},
            ),
        )

        # Jira Issue 不存在
        mock_session.get(
            "http://mcp-atlassian:8001/jira/issue/NOTFOUND-999",
            status=404,
            payload=self.mock_data.create_error_response(
                error_type="NotFound", message="Issue not found"
            ),
        )

        # Confluence 搜尋失敗
        mock_session.post(
            "http://mcp-atlassian:8001/confluence/search",
            status=403,
            payload=self.mock_data.create_error_response(
                error_type="Forbidden",
                message="Insufficient permissions to search Confluence",
            ),
        )

    def setup_custom_response(
        self,
        mock_session,
        method: str,
        url: str,
        status: int = 200,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """設置自定義響應"""
        if method.upper() == "GET":
            mock_session.get(url, status=status, payload=payload or {})
        elif method.upper() == "POST":
            mock_session.post(url, status=status, payload=payload or {})
        elif method.upper() == "PUT":
            mock_session.put(url, status=status, payload=payload or {})
        elif method.upper() == "DELETE":
            mock_session.delete(url, status=status, payload=payload or {})
