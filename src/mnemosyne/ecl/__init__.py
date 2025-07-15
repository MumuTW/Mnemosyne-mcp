"""
ECL (Extract, Cognify, Load) 管線模組

提供軟體專案知識圖譜的核心處理管線。
"""

from .cognify import ASTCognifier
from .extractor import FileSystemExtractor
from .loader import GraphLoader
from .pipeline import ECLPipeline

__all__ = ["FileSystemExtractor", "ASTCognifier", "GraphLoader", "ECLPipeline"]
__version__ = "0.1.0"
