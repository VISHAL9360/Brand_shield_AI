"""
BrandShield AI - AI Teammate Strategy Plugin Template.
================================================================================
ATTENTION AI ROLE TEAMMATE:
Drop your custom prompt chains, vector retrieval weights, and expanded labelled
test cases into this file! You do NOT need to touch FastAPI routers, Pydantic schemas,
or SQLAlchemy async session internals. Everything here integrates automatically via
the AIPluginRegistry port.
================================================================================
"""

import math
import re
import time
from typing import Any, Optional

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

# ==============================================================================
# SECTION 1: CUSTOM PROMPT CHAINS & SYSTEM DIRECTIVES
# ==============================================================================

SYSTEM_COMPLIANCE_DIRECTIVE = """
You are the BrandShield Enterprise Compliance LLM.
Your task is to analyze document passages for brand safety, legal truth-in-advertising,
and tone violations.

Brand Parameters:
- Formality Ceiling: {target_formality}/10
- Voice Tone: {tone_voice}
- Prohibited Terminology: {prohibited_terms}

Output Strict JSON containing:
- category: "TONE" | "TERMINOLOGY" | "MESSAGING"
- severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
- confidence: float (0.0 to 1.0)
- explanation: Detailed rationale
- suggested_rewrite: Context-preserving replacement
"""

FEW_SHOT_DEMONSTRATIONS = [
    {
        "input": "Our product is 100% risk-free with unbeatable performance.",
        "output": {
            "category": "TERMINOLOGY",
            "severity": "CRITICAL",
            "confidence": 0.99,
            "explanation": "Absolute superlatives ('100% risk-free', 'unbeatable') violate SEC and FTC truth-in-advertising guidelines.",
            "suggested_rewrite": "Our product is engineered for managed risk with competitive performance.",
        },
    },
    {
        "input": "We are crazy excited about our insane new features.",
        "output": {
            "category": "TONE",
            "severity": "MEDIUM",
            "confidence": 0.88,
            "explanation": "Colloquial slang ('crazy excited', 'insane') departs from executive B2B tone standards.",
            "suggested_rewrite": "We are proud to introduce our enhanced platform capabilities.",
        },
    },
]


# ==============================================================================
# SECTION 2: CUSTOM AI ANALYZER STRATEGY
# ==============================================================================

class TeammateAIAnalyzerPlugin(BaseAIAnalyzerPlugin):
    """
    AI Teammate plug-in strategy.
    Modify this class to plug in OpenAI, Anthropic, HuggingFace, or custom local models.
    """

    @property
    def plugin_name(self) -> str:
        return "teammate-enterprise-analyzer"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"

    async def analyze_tone(self, context: PluginDocumentContext) -> PluginToneAnalysisResult:
        """
        Executes tone and brand consistency analysis.
        Drop your prompt invocation logic or API router here.
        """
        t0 = time.perf_counter()
        findings: list[PluginToneFinding] = []
        text = context.content_text

        # 1. Terminology scanning using custom parameters
        for term in context.prohibited_terms:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                findings.append(
                    PluginToneFinding(
                        category="TERMINOLOGY",
                        severity="CRITICAL" if "risk-free" in term.lower() or "guarantee" in term.lower() else "HIGH",
                        confidence=0.98,
                        start_offset=m.start(),
                        end_offset=m.end(),
                        excerpt=m.group(0),
                        explanation=f"Term '{m.group(0)}' breaches approved brand matrix.",
                        suggested_rewrite=None,
                        metadata={"rule_id": "CUSTOM_PROMPT_CHAIN"},
                    )
                )

        # 2. Executive Formality Scoring
        words = text.split()
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        formality_score = min(10.0, max(1.0, (avg_word_len * 1.5)))

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return PluginToneAnalysisResult(
            findings=findings,
            formality_score=round(formality_score, 2),
            sentiment_score=0.75,
            processing_duration_ms=round(elapsed_ms, 2),
            plugin_identifier=f"{self.plugin_name}:{self.plugin_version}",
        )

    async def verify_claim(self, context: PluginClaimContext) -> PluginClaimFinding:
        """
        Verifies individual factual claims against candidate evidence facts.
        """
        claim_lower = context.claim_text.lower()
        has_approved_match = False
        matching_fact = None

        for fact in context.candidate_facts:
            stmt = fact.get("statement", "").lower()
            # Simple token overlap or cosine similarity
            if any(token in stmt for token in claim_lower.split() if len(token) > 4):
                has_approved_match = True
                matching_fact = fact
                break

        if has_approved_match and matching_fact:
            return PluginClaimFinding(
                claim_text=context.claim_text,
                is_substantiated=True,
                confidence=0.94,
                grounding_evidence_id=matching_fact.get("id"),
                reason="Claim is directly corroborated by approved corporate repository.",
            )

        return PluginClaimFinding(
            claim_text=context.claim_text,
            is_substantiated=False,
            confidence=0.70,
            grounding_evidence_id=None,
            reason="Needs verification: Claim has no matching citation in approved corporate facts.",
        )


# ==============================================================================
# SECTION 3: CUSTOM RETRIEVAL STRATEGY (DENSE + SPARSE WEIGHTS)
# ==============================================================================

class TeammateVectorRetrieverPlugin(BaseVectorRetrieverPlugin):
    """
    Configurable hybrid retrieval algorithm.
    Tune dense alpha vs sparse beta weights or Reciprocal Rank Fusion parameters.
    """

    def __init__(self, dense_weight: float = 0.65, sparse_weight: float = 0.35, rrf_k: int = 60) -> None:
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k

    @property
    def retriever_name(self) -> str:
        return "teammate-hybrid-rrf-retriever"

    async def rank_candidates(self, query: PluginRetrievalQuery) -> list[PluginRetrievedDocument]:
        """
        Calculates hybrid score = (alpha * dense_cosine) + (beta * sparse_bm25).
        """
        ranked: list[PluginRetrievedDocument] = []
        q_tokens = set(re.findall(r"\w+", query.query_text.lower()))

        for doc in query.candidate_pool:
            doc_tokens = set(re.findall(r"\w+", doc.text.lower()))
            overlap = len(q_tokens & doc_tokens) / max(len(q_tokens), 1)

            # Simulated dense cosine similarity
            dense_sim = 0.85 if overlap > 0.3 else 0.40
            fused_score = (self.dense_weight * dense_sim) + (self.sparse_weight * overlap)

            ranked.append(
                PluginRetrievedDocument(
                    id=doc.id,
                    text=doc.text,
                    score=round(fused_score, 4),
                    metadata={**doc.metadata, "hybrid_algorithm": "tuned_rrf_linear_blend"},
                )
            )

        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked[:query.top_k]


# ==============================================================================
# SECTION 4: EXPANDED LABELLED BENCHMARK TEST CASES
# ==============================================================================

EXPANDED_BENCHMARK_SAMPLES = [
    {
        "sample_id": "EXPANDED-01",
        "title": "Unsubstantiated Competitor Comparison",
        "text": "Acme FinTech processes settlement 10x faster than all competitor banking networks combined.",
        "ground_truth_categories": ["UNSUBSTANTIATED_CLAIM", "TERMINOLOGY"],
    },
    {
        "sample_id": "EXPANDED-02",
        "title": "Compliant Multi-Currency Disclosure",
        "text": "Acme FinTech™ supports multi-currency settlement in USD, EUR, and GBP for verified enterprise accounts.",
        "ground_truth_categories": [],  # Clean passage (True Negative)
    },
]


# ==============================================================================
# SECTION 5: PLUGIN REGISTRATION HELPER
# ==============================================================================

def register_teammate_ai_plugins() -> None:
    """Registers your custom AI plugin components into the BrandShield AI engine."""
    AIPluginRegistry.register_analyzer(TeammateAIAnalyzerPlugin())
    AIPluginRegistry.register_retriever(TeammateVectorRetrieverPlugin())


# Auto-register on import
register_teammate_ai_plugins()
