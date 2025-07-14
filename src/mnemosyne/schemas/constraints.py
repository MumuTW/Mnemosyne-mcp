"""
約束和鎖定數據模型定義

定義了治理相關的數據模型，用於 Sprint 3 的約束和鎖定功能。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


class ConstraintType(str, Enum):
    """約束類型枚舉"""
    IMMUTABLE_LOGIC = "IMMUTABLE_LOGIC"
    DEPRECATION_POLICY = "DEPRECATION_POLICY"
    VERSION_PINNING = "VERSION_PINNING"
    LICENSE_RESTRICTION = "LICENSE_RESTRICTION"
    ARCHITECTURE_BOUNDARY = "ARCHITECTURE_BOUNDARY"
    SECURITY_POLICY = "SECURITY_POLICY"
    PERFORMANCE_THRESHOLD = "PERFORMANCE_THRESHOLD"


class ConstraintSeverity(str, Enum):
    """約束嚴重程度枚舉"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LockStatus(str, Enum):
    """鎖定狀態枚舉"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    FAILED = "FAILED"


class Constraint(BaseModel):
    """
    約束模型
    
    定義了對程式碼實體的約束規則。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="約束唯一標識符")
    name: str = Field(description="約束名稱")
    constraint_type: ConstraintType = Field(description="約束類型")
    description: str = Field(description="約束描述")
    
    # 約束屬性
    severity: ConstraintSeverity = Field(default=ConstraintSeverity.MEDIUM, description="嚴重程度")
    active: bool = Field(default=True, description="是否激活")
    
    # 約束規則
    rules: Dict[str, Any] = Field(default_factory=dict, description="約束規則配置")
    
    # 責任人
    owner: Optional[str] = Field(default=None, description="約束負責人")
    team: Optional[str] = Field(default=None, description="負責團隊")
    
    # 時間屬性
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")
    expires_at: Optional[datetime] = Field(default=None, description="過期時間")
    
    # 統計信息
    violation_count: int = Field(default=0, description="違規次數")
    last_violation: Optional[datetime] = Field(default=None, description="最後違規時間")
    
    # 通知配置
    notification_channels: List[str] = Field(default_factory=list, description="通知渠道")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @validator('expires_at')
    def validate_expiry(cls, v, values):
        """驗證過期時間"""
        if v and 'created_at' in values and v <= values['created_at']:
            raise ValueError("Expiry time must be after creation time")
        return v
    
    @property
    def is_expired(self) -> bool:
        """檢查約束是否已過期"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def is_effective(self) -> bool:
        """檢查約束是否有效"""
        return self.active and not self.is_expired
    
    def record_violation(self) -> None:
        """記錄違規"""
        self.violation_count += 1
        self.last_violation = datetime.now()
        self.updated_at = datetime.now()


class Lock(BaseModel):
    """
    鎖定模型
    
    用於協調多代理的並行操作，防止衝突。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="鎖定唯一標識符")
    target_entity_id: str = Field(description="被鎖定的實體ID")
    target_entity_type: str = Field(description="被鎖定的實體類型")
    
    # 鎖定信息
    lock_type: str = Field(default="exclusive", description="鎖定類型：shared, exclusive")
    status: LockStatus = Field(default=LockStatus.ACTIVE, description="鎖定狀態")
    
    # 持有者信息
    holder_id: str = Field(description="鎖定持有者ID（代理或用戶）")
    holder_type: str = Field(description="持有者類型：agent, user, system")
    task_id: Optional[str] = Field(default=None, description="關聯的任務ID")
    
    # 時間屬性
    acquired_at: datetime = Field(default_factory=datetime.now, description="獲取時間")
    expires_at: Optional[datetime] = Field(default=None, description="過期時間")
    released_at: Optional[datetime] = Field(default=None, description="釋放時間")
    
    # 鎖定原因和上下文
    reason: str = Field(description="鎖定原因")
    context: Dict[str, Any] = Field(default_factory=dict, description="鎖定上下文")
    
    # 續期配置
    auto_extend: bool = Field(default=False, description="是否自動續期")
    max_duration_minutes: Optional[int] = Field(default=None, description="最大持續時間（分鐘）")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @validator('expires_at')
    def validate_expiry(cls, v, values):
        """驗證過期時間"""
        if v and 'acquired_at' in values and v <= values['acquired_at']:
            raise ValueError("Expiry time must be after acquisition time")
        return v
    
    @validator('released_at')
    def validate_release_time(cls, v, values):
        """驗證釋放時間"""
        if v and 'acquired_at' in values and v < values['acquired_at']:
            raise ValueError("Release time must be after acquisition time")
        return v
    
    @property
    def is_expired(self) -> bool:
        """檢查鎖定是否已過期"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def is_active(self) -> bool:
        """檢查鎖定是否激活"""
        return (
            self.status == LockStatus.ACTIVE 
            and not self.is_expired 
            and self.released_at is None
        )
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """計算鎖定持續時間（分鐘）"""
        end_time = self.released_at or datetime.now()
        duration = end_time - self.acquired_at
        return duration.total_seconds() / 60
    
    def release(self) -> None:
        """釋放鎖定"""
        self.status = LockStatus.RELEASED
        self.released_at = datetime.now()
    
    def extend(self, minutes: int) -> None:
        """延長鎖定時間"""
        if not self.is_active:
            raise ValueError("Cannot extend inactive lock")
        
        if self.expires_at:
            self.expires_at = self.expires_at + datetime.timedelta(minutes=minutes)
        else:
            self.expires_at = datetime.now() + datetime.timedelta(minutes=minutes)


class ConstraintViolation(BaseModel):
    """
    約束違規模型
    
    記錄約束違規的詳細信息。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="違規唯一標識符")
    constraint_id: str = Field(description="違反的約束ID")
    entity_id: str = Field(description="違規實體ID")
    entity_type: str = Field(description="違規實體類型")
    
    # 違規詳情
    violation_type: str = Field(description="違規類型")
    description: str = Field(description="違規描述")
    severity: ConstraintSeverity = Field(description="違規嚴重程度")
    
    # 上下文信息
    context: Dict[str, Any] = Field(default_factory=dict, description="違規上下文")
    change_details: Optional[Dict[str, Any]] = Field(default=None, description="變更詳情")
    
    # 時間屬性
    detected_at: datetime = Field(default_factory=datetime.now, description="檢測時間")
    resolved_at: Optional[datetime] = Field(default=None, description="解決時間")
    
    # 處理狀態
    status: str = Field(default="open", description="處理狀態：open, acknowledged, resolved, ignored")
    assignee: Optional[str] = Field(default=None, description="處理人")
    
    # 修復建議
    remediation_suggestions: List[str] = Field(default_factory=list, description="修復建議")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @property
    def is_resolved(self) -> bool:
        """檢查違規是否已解決"""
        return self.status == "resolved" and self.resolved_at is not None
    
    @property
    def age_hours(self) -> float:
        """計算違規存在時間（小時）"""
        end_time = self.resolved_at or datetime.now()
        duration = end_time - self.detected_at
        return duration.total_seconds() / 3600
    
    def resolve(self, resolver: str) -> None:
        """標記違規為已解決"""
        self.status = "resolved"
        self.resolved_at = datetime.now()
        self.assignee = resolver
