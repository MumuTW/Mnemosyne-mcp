"""
API 數據模型定義

定義了 API 請求和響應的數據模型。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """任務狀態枚舉"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HealthStatus(str, Enum):
    """健康狀態枚舉"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """健康檢查響應模型"""

    status: HealthStatus = Field(description="服務健康狀態")
    timestamp: datetime = Field(default_factory=datetime.now, description="檢查時間")
    version: str = Field(default="0.1.0", description="服務版本")

    # 組件健康狀態
    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="組件狀態"
    )

    # 系統信息
    uptime_seconds: Optional[float] = Field(default=None, description="運行時間（秒）")
    memory_usage_mb: Optional[float] = Field(default=None, description="內存使用（MB）")

    model_config = ConfigDict(use_enum_values=True)


class ErrorResponse(BaseModel):
    """錯誤響應模型"""

    error: str = Field(description="錯誤類型")
    message: str = Field(description="錯誤消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="錯誤詳情")
    timestamp: datetime = Field(default_factory=datetime.now, description="錯誤時間")
    trace_id: Optional[str] = Field(default=None, description="追蹤ID")

    model_config = ConfigDict()


class IngestRequest(BaseModel):
    """數據導入請求模型"""

    project_id: str = Field(description="專案唯一標識符")
    source_path: str = Field(description="源代碼路徑")

    # 可選配置
    branch: Optional[str] = Field(default=None, description="Git 分支")
    include_patterns: List[str] = Field(default_factory=list, description="包含文件模式")
    exclude_patterns: List[str] = Field(default_factory=list, description="排除文件模式")

    # 處理選項
    force_refresh: bool = Field(default=False, description="是否強制刷新")
    incremental: bool = Field(default=True, description="是否增量更新")

    # 分析選項
    analyze_dependencies: bool = Field(default=True, description="是否分析依賴")
    extract_comments: bool = Field(default=False, description="是否提取註釋")
    calculate_metrics: bool = Field(default=True, description="是否計算指標")


class IngestResponse(BaseModel):
    """數據導入響應模型"""

    task_id: str = Field(description="任務ID")
    status: TaskStatus = Field(description="任務狀態")
    message: str = Field(description="響應消息")

    # 任務信息
    created_at: datetime = Field(default_factory=datetime.now, description="任務創建時間")
    estimated_duration_minutes: Optional[int] = Field(
        default=None, description="預估耗時（分鐘）"
    )

    # 進度信息
    progress_url: Optional[str] = Field(default=None, description="進度查詢URL")

    model_config = ConfigDict(use_enum_values=True)


class TaskStatusResponse(BaseModel):
    """任務狀態響應模型"""

    task_id: str = Field(description="任務ID")
    status: TaskStatus = Field(description="任務狀態")

    # 時間信息
    created_at: datetime = Field(description="任務創建時間")
    started_at: Optional[datetime] = Field(default=None, description="任務開始時間")
    completed_at: Optional[datetime] = Field(default=None, description="任務完成時間")

    # 進度信息
    progress_percentage: Optional[float] = Field(default=None, description="進度百分比")
    current_step: Optional[str] = Field(default=None, description="當前步驟")
    total_steps: Optional[int] = Field(default=None, description="總步驟數")

    # 結果信息
    result: Optional[Dict[str, Any]] = Field(default=None, description="任務結果")
    error: Optional[str] = Field(default=None, description="錯誤信息")

    # 統計信息
    files_processed: Optional[int] = Field(default=None, description="已處理文件數")
    entities_created: Optional[int] = Field(default=None, description="創建實體數")
    relationships_created: Optional[int] = Field(default=None, description="創建關係數")

    model_config = ConfigDict(use_enum_values=True)


class SearchRequest(BaseModel):
    """搜索請求模型"""

    query: str = Field(description="搜索查詢")
    project_id: Optional[str] = Field(default=None, description="專案ID")

    # 搜索選項
    entity_types: List[str] = Field(default_factory=list, description="實體類型過濾")
    max_results: int = Field(default=10, description="最大結果數")
    include_relationships: bool = Field(default=True, description="是否包含關係")

    # 高級選項
    semantic_search: bool = Field(default=False, description="是否使用語義搜索")
    fuzzy_matching: bool = Field(default=True, description="是否模糊匹配")


class SearchResult(BaseModel):
    """搜索結果項模型"""

    entity_id: str = Field(description="實體ID")
    entity_type: str = Field(description="實體類型")
    name: str = Field(description="實體名稱")

    # 匹配信息
    score: float = Field(description="匹配分數")
    matched_fields: List[str] = Field(default_factory=list, description="匹配字段")

    # 實體屬性
    properties: Dict[str, Any] = Field(default_factory=dict, description="實體屬性")

    # 關係信息
    relationships: List[Dict[str, Any]] = Field(
        default_factory=list, description="相關關係"
    )


class SearchResponse(BaseModel):
    """搜索響應模型"""

    query: str = Field(description="原始查詢")
    total_results: int = Field(description="總結果數")
    results: List[SearchResult] = Field(description="搜索結果")

    # 執行信息
    execution_time_ms: float = Field(description="執行時間（毫秒）")
    used_semantic_search: bool = Field(default=False, description="是否使用了語義搜索")

    # 建議
    suggestions: List[str] = Field(default_factory=list, description="搜索建議")


class ImpactAnalysisRequest(BaseModel):
    """影響分析請求模型"""

    entity_id: str = Field(description="分析目標實體ID")
    change_type: str = Field(description="變更類型：modify, delete, move")

    # 分析選項
    max_depth: int = Field(default=3, description="最大分析深度")
    include_indirect: bool = Field(default=True, description="是否包含間接影響")

    # 過濾選項
    exclude_entity_types: List[str] = Field(default_factory=list, description="排除的實體類型")


class ImpactAnalysisResponse(BaseModel):
    """影響分析響應模型"""

    target_entity_id: str = Field(description="目標實體ID")
    change_type: str = Field(description="變更類型")

    # 影響摘要
    risk_level: str = Field(description="風險等級：low, medium, high, critical")
    impact_score: float = Field(description="影響分數")
    affected_entities_count: int = Field(description="受影響實體數量")

    # 詳細影響
    direct_impacts: List[Dict[str, Any]] = Field(
        default_factory=list, description="直接影響"
    )
    indirect_impacts: List[Dict[str, Any]] = Field(
        default_factory=list, description="間接影響"
    )

    # 建議
    recommendations: List[str] = Field(default_factory=list, description="建議")
    required_tests: List[str] = Field(default_factory=list, description="需要的測試")

    # 執行信息
    execution_time_ms: float = Field(description="執行時間（毫秒）")
    analysis_depth: int = Field(description="實際分析深度")
