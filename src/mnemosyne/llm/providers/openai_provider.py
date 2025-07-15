"""
OpenAI 提供者實作

實作 OpenAI API 的 LLM 能力。
"""

import os
from typing import Any, Dict, List, Optional

import structlog

from ..base import EmbeddingResponse, LLMCapability, LLMProvider, LLMResponse

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI 提供者實作

    實作 OpenAI API 的三個核心能力：
    - generation: 使用 gpt-4.1-mini 進行文本生成
    - embedding: 使用 text-embedding-3-small 生成向量嵌入
    - reasoning: 使用 gpt-4.1-nano 進行輕量級推理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 OpenAI 提供者

        Args:
            config: 配置字典，可包含 api_key, embedding_model, generation_model, reasoning_model
        """
        config = config or {}

        # 從環境變數或配置中獲取 API Key
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API Key not provided, some features may not work")

        # 設置默認模型
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self.generation_model = config.get("generation_model", "gpt-4.1-mini")
        self.reasoning_model = config.get("reasoning_model", "gpt-4.1-nano")

        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """初始化 OpenAI 客戶端"""
        try:
            from openai import AsyncOpenAI

            api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API Key not provided, will use mock mode")
                self._client = None  # 設置為 None 表示模擬模式
                return

            self._client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI client initialized with real API")
        except ImportError:
            logger.error("OpenAI package not installed")
            raise

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> LLMResponse:
        """使用 gpt-4.1-mini 生成文本"""
        if not self._client:
            await self.initialize()

        # 模擬實作（用於測試）
        return LLMResponse(
            content=f"Generated text for: {prompt[:50]}...",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    async def generate_embedding(self, text: str, **kwargs) -> EmbeddingResponse:
        """使用 text-embedding-3-small 生成向量嵌入"""
        if not self._client:
            await self.initialize()

        # 模擬實作（用於測試）
        import random

        embedding = [random.random() for _ in range(1536)]  # text-embedding-3-small 的維度

        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
            usage={
                "prompt_tokens": len(text.split()),
                "total_tokens": len(text.split()),
            },
        )

    async def reason(self, context: str, question: str, **kwargs) -> LLMResponse:
        """使用 gpt-4.1-nano 進行輕量級推理"""
        if not self._client:
            await self.initialize()

        # 模擬實作（用於測試）
        return LLMResponse(
            content=f"Reasoning result for question: {question[:30]}... based on context",
            usage={"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40},
        )

    async def health_check(self) -> bool:
        """檢查 OpenAI 服務健康狀態"""
        # 模擬實作（用於測試）
        return True

    @property
    def supported_capabilities(self) -> List[LLMCapability]:
        """返回支援的能力列表"""
        return [
            LLMCapability.GENERATION,
            LLMCapability.EMBEDDING,
            LLMCapability.REASONING,
        ]
