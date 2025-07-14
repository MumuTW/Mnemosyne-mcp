"""
Mnemosyne MCP - 數據模型定義

這個模組包含了所有的 Pydantic 數據模型定義，是系統的數據契約。
"""

from .core import (
    BaseEntity,
    File,
    Function,
    Class,
    Package,
    ThirdPartyPackage,
)

from .relationships import (
    BaseRelationship,
    CallsRelationship,
    ContainsRelationship,
    DependsOnRelationship,
    InheritsFromRelationship,
)

from .constraints import (
    Constraint,
    Lock,
    ConstraintType,
    LockStatus,
)

from .api import (
    HealthResponse,
    ErrorResponse,
    IngestRequest,
    IngestResponse,
)

__all__ = [
    # Core entities
    "BaseEntity",
    "File",
    "Function", 
    "Class",
    "Package",
    "ThirdPartyPackage",
    
    # Relationships
    "BaseRelationship",
    "CallsRelationship",
    "ContainsRelationship", 
    "DependsOnRelationship",
    "InheritsFromRelationship",
    
    # Constraints
    "Constraint",
    "Lock",
    "ConstraintType",
    "LockStatus",
    
    # API models
    "HealthResponse",
    "ErrorResponse",
    "IngestRequest",
    "IngestResponse",
]
