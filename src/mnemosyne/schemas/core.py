"""
核心實體數據模型定義

定義了知識圖譜中的核心節點類型，包括 File, Function, Class 等。
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class EntityType(str, Enum):
    """實體類型枚舉"""

    FILE = "File"
    FUNCTION = "Function"
    CLASS = "Class"
    PACKAGE = "Package"
    THIRD_PARTY_PACKAGE = "ThirdPartyPackage"
    VARIABLE = "Variable"
    IMPORT = "Import"


class BaseEntity(BaseModel):
    """
    基礎實體模型

    所有圖譜節點的基礎類，提供通用的屬性和方法。
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="唯一標識符")
    entity_type: EntityType = Field(description="實體類型")
    name: str = Field(description="實體名稱")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")

    # 擴展屬性，用於存儲額外的元數據
    extra: Dict[str, Any] = Field(default_factory=dict, description="擴展屬性")

    class Config:
        """Pydantic 配置"""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @computed_field
    @property
    def unique_key(self) -> str:
        """生成唯一鍵，用於去重和索引"""
        return f"{self.entity_type}:{self.name}"

    def __hash__(self) -> int:
        """支持哈希，用於集合操作"""
        return hash(self.unique_key)

    def __eq__(self, other: object) -> bool:
        """支持相等比較"""
        if not isinstance(other, BaseEntity):
            return False
        return self.unique_key == other.unique_key

    def to_graph_properties(self) -> Dict[str, Any]:
        """轉換為圖資料庫屬性格式"""
        props = self.model_dump(exclude={"extra"})
        props.update(self.extra)
        return props


class File(BaseEntity):
    """
    文件實體模型

    表示程式碼文件，是知識圖譜的基本組織單位。
    """

    entity_type: EntityType = Field(default=EntityType.FILE, frozen=True)
    path: str = Field(description="文件路徑")
    extension: str = Field(description="文件擴展名")
    size_bytes: Optional[int] = Field(default=None, description="文件大小（字節）")
    hash: Optional[str] = Field(default=None, description="文件內容哈希")
    encoding: str = Field(default="utf-8", description="文件編碼")

    # 語言相關屬性
    language: Optional[str] = Field(default=None, description="程式語言")

    @field_validator("extension", mode="before")
    @classmethod
    def normalize_extension(cls, v: str) -> str:
        """標準化文件擴展名"""
        if v and not v.startswith("."):
            return f".{v}"
        return v

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """驗證文件路徑"""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    @computed_field
    @property
    def unique_key(self) -> str:
        """文件的唯一鍵基於路徑"""
        return f"File:{self.path}"

    def calculate_hash(self, content: str) -> str:
        """計算文件內容哈希"""
        return hashlib.sha256(content.encode(self.encoding)).hexdigest()


class Function(BaseEntity):
    """
    函數實體模型

    表示程式碼中的函數或方法。
    """

    entity_type: EntityType = Field(default=EntityType.FUNCTION, frozen=True)
    file_path: str = Field(description="所屬文件路徑")
    line_start: int = Field(description="起始行號")
    line_end: int = Field(description="結束行號")

    # 函數特性
    is_method: bool = Field(default=False, description="是否為類方法")
    is_static: bool = Field(default=False, description="是否為靜態方法")
    is_async: bool = Field(default=False, description="是否為異步函數")
    is_private: bool = Field(default=False, description="是否為私有函數")

    # 函數簽名
    parameters: List[str] = Field(default_factory=list, description="參數列表")
    return_type: Optional[str] = Field(default=None, description="返回類型")

    # 複雜度指標
    cyclomatic_complexity: Optional[int] = Field(default=None, description="循環複雜度")
    lines_of_code: Optional[int] = Field(default=None, description="代碼行數")

    @field_validator("line_start", "line_end")
    @classmethod
    def validate_line_numbers(cls, v: int) -> int:
        """驗證行號"""
        if v < 1:
            raise ValueError("Line numbers must be positive")
        return v

    @field_validator("line_end")
    @classmethod
    def validate_line_end(cls, v: int, info) -> int:
        """驗證結束行號大於起始行號"""
        if info.data.get("line_start") and v < info.data["line_start"]:
            raise ValueError("End line must be greater than or equal to start line")
        return v

    @computed_field
    @property
    def unique_key(self) -> str:
        """函數的唯一鍵基於文件路徑和函數名"""
        return f"Function:{self.file_path}:{self.name}:{self.line_start}"

    @computed_field
    @property
    def signature(self) -> str:
        """生成函數簽名"""
        params = ", ".join(self.parameters)
        return f"{self.name}({params})"


class Class(BaseEntity):
    """
    類實體模型

    表示程式碼中的類定義。
    """

    entity_type: EntityType = Field(default=EntityType.CLASS, frozen=True)
    file_path: str = Field(description="所屬文件路徑")
    line_start: int = Field(description="起始行號")
    line_end: int = Field(description="結束行號")

    # 類特性
    is_abstract: bool = Field(default=False, description="是否為抽象類")
    is_interface: bool = Field(default=False, description="是否為介面")
    is_enum: bool = Field(default=False, description="是否為枚舉")

    # 繼承關係
    base_classes: List[str] = Field(default_factory=list, description="基類列表")

    # 成員統計
    method_count: Optional[int] = Field(default=None, description="方法數量")
    property_count: Optional[int] = Field(default=None, description="屬性數量")

    @computed_field
    @property
    def unique_key(self) -> str:
        """類的唯一鍵基於文件路徑和類名"""
        return f"Class:{self.file_path}:{self.name}"


class Package(BaseEntity):
    """
    包實體模型

    表示程式碼包或模組。
    """

    entity_type: EntityType = Field(default=EntityType.PACKAGE, frozen=True)
    path: str = Field(description="包路徑")
    version: Optional[str] = Field(default=None, description="版本號")

    # 包特性
    is_namespace: bool = Field(default=False, description="是否為命名空間包")

    # 統計信息
    file_count: Optional[int] = Field(default=None, description="包含文件數量")
    subpackage_count: Optional[int] = Field(default=None, description="子包數量")

    @computed_field
    @property
    def unique_key(self) -> str:
        """包的唯一鍵基於路徑"""
        return f"Package:{self.path}"


class ThirdPartyPackage(BaseEntity):
    """
    第三方包實體模型

    表示外部依賴包。
    """

    entity_type: EntityType = Field(default=EntityType.THIRD_PARTY_PACKAGE, frozen=True)
    version: str = Field(description="版本號")

    # 包信息
    registry: str = Field(default="pypi", description="包註冊表")
    license: Optional[str] = Field(default=None, description="授權類型")
    homepage: Optional[str] = Field(default=None, description="主頁URL")
    repository: Optional[str] = Field(default=None, description="倉庫URL")

    # 安全和合規
    security_advisories: List[str] = Field(default_factory=list, description="安全公告")
    deprecated: bool = Field(default=False, description="是否已棄用")

    @computed_field
    @property
    def unique_key(self) -> str:
        """第三方包的唯一鍵基於名稱和版本"""
        return f"ThirdPartyPackage:{self.name}:{self.version}"
