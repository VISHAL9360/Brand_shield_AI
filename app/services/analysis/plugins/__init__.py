"""
BrandShield AI - AI Analysis Plugins Package.
Directory where AI team members drop custom analyzer strategies and retrievers.
"""

from app.domain.ai_plugin_port import (
    AIPluginRegistry,
    BaseAIAnalyzerPlugin,
    BaseVectorRetrieverPlugin,
    PluginClaimContext,
    PluginClaimFinding,
    PluginDocumentContext,
    PluginRetrievalQuery,
    PluginRetrievedDocument,
    PluginToneAnalysisResult,
    PluginToneFinding,
)
from app.services.analysis.plugins.default_ai_plugin import (
    DefaultAIAnalyzerPlugin,
    DefaultVectorRetrieverPlugin,
)
from app.services.analysis.plugins.ai_role_template import (
    TeammateAIAnalyzerPlugin,
    TeammateVectorRetrieverPlugin,
)

__all__ = [
    "AIPluginRegistry",
    "BaseAIAnalyzerPlugin",
    "BaseVectorRetrieverPlugin",
    "DefaultAIAnalyzerPlugin",
    "DefaultVectorRetrieverPlugin",
    "PluginClaimContext",
    "PluginClaimFinding",
    "PluginDocumentContext",
    "PluginRetrievalQuery",
    "PluginRetrievedDocument",
    "PluginToneAnalysisResult",
    "PluginToneFinding",
    "TeammateAIAnalyzerPlugin",
    "TeammateVectorRetrieverPlugin",
]
