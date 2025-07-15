"""
關係數據模型定義

定義了知識圖譜中的邊（關係）類型，如 CALLS, CONTAINS, DEPENDS_ON 等。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class RelationshipType(str, Enum):
    """關係類型枚舉"""

    CALLS = "CALLS"
    CONTAINS = "CONTAINS"
    DEPENDS_ON = "DEPENDS_ON"
    INHERITS_FROM = "INHERITS_FROM"
    IMPLEMENTS = "IMPLEMENTS"
    IMPORTS = "IMPORTS"
    DEFINES = "DEFINES"
    USES = "USES"
    APPLIES_TO = "APPLIES_TO"  # 用於約束關係


class BaseRelationship(BaseModel):
    """
    基礎關係模型

    所有圖譜邊的基礎類，提供通用的屬性和方法。
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="關係唯一標識符"
    )
    relationship_type: RelationshipType = Field(description="關係類型")
    source_id: str = Field(description="源節點ID")
    target_id: str = Field(description="目標節點ID")

    # 時間屬性
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")

    # 有效期（用於時間版本控制）
    valid_from: Optional[datetime] = Field(default=None, description="有效開始時間")
    valid_to: Optional[datetime] = Field(default=None, description="有效結束時間")

    # 擴展屬性
    extra: Dict[str, Any] = Field(default_factory=dict, description="擴展屬性")

    class Config:
        """Pydantic 配置"""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @validator("valid_to")
    def validate_valid_period(cls, v, values):
        """驗證有效期"""
        if v and "valid_from" in values and values["valid_from"]:
            if v <= values["valid_from"]:
                raise ValueError("valid_to must be after valid_from")
        return v

    def to_graph_properties(self) -> Dict[str, Any]:
        """轉換為圖資料庫屬性格式"""
        props = self.model_dump(exclude={"extra", "source_id", "target_id"})
        props.update(self.extra)
        return props

    @property
    def is_active(self) -> bool:
        """檢查關係是否當前有效"""
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now >= self.valid_to:
            return False
        return True


class CallsRelationship(BaseRelationship):
    """
    函數調用關係

    表示一個函數調用另一個函數的關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.CALLS, frozen=True
    )

    # 調用特性
    call_type: str = Field(
        default="direct", description="調用類型：direct, indirect, recursive"
    )
    call_count: Optional[int] = Field(default=None, description="調用次數（靜態分析）")
    is_conditional: bool = Field(default=False, description="是否為條件調用")

    # 調用位置
    call_line: Optional[int] = Field(default=None, description="調用所在行號")
    call_column: Optional[int] = Field(default=None, description="調用所在列號")

    # 調用上下文
    context: Optional[str] = Field(default=None, description="調用上下文")


class ContainsRelationship(BaseRelationship):
    """
    包含關係

    表示一個實體包含另一個實體的關係，如文件包含函數。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.CONTAINS, frozen=True
    )

    # 包含特性
    container_type: str = Field(description="容器類型：file, class, package")
    position: Optional[int] = Field(default=None, description="在容器中的位置")

    # 可見性
    visibility: str = Field(
        default="public", description="可見性：public, private, protected"
    )


class DependsOnRelationship(BaseRelationship):
    """
    依賴關係

    表示一個實體依賴另一個實體的關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.DEPENDS_ON, frozen=True
    )

    # 依賴特性
    dependency_type: str = Field(
        description="依賴類型：import, inheritance, composition"
    )
    is_optional: bool = Field(default=False, description="是否為可選依賴")

    # 版本約束
    version_constraint: Optional[str] = Field(default=None, description="版本約束")

    # 依賴強度
    strength: str = Field(
        default="strong", description="依賴強度：weak, strong, critical"
    )


class InheritsFromRelationship(BaseRelationship):
    """
    繼承關係

    表示類繼承關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.INHERITS_FROM, frozen=True
    )

    # 繼承特性
    inheritance_type: str = Field(
        default="single", description="繼承類型：single, multiple"
    )
    is_abstract: bool = Field(default=False, description="是否為抽象繼承")

    # 繼承順序（用於多重繼承）
    inheritance_order: Optional[int] = Field(default=None, description="繼承順序")


class ImplementsRelationship(BaseRelationship):
    """
    實現關係

    表示類實現介面的關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.IMPLEMENTS, frozen=True
    )

    # 實現特性
    is_complete: bool = Field(default=True, description="是否完全實現")

    # 實現的方法列表
    implemented_methods: list[str] = Field(
        default_factory=list, description="已實現的方法"
    )
    missing_methods: list[str] = Field(default_factory=list, description="未實現的方法")


class ImportsRelationship(BaseRelationship):
    """
    導入關係

    表示模組導入關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.IMPORTS, frozen=True
    )

    # 導入特性
    import_type: str = Field(description="導入類型：module, from, star")
    alias: Optional[str] = Field(default=None, description="導入別名")

    # 導入的具體項目
    imported_items: list[str] = Field(
        default_factory=list, description="導入的具體項目"
    )

    # 導入位置
    import_line: Optional[int] = Field(default=None, description="導入語句所在行號")


class UsesRelationship(BaseRelationship):
    """
    使用關係

    表示一個實體使用另一個實體的關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.USES, frozen=True
    )

    # 使用特性
    usage_type: str = Field(description="使用類型：variable, type, annotation")
    usage_context: Optional[str] = Field(default=None, description="使用上下文")

    # 使用頻率
    usage_count: Optional[int] = Field(default=None, description="使用次數")


class AppliesToRelationship(BaseRelationship):
    """
    應用關係

    表示約束或規則應用到實體的關係。
    """

    relationship_type: RelationshipType = Field(
        default=RelationshipType.APPLIES_TO, frozen=True
    )

    # 應用特性
    constraint_type: str = Field(description="約束類型")
    severity: str = Field(
        default="medium", description="嚴重程度：low, medium, high, critical"
    )

    # 約束狀態
    is_active: bool = Field(default=True, description="約束是否激活")
    last_checked: Optional[datetime] = Field(default=None, description="最後檢查時間")

    # 違規信息
    violation_count: int = Field(default=0, description="違規次數")
    last_violation: Optional[datetime] = Field(default=None, description="最後違規時間")
