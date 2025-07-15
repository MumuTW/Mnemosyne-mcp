"""
gRPC 服務模組

提供 Atlassian 知識提取的 gRPC 服務實現。
"""

from .atlassian_service_simple import AtlassianKnowledgeExtractorService

__all__ = ["AtlassianKnowledgeExtractorService"]
