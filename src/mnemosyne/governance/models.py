"""
治理核心數據模型

定義約束、鎖定、違規等核心數據結構，基於 Pydantic 提供類型安全和驗證。
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ConstraintType(str, Enum):
    """約束類型枚舉"""

    ARCHITECTURE = "architecture"  # 架構約束
    SECURITY = "security"  # 安全約束
    QUALITY = "quality"  # 品質約束
    NAMING = "naming"  # 命名約束


class Severity(str, Enum):
    """嚴重程度枚舉"""

    ERROR = "error"  # 錯誤 - 必須修復
    WARNING = "warning"  # 警告 - 建議修復
    INFO = "info"  # 信息 - 僅提示


class RuleConfig(BaseModel):
    """規則配置基類"""

    class Config:
        extra = "allow"  # 允許額外字段以支援不同規則類型


class Constraint(BaseModel):
    """約束定義"""

    id: str = Field(..., description="約束唯一標識")
    name: str = Field(..., description="約束名稱")
    description: str = Field(..., description="約束描述")
    type: ConstraintType = Field(..., description="約束類型")
    severity: Severity = Field(..., description="嚴重程度")

    # 規則配置
    rule_config: RuleConfig = Field(..., description="規則配置")

    # 元數據
    enabled: bool = Field(default=True, description="是否啟用")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="創建時間")

    # 自定義訊息
    violation_message: Optional[str] = Field(None, description="違規訊息模板")
    suggestion: Optional[str] = Field(None, description="修復建議")


class ViolationLocation(BaseModel):
    """違規位置信息"""

    file_path: str = Field(..., description="檔案路徑")
    line_number: int = Field(..., description="行號")
    column_number: int = Field(default=0, description="列號")
    function_name: Optional[str] = Field(None, description="函數名稱")
    class_name: Optional[str] = Field(None, description="類名稱")


class Violation(BaseModel):
    """約束違規"""

    id: str = Field(..., description="違規唯一標識")
    constraint_id: str = Field(..., description="相關約束ID")
    constraint_name: str = Field(..., description="約束名稱")

    # 違規信息
    message: str = Field(..., description="違規訊息")
    severity: Severity = Field(..., description="嚴重程度")
    location: ViolationLocation = Field(..., description="違規位置")

    # 上下文信息
    suggestion: Optional[str] = Field(None, description="修復建議")

    # 元數據
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="檢測時間")


class ValidationResult(BaseModel):
    """驗證結果"""

    success: bool = Field(..., description="是否通過驗證")
    violations: List[Violation] = Field(default_factory=list, description="違規列表")

    # 統計信息
    total_files_checked: int = Field(default=0, description="檢查的檔案數")
    total_violations: int = Field(default=0, description="總違規數")
    error_count: int = Field(default=0, description="錯誤數")
    warning_count: int = Field(default=0, description="警告數")

    # 性能信息
    execution_time_ms: float = Field(default=0.0, description="執行時間（毫秒）")

    def add_violation(self, violation: Violation) -> None:
        """添加違規"""
        self.violations.append(violation)
        self.total_violations += 1

        if violation.severity == Severity.ERROR:
            self.error_count += 1
        elif violation.severity == Severity.WARNING:
            self.warning_count += 1

    def has_errors(self) -> bool:
        """是否有錯誤"""
        return self.error_count > 0


class LockScope(str, Enum):
    """鎖定範圍層級"""

    APPLICATION = "application"  # 整個應用程式
    PACKAGE = "package"  # 套件/模組
    FILE = "file"  # 檔案
    FUNCTION = "function"  # 函數


class LockStatus(str, Enum):
    """鎖定狀態"""

    ACTIVE = "active"  # 活躍
    EXPIRED = "expired"  # 已過期
    RELEASED = "released"  # 已釋放


class Lock(BaseModel):
    """鎖定定義"""

    id: str = Field(..., description="鎖定唯一標識")
    resource_id: str = Field(..., description="資源標識")
    resource_type: str = Field(..., description="資源類型")
    scope: LockScope = Field(..., description="鎖定範圍")

    # 鎖定信息
    owner_id: str = Field(..., description="擁有者標識")
    owner_name: Optional[str] = Field(None, description="擁有者名稱")
    reason: Optional[str] = Field(None, description="鎖定原因")

    # 時間信息
    acquired_at: datetime = Field(..., description="獲取時間")
    expires_at: datetime = Field(..., description="過期時間")

    # 狀態
    status: LockStatus = Field(default=LockStatus.ACTIVE, description="鎖定狀態")

    def is_expired(self) -> bool:
        """檢查是否已過期"""
        return datetime.utcnow() > self.expires_at


class LockRequest(BaseModel):
    """鎖定請求"""

    resource_id: str = Field(..., description="資源標識")
    resource_type: str = Field(..., description="資源類型")
    scope: LockScope = Field(..., description="鎖定範圍")

    owner_id: str = Field(..., description="擁有者標識")
    owner_name: Optional[str] = Field(None, description="擁有者名稱")
    reason: Optional[str] = Field(None, description="鎖定原因")

    timeout_seconds: int = Field(default=3600, description="超時時間（秒）")


class LockResult(BaseModel):
    """鎖定結果"""

    success: bool = Field(..., description="是否成功")
    lock: Optional[Lock] = Field(None, description="鎖定對象")

    # 錯誤信息
    error_message: Optional[str] = Field(None, description="錯誤訊息")

    # 衝突信息
    conflicting_locks: List[Lock] = Field(default_factory=list, description="衝突的鎖定列表")

    # 性能信息
    execution_time_ms: float = Field(default=0.0, description="執行時間（毫秒）")
