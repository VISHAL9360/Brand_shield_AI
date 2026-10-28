"""
BrandShield AI - Intelligence Analysis & Triage Router.
Exposes endpoints to:
1. Run the 4-Stage Intelligence Pipeline on immutable document revisions (POST /analysis/run).
2. Trigger automated analysis for an entire submission tip (POST /analysis/submissions/{id}/run).
3. Execute real-time ad-hoc compliance checks for live interactive editor feedback (POST /analysis/live).
4. Inspect triaged findings linked to specific revision nodes (GET /analysis/revisions/{id}/findings).
5. Monitor intelligence engine health, circuit breaker, and demo fallback cache (GET /analysis/status).
"""

import asyncio
from datetime import datetime, timezone
import inspect
import time
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictProblem, NotFoundProblem, ValidationErrorProblem
from app.core.security import get_current_user, get_current_user_optional
from app.domain.enums import DetectorSource, FindingCategory, SeverityLevel, TriageStatus
from app.domain.schemas.analysis import (
    AdHocAnalysisRequest,
    AdHocAnalysisResponse,
    AdHocFinding,
    AnalysisEngineStatusResponse,
    AnalysisPipelineResultResponse,
    AnalysisPipelineRunRequest,
    InlinePreflightRequest,
    InlinePreflightResponse,
    InlineSpanHighlight,
)
from app.domain.schemas.finding import FindingRead
from app.infrastructure.db.models import (
    BrandProfile,
    DocumentRevision,
    Finding,
    Submission,
    User,
)
from app.infrastructure.db.session import get_async_session
from app.services.analysis.adversarial_critic import AdversarialCritic
from app.services.analysis.demo_fallback_cache import DemoFallbackCache
from app.services.analysis.deterministic_engine import BrandAutomatonCache, DeterministicRuleEngine
from app.services.analysis.privacy_gate import PrivacyGateRouter
from app.services.analysis.temporal_fact_engine import TemporalFactEngine
from app.services.analysis.triage_orchestrator import TriageOrchestrator

router = APIRouter()
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]


@router.post(
    "/run",
    response_model=AnalysisPipelineResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute 4-Stage Intelligence Pipeline on Revision",
)
@router.post(
    "/",
    response_model=AnalysisPipelineResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute 4-Stage Intelligence Pipeline on Revision",
)
async def run_analysis_pipeline(
    payload: AnalysisPipelineRunRequest,
    current_user: AuthenticatedUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    x_ai_plugin_id: Annotated[Optional[str], Header(alias="X-AI-Plugin-ID")] = None,
) -> AnalysisPipelineResultResponse:
    """
    Executes the 4-stage intelligence pipeline on an immutable document revision:
    1. Deterministic Rule Engine (O(N) Aho-Corasick, Readability, Passive Voice, Caps Abuse).
    2. Temporal Fact & Hybrid RAG Retrieval Engine (RRF, Staleness, Missing Evidence).
    3. Zero-Trust Privacy Gate & Circuit-Breaker LLM Router (PII Scrubber, Cache).
    4. Calibrated Confidence Triage & 15% Stochastic Automation-Bias Safeguard.
    """
    # 1. Resolve Revision & Submission
    revision = await session.get(DocumentRevision, payload.revision_id)
    if not revision:
        raise NotFoundProblem(
            detail=f"DocumentRevision '{payload.revision_id}' not found.",
            resource_type="DocumentRevision",
            resource_id=str(payload.revision_id),
        )

    submission = await session.get(Submission, revision.submission_id)
    if not submission or submission.workspace_id != current_user.workspace_id:
        raise NotFoundProblem(
            detail=f"Submission for revision '{payload.revision_id}' not found in workspace.",
            resource_type="Submission",
            resource_id=str(revision.submission_id),
        )

    target_profile_id = payload.brand_profile_id or submission.brand_profile_id
    profile = await session.get(BrandProfile, target_profile_id)
    if not profile or profile.workspace_id != current_user.workspace_id:
        raise NotFoundProblem(
            detail=f"Brand profile '{target_profile_id}' not found in workspace.",
            resource_type="BrandProfile",
            resource_id=str(target_profile_id),
        )

    # 2. Execute Pipeline
    kwargs = {
        "session": session,
        "revision_id": revision.id,
        "brand_profile_id": profile.id,
        "workspace_id": current_user.workspace_id,
        "content_text": revision.content_text,
        "requested_provider": payload.requested_provider,
        "preloaded_profile": profile,
        "ai_plugin_id": x_ai_plugin_id,
    }
    if payload.audit_sample_rate is not None:
        kwargs["audit_sample_rate"] = payload.audit_sample_rate

    pipeline_result = await TriageOrchestrator.run_pipeline(**kwargs)

    # 3. Compile Response
    finding_reads = [FindingRead.model_validate(f) for f in pipeline_result.findings]

    return AnalysisPipelineResultResponse(
        revision_id=revision.id,
        submission_id=submission.id,
        total_findings=pipeline_result.total_findings,
        flagged_high_confidence=pipeline_result.flagged_high_confidence,
        routed_to_human_low_confidence=pipeline_result.routed_to_human_low_confidence,
        stale_facts_to_reverify=pipeline_result.stale_facts_to_reverify,
        needs_verification_missing_evidence=pipeline_result.needs_verification_missing_evidence,
        automation_bias_audits_injected=pipeline_result.automation_bias_audits_injected,
        suppressed_false_positives_count=getattr(pipeline_result, "suppressed_false_positives_count", 0),
        processing_duration_ms=pipeline_result.processing_duration_ms,
        findings=finding_reads,
    )


@router.post(
    "/submissions/{submission_id}/run",
    response_model=AnalysisPipelineResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Pipeline on Latest Submission Head Revision",
)
async def run_analysis_for_submission(
    submission_id: uuid.UUID,
    current_user: AuthenticatedUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    requested_provider: str = Query(default="Azure OpenAI"),
    x_ai_plugin_id: Annotated[Optional[str], Header(alias="X-AI-Plugin-ID")] = None,
) -> AnalysisPipelineResultResponse:
    """
    Convenience endpoint triggering compliance analysis on the active head revision of a submission.
    """
    submission = await session.get(Submission, submission_id)
    if not submission or submission.workspace_id != current_user.workspace_id:
        raise NotFoundProblem(
            detail=f"Submission '{submission_id}' not found in workspace.",
            resource_type="Submission",
            resource_id=str(submission_id),
        )

    if not submission.current_revision_id:
        raise ConflictProblem(
            detail=f"Submission '{submission_id}' has no committed head revision.",
            conflicting_field="current_revision_id",
        )

    run_payload = AnalysisPipelineRunRequest(
        revision_id=submission.current_revision_id,
        brand_profile_id=submission.brand_profile_id,
        requested_provider=requested_provider,
    )
    return await run_analysis_pipeline(
        payload=run_payload,
        current_user=current_user,
        session=session,
        x_ai_plugin_id=x_ai_plugin_id,
    )


@router.post(
    "/live",
    response_model=AdHocAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Real-Time Ad-Hoc Text Analysis for Live Editor",
)
async def analyze_live_text(
    payload: AdHocAnalysisRequest,
    current_user: AuthenticatedUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AdHocAnalysisResponse:
    """
    Executes real-time, non-persisted compliance analysis on raw text.
    Powers the interactive document editor with instantaneous feedback:
    - Runs O(N) deterministic terminology & tone automata (<2ms).
    - Checks ground-truth approved facts for temporal staleness.
    - Evaluates privacy-gated tone checks without creating database revisions.
    """
    start_time = time.perf_counter()

    profile = await session.get(BrandProfile, payload.brand_profile_id)
    if not profile or profile.workspace_id != current_user.workspace_id:
        raise NotFoundProblem(
            detail=f"Brand profile '{payload.brand_profile_id}' not found in workspace.",
            resource_type="BrandProfile",
            resource_id=str(payload.brand_profile_id),
        )

    # 1. Deterministic Rule Hits
    deterministic_hits = DeterministicRuleEngine.analyze_document(
        content_text=payload.content_text,
        brand_profile=profile,
    )

    # 2. Temporal Fact Verification
    temporal_hits = await TemporalFactEngine.evaluate_claims(
        content_text=payload.content_text,
        workspace_id=current_user.workspace_id,
        session=session,
    )

    # 3. Privacy Gated Tone Analysis
    tone_hits = await PrivacyGateRouter.analyze_tone_and_messaging(
        content_text=payload.content_text,
        brand_profile=profile,
        workspace_id=current_user.workspace_id,
        session=session,
        requested_provider=payload.requested_provider,
    )

    findings: list[AdHocFinding] = []

    for d in deterministic_hits:
        findings.append(
            AdHocFinding(
                issue_category=d.issue_category,
                severity=d.severity,
                confidence_score=1.0,
                triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
                start_offset=d.start_offset,
                end_offset=d.end_offset,
                explanation_reason=d.explanation_reason,
                suggested_correction=d.suggested_correction,
                detector_source=d.detector_source.value if hasattr(d.detector_source, "value") else str(d.detector_source),
                is_automation_bias_audit=False,
            )
        )

    for t in temporal_hits:
        findings.append(
            AdHocFinding(
                issue_category=t.issue_category,
                severity=t.severity,
                confidence_score=t.confidence_score,
                triage_status=t.triage_status,
                start_offset=t.start_offset,
                end_offset=t.end_offset,
                explanation_reason=t.explanation_reason,
                suggested_correction=t.suggested_correction,
                detector_source=t.detector_source.value if hasattr(t.detector_source, "value") else str(t.detector_source),
                is_automation_bias_audit=False,
            )
        )

    for tone in tone_hits:
        if tone.confidence_score >= 0.40:
            status_val = (
                TriageStatus.FLAGGED_HIGH_CONFIDENCE
                if tone.confidence_score >= 0.85
                else TriageStatus.ROUTED_TO_HUMAN_LOW_CONFIDENCE
            )
            findings.append(
                AdHocFinding(
                    issue_category=tone.issue_category,
                    severity=tone.severity,
                    confidence_score=tone.confidence_score,
                    triage_status=status_val,
                    start_offset=tone.start_offset,
                    end_offset=tone.end_offset,
                    explanation_reason=tone.explanation_reason,
                    suggested_correction=tone.suggested_correction,
                    detector_source=tone.detector_source.value if hasattr(tone.detector_source, "value") else str(tone.detector_source),
                    is_automation_bias_audit=False,
                )
            )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return AdHocAnalysisResponse(
        brand_profile_id=payload.brand_profile_id,
        total_findings=len(findings),
        processing_duration_ms=duration_ms,
        findings=findings,
    )


@router.get(
    "/revisions/{revision_id}/findings",
    response_model=list[FindingRead],
    status_code=status.HTTP_200_OK,
    summary="List Triaged Findings for Document Revision",
)
async def list_revision_findings(
    revision_id: uuid.UUID,
    current_user: AuthenticatedUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    triage_status: Optional[TriageStatus] = Query(default=None, description="Filter by triage status"),
    issue_category: Optional[FindingCategory] = Query(default=None, description="Filter by category"),
    severity: Optional[SeverityLevel] = Query(default=None, description="Filter by severity"),
) -> list[Finding]:
    """
    Retrieves all compliance findings detected on a specific document revision,
    sorted by character start offset for precise inline document highlighting.
    """
    revision = await session.get(DocumentRevision, revision_id)
    if not revision:
        raise NotFoundProblem(
            detail=f"DocumentRevision '{revision_id}' not found.",
            resource_type="DocumentRevision",
            resource_id=str(revision_id),
        )

    submission = await session.get(Submission, revision.submission_id)
    if not submission or submission.workspace_id != current_user.workspace_id:
        raise NotFoundProblem(
            detail=f"Submission for revision '{revision_id}' not found in workspace.",
            resource_type="Submission",
            resource_id=str(revision.submission_id),
        )

    query = (
        select(Finding)
        .where(Finding.revision_id == revision_id)
        .order_by(Finding.start_offset.asc())
    )
    if triage_status:
        query = query.where(Finding.triage_status == triage_status)
    if issue_category:
        query = query.where(Finding.issue_category == issue_category)
    if severity:
        query = query.where(Finding.severity == severity)

    result = await session.execute(query)
    return list(result.scalars().all())


@router.get(
    "/status",
    response_model=AnalysisEngineStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Intelligence Engine Operational Status",
)
async def get_analysis_engine_status(
    current_user: AuthenticatedUser,
) -> AnalysisEngineStatusResponse:
    """
    Inspects operational health of the analysis pipeline:
    - Circuit breaker state for external LLM inference.
    - Demo fallback cache pre-warmed entries count.
    - Supported Zero-Trust inference providers.
    """
    cb_available = PrivacyGateRouter.circuit_breaker.is_available()
    cb_state = PrivacyGateRouter.circuit_breaker.state

    return AnalysisEngineStatusResponse(
        circuit_breaker_state=cb_state,
        circuit_breaker_available=cb_available,
        fallback_cache_size=DemoFallbackCache.get_cache_size(),
    )


@router.post(
    "/preflight-inline",
    response_model=InlinePreflightResponse,
    status_code=status.HTTP_200_OK,
    summary="Sub-10ms Live-Typing Inline Co-Pilot Preflight",
)
async def preflight_inline(
    payload: InlinePreflightRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: OptionalUser = None,
) -> InlinePreflightResponse:
    """
    Sub-10ms stateless, zero-DB-write endpoint powered by L1 BrandAutomatonCache.
    Evaluates real-time keystroke snippets against pre-compiled Aho-Corasick state machines
    and the Adversarial Critic false-positive filter, returning span highlights and suggestions in <5ms.
    """
    t0 = time.perf_counter()
    snippet = payload.text_snippet or ""

    # 1. Resolve L1 In-Memory Automaton Bundle
    bundle = None
    for (prof_id, _), b in BrandAutomatonCache._cache.items():
        if str(prof_id) == str(payload.brand_profile_id):
            bundle = b
            break

    # Cold cache fallback: warm bundle once from DB if not yet compiled in memory
    if not bundle:
        profile = await session.get(BrandProfile, payload.brand_profile_id)
        if profile:
            from app.infrastructure.db.models import BrandGuideline
            g_res = await session.execute(
                select(BrandGuideline).where(
                    BrandGuideline.brand_profile_id == payload.brand_profile_id,
                    BrandGuideline.is_active == True,  # noqa: E712
                )
            )
            scalars_obj = g_res.scalars() if hasattr(g_res, "scalars") else None
            if asyncio.iscoroutine(scalars_obj):
                scalars_obj = await scalars_obj
            if scalars_obj and hasattr(scalars_obj, "all"):
                all_res = scalars_obj.all()
                if asyncio.iscoroutine(all_res):
                    all_res = await all_res
                guidelines = list(all_res)
            else:
                guidelines = []
            bundle = BrandAutomatonCache.get_or_compile(profile, guidelines)

    raw_highlights: list[InlineSpanHighlight] = []

    if bundle:
        # 2. O(N) Multi-Pattern String Matching via L1 Automaton
        ci_matches = bundle.ci_automaton.search(snippet)
        for start, end, match_payload in ci_matches:
            raw_highlights.append(
                InlineSpanHighlight(
                    start_offset=start,
                    end_offset=end,
                    matched_term=match_payload.term,
                    issue_category=match_payload.category,
                    severity=match_payload.severity,
                    explanation_reason=match_payload.reason,
                    suggested_replacement=match_payload.suggested_correction,
                    confidence_score=1.0,
                )
            )

        cs_matches = bundle.cs_automaton.search(snippet)
        for start, end, match_payload in cs_matches:
            raw_highlights.append(
                InlineSpanHighlight(
                    start_offset=start,
                    end_offset=end,
                    matched_term=match_payload.term,
                    issue_category=match_payload.category,
                    severity=match_payload.severity,
                    explanation_reason=match_payload.reason,
                    suggested_replacement=match_payload.suggested_correction,
                    confidence_score=1.0,
                )
            )

    # 3. Adversarial False-Positive Filtration for Real-Time Typing
    # Suppresses false alarms (e.g. author typing "We do not claim X" or quoted competitor phrases)
    clean_highlights: list[InlineSpanHighlight] = []
    for h in raw_highlights:
        surrogate = Finding(
            start_offset=h.start_offset,
            end_offset=h.end_offset,
            issue_category=h.issue_category,
            severity=h.severity,
            confidence_score=h.confidence_score,
            explanation_reason=h.explanation_reason,
            detector_source=DetectorSource.DETERMINISTIC_RULE,
        )
        is_fp, _ = AdversarialCritic.evaluate_false_positive(snippet, surrogate)
        if not is_fp:
            uncertainty = AdversarialCritic.compute_epistemic_uncertainty(surrogate, snippet)
            h.epistemic_uncertainty_score = uncertainty
            h.counterfactual_risk_summary = AdversarialCritic.generate_counterfactual_risk_summary(surrogate, h.matched_term)
            h.start_char = h.start_offset
            h.end_char = h.end_offset
            h.flagged_text = h.matched_term
            h.suggested_correction = h.suggested_replacement
            clean_highlights.append(h)

    # Deduplicate and sort highlights by character offset
    clean_highlights.sort(key=lambda x: (x.start_offset, -(x.end_offset - x.start_offset)))

    latency_ms = round((time.perf_counter() - t0) * 1000, 3)
    replacements_count = sum(1 for h in clean_highlights if h.suggested_replacement)

    is_compliant = (len(clean_highlights) == 0)

    return InlinePreflightResponse(
        latency_ms=latency_ms,
        clean_pass=is_compliant,
        character_count=len(snippet),
        span_highlights=clean_highlights,
        suggested_replacements_count=replacements_count,
        is_compliant=is_compliant,
        total_spans_detected=len(clean_highlights),
        spans=clean_highlights,
    )
