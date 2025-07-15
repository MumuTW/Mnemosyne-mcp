"""
Atlassian 知識圖譜數據模型

定義 Jira Issues、Confluence Pages 和相關關係的數據結構。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .relationships import RelationshipType


class AtlassianEntityType(str, Enum):
    """Atlassian 實體類型枚舉"""

    JIRA_ISSUE = "jira_issue"
    CONFLUENCE_PAGE = "confluence_page"
    JIRA_PROJECT = "jira_project"
    CONFLUENCE_SPACE = "confluence_space"
    PERSON = "person"
    ATTACHMENT = "attachment"
    COMMENT = "comment"


class AtlassianEntity(BaseModel):
    """
    Atlassian 實體基礎模型

    統一的 Atlassian 實體表示，適用於 Jira Issues 和 Confluence Pages
    """

    id: str = Field(description="實體唯一標識符")
    entity_type: str = Field(description="實體類型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="實體屬性")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")

    model_config = ConfigDict(use_enum_values=True)

    def to_graph_properties(self) -> Dict[str, Any]:
        """轉換為圖資料庫屬性格式"""
        props = {
            "id": self.id,
            "entity_type": self.entity_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # 合併實體屬性
        props.update(self.properties)

        # 移除 None 值
        return {k: v for k, v in props.items() if v is not None}

    @property
    def project_key(self) -> Optional[str]:
        """獲取專案鍵值（適用於 Jira Issue）"""
        return self.properties.get("project_key")

    @property
    def space_key(self) -> Optional[str]:
        """獲取空間鍵值（適用於 Confluence Page）"""
        return self.properties.get("space_key")

    @property
    def space_name(self) -> Optional[str]:
        """獲取空間名稱（適用於 Confluence Page）"""
        return self.properties.get("space_name")


class AtlassianRelationship(BaseModel):
    """
    Atlassian 關係模型

    表示 Atlassian 實體之間的關係
    """

    id: str = Field(description="關係唯一標識符")
    source_id: str = Field(description="源實體 ID")
    target_id: str = Field(description="目標實體 ID")
    relationship_type: RelationshipType = Field(description="關係類型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="關係屬性")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    strength: float = Field(default=1.0, description="關係強度 (0.0-1.0)")

    model_config = ConfigDict(use_enum_values=True)

    def to_graph_properties(self) -> Dict[str, Any]:
        """轉換為圖資料庫屬性格式"""
        props = {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": str(self.relationship_type),
            "strength": self.strength,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # 合併關係屬性
        props.update(self.properties)

        # 移除 None 值
        return {k: v for k, v in props.items() if v is not None}


class JiraIssueData(BaseModel):
    """
    Jira Issue 原始數據模型

    用於接收來自 Jira API 的原始數據
    """

    id: str = Field(description="Jira 內部 ID")
    key: str = Field(description="Issue 鍵值 (如 DEMO-123)")
    summary: str = Field(description="Issue 摘要")
    description: Optional[str] = Field(default=None, description="Issue 描述")
    status: str = Field(description="狀態")
    priority: Optional[str] = Field(default=None, description="優先級")
    issue_type: str = Field(description="Issue 類型")
    project_key: str = Field(description="所屬專案鍵值")
    assignee: Optional[str] = Field(default=None, description="指派者")
    reporter: Optional[str] = Field(default=None, description="報告者")
    created: datetime = Field(description="創建時間")
    updated: datetime = Field(description="更新時間")
    labels: List[str] = Field(default_factory=list, description="標籤列表")
    components: List[str] = Field(default_factory=list, description="組件列表")
    custom_fields: Dict[str, str] = Field(default_factory=dict, description="自定義欄位")
    url: Optional[str] = Field(default=None, description="Issue URL")

    model_config = ConfigDict(use_enum_values=True)


class ConfluencePageData(BaseModel):
    """
    Confluence Page 原始數據模型

    用於接收來自 Confluence API 的原始數據
    """

    id: str = Field(description="Confluence 內部 ID")
    title: str = Field(description="頁面標題")
    content: Optional[str] = Field(default=None, description="頁面內容")
    space_key: str = Field(description="空間鍵值")
    space_name: str = Field(description="空間名稱")
    author: Optional[str] = Field(default=None, description="作者")
    created: datetime = Field(description="創建時間")
    updated: datetime = Field(description="更新時間")
    version: int = Field(description="版本號")
    status: str = Field(description="狀態")
    labels: List[str] = Field(default_factory=list, description="標籤列表")
    ancestors: List[str] = Field(default_factory=list, description="父頁面列表")
    url: Optional[str] = Field(default=None, description="頁面 URL")

    model_config = ConfigDict(use_enum_values=True)


class AtlassianExtractionMetadata(BaseModel):
    """
    Atlassian 資料提取元數據

    記錄提取過程的相關信息
    """

    extraction_time: datetime = Field(default_factory=datetime.now, description="提取時間")
    extractor_version: str = Field(description="提取器版本")
    total_entities: int = Field(description="總實體數量")
    total_relationships: int = Field(description="總關係數量")
    processing_time_ms: int = Field(description="處理時間（毫秒）")
    source_info: Dict[str, str] = Field(default_factory=dict, description="數據源資訊")
    warnings: List[str] = Field(default_factory=list, description="警告訊息")
    errors: List[str] = Field(default_factory=list, description="錯誤訊息")

    model_config = ConfigDict(use_enum_values=True)


class AtlassianConfig(BaseModel):
    """
    Atlassian 提取配置

    配置 Atlassian 數據提取的參數
    """

    max_concurrent_requests: int = Field(default=5, description="最大並發請求數")
    request_timeout_seconds: int = Field(default=30, description="請求超時時間")
    enable_caching: bool = Field(default=True, description="是否啟用快取")
    cache_ttl_seconds: int = Field(default=3600, description="快取存活時間")
    included_fields: List[str] = Field(default_factory=list, description="包含的欄位")
    excluded_fields: List[str] = Field(default_factory=list, description="排除的欄位")

    model_config = ConfigDict(use_enum_values=True)
