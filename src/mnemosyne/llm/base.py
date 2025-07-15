"""
LLM 能力中心基礎抽象

定義 LLM 提供者的統一介面。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LLMCapability(Enum):
    """LLM 核心能力枚舉"""

    GENERATION = "generation"  # 文本生成
    EMBEDDING = "embedding"  # 向量嵌入
    REASONING = "reasoning"  # 推理判斷


class LLMRequest(BaseModel):
    """LLM 請求基礎模型"""

    capability: LLMCapability
    content: str
    metadata: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """LLM 響應基礎模型"""

    content: str
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None


class EmbeddingResponse(BaseModel):
    """嵌入響應模型"""

    embedding: List[float]
    dimension: int
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    LLM 提供者抽象基類

    定義所有 LLM 提供者必須實現的核心方法。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None

    @abstractmethod
    async def initialize(self) -> None:
        """初始化 LLM 客戶端"""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> LLMResponse:
        """文本生成能力"""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str, **kwargs) -> EmbeddingResponse:
        """向量嵌入能力"""
        pass

    @abstractmethod
    async def reason(self, context: str, question: str, **kwargs) -> LLMResponse:
        """推理判斷能力"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """檢查 LLM 服務健康狀態"""
        pass

    @property
    @abstractmethod
    def supported_capabilities(self) -> List[LLMCapability]:
        """返回支援的能力列表"""
        pass
