"""
Unit tests for AI Teammate Plug-in Port and strategy plugins.
Verifies that custom analyzer and retriever plugins can be plugged in without
touching database sessions, RBAC, or FastAPI routing.
"""

import pytest

from app.domain.ai_plugin_port import (
    AIPluginRegistry,
    PluginClaimContext,
    PluginDocumentContext,
    PluginRetrievalQuery,
    PluginRetrievedDocument,
)
from app.services.analysis.plugins.default_ai_plugin import (
    DefaultAIAnalyzerPlugin,
    DefaultVectorRetrieverPlugin,
)


@pytest.mark.asyncio
async def test_ai_analyzer_plugin_execution():
    plugin = DefaultAIAnalyzerPlugin()
    assert plugin.plugin_name == "default-heuristic-analyzer"
    assert plugin.plugin_version == "1.0.0"

    context = PluginDocumentContext(
        content_text="This product provides a guaranteed miracle cure and is completely risk-free.",
        brand_name="ShieldHealth",
        prohibited_terms=["cure"],
    )

    result = await plugin.analyze_tone(context)
    assert result.model_name == "default-heuristic-analyzer"
    assert len(result.findings) >= 2

    # Check prohibited claim detection
    prohibited = [f for f in result.findings if f.issue_category == "PROHIBITED_CLAIM"]
    assert len(prohibited) == 1
    assert prohibited[0].severity == "CRITICAL"
    assert prohibited[0].confidence_score == 0.98

    # Check tone hyperbolic phrasing
    tone_findings = [f for f in result.findings if f.issue_category == "TONE"]
    assert len(tone_findings) >= 1


@pytest.mark.asyncio
async def test_ai_claim_verification_grounding_guarantee():
    plugin = DefaultAIAnalyzerPlugin()

    context = PluginClaimContext(
        claims_to_verify=[
            "BrandShield reduces review latency by 85 percent.",
            "Our software makes all compliance officers completely obsolete.",
        ],
        brand_name="BrandShield AI",
        approved_facts=[
            {
                "id": "fact-123",
                "statement": "BrandShield reduces human review latency by 85 percent across enterprise workflows.",
            }
        ],
    )

    findings = await plugin.verify_claims(context)
    assert len(findings) == 2

    # Grounded claim should be VERIFIED
    assert findings[0].verification_status == "VERIFIED"
    assert findings[0].supporting_fact_id == "fact-123"

    # Ungrounded claim MUST be marked NEEDS_VERIFICATION (zero-hallucination guarantee)
    assert findings[1].verification_status == "NEEDS_VERIFICATION"
    assert findings[1].supporting_fact_id is None


@pytest.mark.asyncio
async def test_vector_retriever_plugin():
    retriever = DefaultVectorRetrieverPlugin()
    assert retriever.retriever_name == "default-hash-retriever"

    corpus = [
        PluginRetrievedDocument(
            document_id="doc-1",
            content="Never use absolute superlatives like best, miraculous, or number one in healthcare claims.",
            score=0.0,
        ),
        PluginRetrievedDocument(
            document_id="doc-2",
            content="Annual compliance training is mandatory for all contractors.",
            score=0.0,
        ),
    ]

    query = PluginRetrievalQuery(
        query_text="miraculous superlative healthcare",
        top_k=1,
        similarity_threshold=0.2,
    )

    results = await retriever.retrieve_relevant_guidelines(query, corpus)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"
    assert results[0].score > 0.2


@pytest.mark.asyncio
async def test_ai_plugin_registry():
    import app.services.analysis.plugins  # Ensure all plugins are loaded

    analyzer = AIPluginRegistry.get_analyzer("default-heuristic-analyzer")
    assert analyzer is not None
    assert analyzer.plugin_name == "default-heuristic-analyzer"

    teammate_analyzer = AIPluginRegistry.get_analyzer("teammate-enterprise-analyzer")
    assert teammate_analyzer is not None
    assert teammate_analyzer.plugin_name == "teammate-enterprise-analyzer"

    retriever = AIPluginRegistry.get_retriever("default-hash-retriever")
    assert retriever is not None
    assert retriever.retriever_name == "default-hash-retriever"

    teammate_retriever = AIPluginRegistry.get_retriever("teammate-hybrid-rrf-retriever")
    assert teammate_retriever is not None
    assert teammate_retriever.retriever_name == "teammate-hybrid-rrf-retriever"


@pytest.mark.asyncio
async def test_system_ai_plugins_endpoint():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/ai-plugins")
        assert response.status_code == 200
        data = response.json()
        assert data["active_header"] == "X-AI-Plugin-ID"
        assert data["total_analyzers"] >= 2
        plugin_ids = [a["plugin_id"] for a in data["analyzers"]]
        assert "default-heuristic-analyzer" in plugin_ids
        assert "teammate-enterprise-analyzer" in plugin_ids

