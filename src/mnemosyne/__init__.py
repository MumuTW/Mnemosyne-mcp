"""
Mnemosyne MCP - 主動的、有狀態的軟體知識圖譜引擎

這是 Mnemosyne MCP 的主模組，提供了一個統一的入口點。
"""

__version__ = "0.1.0"
__author__ = "Mnemosyne Team"
__description__ = "主動的、有狀態的軟體知識圖譜引擎"

from . import ecl
from .api.main import app
from .core.config import get_settings

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_settings",
    "app",
    "ecl",
]
