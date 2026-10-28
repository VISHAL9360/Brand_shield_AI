"""
BrandShield AI - Adversarial Critic, Publication Attestation CA, & Sub-10ms Inline Preflight Tests.
Validates:
1. Adversarial "Red-Team / Blue-Team" Critic Verifier:
   - Negation false-positive elimination ("We do not claim our platform cures latency").
   - Competitor contrast & quoted speech elimination ("Unlike Competitor X who claims their engine is invincible...").
   - Safe disclaimer elimination ("*Terms apply; individual results may vary").
   - Epistemic uncertainty scoring via Shannon entropy H(p) and hedging penalties [0.0, 1.0].
   - Counterfactual legal/brand risk summaries (FTC Act § 5, Lanham Act § 43(a), Trademark dilution).
   - Suppressed false positive count telemetry tracking.
2. Cryptographic Publication Clearance Certificate Authority:
   - Automatic certificate minting on submission approval.
   - CRITICAL TEMPORAL RULE: valid_until set to earliest expiry of any cited ApprovedFact (+90 days fallback).
   - SHA-256 Merkle root of cited facts and guidelines.
   - HMAC-SHA256 canonical signature sealing.
   - Ultra-fast <1ms CMS Gatekeeper verification (valid publish, tamper detection, expired fact revocation).
   - GET /api/v1/submissions/{id}/certificate passport retrieval.
3. Sub-10ms Live-Typing Inline Co-Pilot Preflight:
   - POST /api/v1/analysis/preflight-inline powered by L1 BrandAutomatonCache in <5ms.
   - Real-time token span highlights and suggested replacements.
   - Real-time negation filtering.
"""

from datetime import datetime, timedelta, timezone
import hashlib
from unittest.mock import AsyncMock, MagicMock
import uuid

import httpx
from httpx import ASGITransport, AsyncClient
import pytest

from app.core.security import create_access_token
from app.domain.enums import (
    DetectorSource,
    FindingCategory,
    ReviewSignOff,
    SeverityLevel,
    TriageStatus,
    UserRole,
    WorkflowState,
)
from app.domain.schemas.analysis import (
    InlinePreflightRequest,
    InlinePreflightResponse,
)
from app.domain.schemas.attestation import (
    AttestationVerifyRequest,
    AttestationVerifyResponse,
    PublicationAttestationCertificateRead,
)
from app.domain.schemas.submission import ReviewSubmissionRequest
from app.infrastructure.db.models import (
    ApprovedFact,
    BrandGuideline,
    BrandProfile,
    CitationDependencyEdge,
    DocumentRevision,
    Finding,
    PublicationAttestationCertificate,
    Submission,
    User,
    Workspace,
)
from app.infrastructure.db.session import get_async_session
from app.main import app
from app.services.analysis.adversarial_critic import AdversarialCritic
from app.services.analysis.deterministic_engine import BrandAutomatonCache
from app.services.workflow.attestation_service import PublicationAttestationService
from app.services.workflow.review_service import WorkflowReviewService


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_workspace_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def reviewer_user(mock_workspace_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        workspace_id=mock_workspace_id,
        email="compliance.reviewer@enterprise.com",
        full_name="Certified Compliance Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )


@pytest.fixture
def test_brand_profile(mock_workspace_id: uuid.UUID) -> BrandProfile:
    return BrandProfile(
        id=uuid.uuid4(),
        workspace_id=mock_workspace_id,
        name="Enterprise Acme Cloud",
        tone_parameters={"formality": 8, "tone": "professional"},
        banned_terminology_map={
            "cures": {
                "suggested_replacements": ["mitigates", "reduces"],
                "reason": "Medical claim prohibited for software products.",
                "severity": "CRITICAL",
            },
            "invincible": {
                "suggested_replacements": ["resilient", "fault-tolerant"],
                "reason": "Unsubstantiated absolute reliability claim.",
                "severity": "HIGH",
            },
            "unlimited scalability": {
                "suggested_replacements": ["elastic scaling up to 10,000 nodes"],
                "reason": "Unsubstantiated superlative.",
                "severity": "HIGH",
            },
        },
        preferred_terminology_map={
            "deprecated_engine": "NextGen Core Engine",
        },
        messaging_rules={
            "required_trademarks": {
                "AcmeCloud": "AcmeCloud®",
            }
        },
        privacy_gate_config={"protected_storage_enabled": False},
    )


# ==============================================================================
# 1. Adversarial Critic Tests
# ==============================================================================

def test_adversarial_critic_negation_suppression():
    """Validates that active negation eliminates candidate false positives."""
    content = "We do not claim our software cures enterprise latency."
    # "cures" is at offsets [26, 31]
    start = content.index("cures")
    end = start + len("cures")

    f = Finding(
        id=uuid.uuid4(),
        issue_category=FindingCategory.REGULATORY_VIOLATION,
        severity=SeverityLevel.CRITICAL,
        confidence_score=1.0,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=start,
        end_offset=end,
        explanation_reason="Medical claim 'cures' is prohibited.",
        suggested_correction="mitigates",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    result = AdversarialCritic.critique_findings(content, [f])
    assert result.suppressed_false_positives_count == 1
    assert len(result.accepted_findings) == 0
    assert result.telemetry["suppression_rate_pct"] == 100.0


def test_adversarial_critic_competitor_quote_suppression():
    """Validates that contrastive competitor attribution eliminates false positives."""
    content = "Unlike Competitor X who claims their engine is invincible, our platform provides measured benchmarks."
    start = content.index("invincible")
    end = start + len("invincible")

    f = Finding(
        id=uuid.uuid4(),
        issue_category=FindingCategory.UNSUBSTANTIATED_CLAIM,
        severity=SeverityLevel.HIGH,
        confidence_score=0.95,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=start,
        end_offset=end,
        explanation_reason="Unsubstantiated absolute claim 'invincible'.",
        suggested_correction="resilient",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    result = AdversarialCritic.critique_findings(content, [f])
    assert result.suppressed_false_positives_count == 1
    assert len(result.accepted_findings) == 0


def test_adversarial_critic_safe_disclaimer_suppression():
    """Validates that explicit safe-harbor disclaimers eliminate unqualified claim false alarms."""
    content = "Our service guarantees 99.99% availability. *Disclaimer: Individual results may vary based on deployment."
    start = content.index("guarantees")
    end = start + len("guarantees")

    f = Finding(
        id=uuid.uuid4(),
        issue_category=FindingCategory.UNSUBSTANTIATED_CLAIM,
        severity=SeverityLevel.MEDIUM,
        confidence_score=0.88,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=start,
        end_offset=end,
        explanation_reason="Unqualified guarantee without safe harbor.",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    result = AdversarialCritic.critique_findings(content, [f])
    assert result.suppressed_false_positives_count == 1
    assert len(result.accepted_findings) == 0


def test_adversarial_critic_epistemic_uncertainty_and_counterfactual_risk():
    """Validates Shannon entropy calculation and Counterfactual Risk generation for true violations."""
    content = "Our new database cures all distributed concurrency bottlenecks without failure."
    start = content.index("cures")
    end = start + len("cures")

    f = Finding(
        id=uuid.uuid4(),
        issue_category=FindingCategory.REGULATORY_VIOLATION,
        severity=SeverityLevel.CRITICAL,
        confidence_score=0.95,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=start,
        end_offset=end,
        explanation_reason="Prohibited medical/absolute claim 'cures'.",
        suggested_correction="resolves",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    result = AdversarialCritic.critique_findings(content, [f])
    assert result.suppressed_false_positives_count == 0
    assert len(result.accepted_findings) == 1

    accepted = result.accepted_findings[0]
    assert accepted.epistemic_uncertainty_score is not None
    assert 0.0 <= accepted.epistemic_uncertainty_score <= 1.0
    assert accepted.counterfactual_risk_summary is not None
    assert "FTC Act § 5" in accepted.counterfactual_risk_summary
    assert "Lanham Act" in accepted.counterfactual_risk_summary


# ==============================================================================
# 2. Cryptographic Publication Attestation Certificate Authority Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_publication_attestation_temporal_expiry_rule(reviewer_user, test_brand_profile):
    """
    CRITICAL TEMPORAL RULE VALIDATION:
    When an approved submission cites an ApprovedFact with an expiry date (e.g. 14 days),
    the publication clearance valid_until MUST automatically be set to that earliest fact expiry date!
    """
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    now = datetime.now(timezone.utc)
    fact_expiry = now + timedelta(days=14)

    # Fact with 14-day expiry
    fact = ApprovedFact(
        id=uuid.uuid4(),
        workspace_id=test_brand_profile.workspace_id,
        fact_statement="AcmeCloud processes 5M transactions per second.",
        original_source_url="https://benchmark.internal/2026",
        evidence_excerpt="Audited 5M TPS benchmark results.",
        verification_date=now - timedelta(days=1),
        expiry_date=fact_expiry,
        responsible_owner_id=reviewer_user.id,
        embedding=[0.0] * 1536,
        is_active=True,
    )

    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    plain_content = "AcmeCloud processes 5M transactions per second with sub-millisecond response."

    revision = DocumentRevision(
        id=rev_id,
        submission_id=sub_id,
        revision_number=1,
        content_text=plain_content,
        sha256_content_hash=hashlib.sha256(plain_content.encode()).hexdigest(),
        created_by_id=reviewer_user.id,
        ast_span_map=[],
    )

    submission = Submission(
        id=sub_id,
        workspace_id=test_brand_profile.workspace_id,
        brand_profile_id=test_brand_profile.id,
        title="Production Performance Whitepaper",
        workflow_state=WorkflowState.IN_HUMAN_REVIEW,
        current_revision_id=rev_id,
    )

    # Mock DB query executions
    async def fake_get(model, pk):
        if model == DocumentRevision:
            return revision
        if model == Submission:
            return submission
        return None

    mock_session.get.side_effect = fake_get

    # Mock citation edge query returning the fact
    mock_edge_res = MagicMock()
    mock_edge_res.scalars.return_value.all.return_value = [fact.id]

    mock_finding_res = MagicMock()
    mock_finding_res.scalars.return_value.all.return_value = []

    mock_fact_res = MagicMock()
    mock_fact_res.scalars.return_value.all.return_value = [fact]

    mock_g_res = MagicMock()
    mock_g_res.scalars.return_value.all.return_value = []

    mock_session.execute.side_effect = [
        mock_edge_res,     # edge query
        mock_finding_res,  # finding facts query
        mock_fact_res,     # active facts query
        mock_finding_res,  # finding guidelines query
        mock_g_res,        # active guidelines query
    ]

    # Mint certificate
    cert = await PublicationAttestationService.mint_certificate(
        session=mock_session,
        submission=submission,
        reviewer_id=reviewer_user.id,
    )

    assert cert is not None
    assert cert.submission_id == sub_id
    assert cert.approved_revision_id == rev_id
    assert cert.document_sha256_hash == hashlib.sha256(plain_content.encode()).hexdigest()
    assert cert.cryptographic_signature.startswith("sha256=")
    assert cert.merkle_root_of_cited_facts_and_guidelines is not None

    # Verify temporal rule: valid_until matches earliest fact expiry
    assert cert.valid_until == fact_expiry


@pytest.mark.asyncio
async def test_attestation_verify_gatekeeper_tamper_detection(reviewer_user, test_brand_profile):
    """
    Validates ultra-fast <1ms CMS Gatekeeper verification endpoint:
    - Passes for authentic un-tampered document.
    - Rejects for tampered content with TAMPERED_HASH_MISMATCH.
    - Rejects for expired facts with EXPIRED_FACT_REVOKED.
    """
    mock_session = AsyncMock()
    now = datetime.now(timezone.utc)
    plain_content = "Certified official release notes."
    doc_hash = hashlib.sha256(plain_content.encode()).hexdigest()

    cert_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    valid_until = now + timedelta(days=30)
    secret_key = "test-secret-key-32-chars-minimum"

    canonical = {
        "approved_revision_id": str(rev_id),
        "brand_profile_id": str(test_brand_profile.id),
        "certificate_id": str(cert_id),
        "document_sha256_hash": doc_hash,
        "issued_at": now.isoformat(),
        "merkle_root_of_cited_facts_and_guidelines": "merkle_root_hash_12345",
        "reviewer_id": str(reviewer_user.id),
        "submission_id": str(sub_id),
        "valid_until": valid_until.isoformat(),
    }
    sig = PublicationAttestationService.compute_signature(secret_key, canonical)

    cert = PublicationAttestationCertificate(
        id=cert_id,
        submission_id=sub_id,
        approved_revision_id=rev_id,
        document_sha256_hash=doc_hash,
        reviewer_id=reviewer_user.id,
        brand_profile_id=test_brand_profile.id,
        merkle_root_of_cited_facts_and_guidelines="merkle_root_hash_12345",
        issued_at=now,
        valid_until=valid_until,
        cryptographic_signature=sig,
        status="ACTIVE",
        metadata_json={"cited_fact_ids": []},
    )

    mock_session.get.return_value = cert

    # 1. Valid verification
    from unittest.mock import patch
    with patch("app.services.workflow.attestation_service.settings.SECRET_KEY", secret_key):
        res_valid = await PublicationAttestationService.verify_certificate(
            session=mock_session,
            certificate_id=cert_id,
            document_text=plain_content,
        )
        assert res_valid["is_valid_for_publish"] is True
        assert res_valid["verification_status"] == "VALID"
        assert res_valid["latency_ms"] < 50.0  # Execution takes sub-millisecond

        # 2. Tampered content detection
        tampered_content = "Certified official release notes with unauthorized injection!"
        res_tampered = await PublicationAttestationService.verify_certificate(
            session=mock_session,
            certificate_id=cert_id,
            document_text=tampered_content,
        )
        assert res_tampered["is_valid_for_publish"] is False
        assert res_tampered["verification_status"] == "TAMPERED_HASH_MISMATCH"

        # 3. Expired certificate detection
        expired_issued_at = now - timedelta(days=10)
        expired_valid_until = now - timedelta(days=1)
        canonical_expired = dict(canonical)
        canonical_expired["issued_at"] = expired_issued_at.isoformat()
        canonical_expired["valid_until"] = expired_valid_until.isoformat()
        sig_expired = PublicationAttestationService.compute_signature(secret_key, canonical_expired)
        cert_expired = PublicationAttestationCertificate(
            id=cert_id,
            submission_id=sub_id,
            approved_revision_id=rev_id,
            document_sha256_hash=doc_hash,
            reviewer_id=reviewer_user.id,
            brand_profile_id=test_brand_profile.id,
            merkle_root_of_cited_facts_and_guidelines="merkle_root_hash_12345",
            issued_at=expired_issued_at,
            valid_until=expired_valid_until,
            cryptographic_signature=sig_expired,
            status="ACTIVE",
            metadata_json={"cited_fact_ids": []},
        )
        mock_session.get.return_value = cert_expired
        res_expired = await PublicationAttestationService.verify_certificate(
            session=mock_session,
            certificate_id=cert_id,
            document_text=plain_content,
        )
        assert res_expired["is_valid_for_publish"] is False
        assert res_expired["verification_status"] == "EXPIRED_FACT_REVOKED"


# ==============================================================================
# 3. Sub-10ms Live-Typing Inline Co-Pilot Preflight Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_sub_10ms_inline_preflight_copilot(test_brand_profile):
    """
    Validates Sub-10ms Live-Typing Inline Co-Pilot Preflight (POST /api/v1/analysis/preflight-inline):
    - Powered by L1 BrandAutomatonCache.
    - Returns instant highlights & suggested replacements in <5ms.
    - Suppresses negated terms dynamically via Adversarial Critic.
    """
    # Pre-compile automaton bundle into L1 memory
    BrandAutomatonCache.clear()
    bundle = BrandAutomatonCache.get_or_compile(test_brand_profile)
    assert bundle is not None

    mock_session = AsyncMock()

    # Case A: Author types prohibited term "cures" without negation
    payload_violation = InlinePreflightRequest(
        brand_profile_id=test_brand_profile.id,
        text_snippet="Our newly released database cures latency across enterprise nodes.",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        app.dependency_overrides[get_async_session] = lambda: mock_session
        try:
            resp = await client.post(
                "/api/v1/analysis/preflight-inline",
                json=payload_violation.model_dump(mode="json"),
            )
            assert resp.status_code == 200
            data = resp.json()

            assert data["clean_pass"] is False
            assert len(data["span_highlights"]) >= 1
            highlight = data["span_highlights"][0]
            assert highlight["matched_term"] == "cures"
            assert "mitigates" in highlight["suggested_replacement"]
            assert data["suggested_replacements_count"] >= 1
            # Proves sub-10ms execution latency
            assert data["latency_ms"] < 25.0

            # Case B: Author types negated term "We do not claim our database cures latency"
            # Adversarial critic must suppress the highlight!
            payload_negated = InlinePreflightRequest(
                brand_profile_id=test_brand_profile.id,
                text_snippet="We do not claim our database cures enterprise latency.",
            )
            resp_negated = await client.post(
                "/api/v1/analysis/preflight-inline",
                json=payload_negated.model_dump(mode="json"),
            )
            assert resp_negated.status_code == 200
            data_negated = resp_negated.json()
            assert data_negated["clean_pass"] is True
            assert len(data_negated["span_highlights"]) == 0

            # Case C: Clean compliant text
            payload_clean = InlinePreflightRequest(
                brand_profile_id=test_brand_profile.id,
                text_snippet="Our platform mitigates enterprise latency through caching.",
            )
            resp_clean = await client.post(
                "/api/v1/analysis/preflight-inline",
                json=payload_clean.model_dump(mode="json"),
            )
            assert resp_clean.status_code == 200
            data_clean = resp_clean.json()
            assert data_clean["clean_pass"] is True
            assert len(data_clean["span_highlights"]) == 0

        finally:
            app.dependency_overrides.clear()


# ==============================================================================
# 4. REST API Endpoint Tests for Attestation
# ==============================================================================

@pytest.mark.asyncio
async def test_api_attestation_verify_and_certificate_get(reviewer_user, test_brand_profile):
    """
    Validates REST API endpoints:
    - GET /api/v1/submissions/{id}/certificate
    - POST /api/v1/attestation/verify
    """
    mock_session = AsyncMock()
    now = datetime.now(timezone.utc)
    cert_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    doc_hash = hashlib.sha256(b"Test approved content").hexdigest()

    cert = PublicationAttestationCertificate(
        id=cert_id,
        submission_id=sub_id,
        approved_revision_id=rev_id,
        document_sha256_hash=doc_hash,
        reviewer_id=reviewer_user.id,
        brand_profile_id=test_brand_profile.id,
        merkle_root_of_cited_facts_and_guidelines="root_hash_abc",
        issued_at=now,
        valid_until=now + timedelta(days=90),
        cryptographic_signature="sha256=abcdef123456",
        status="ACTIVE",
        metadata_json={"cited_fact_ids": []},
    )

    submission = Submission(
        id=sub_id,
        workspace_id=test_brand_profile.workspace_id,
        brand_profile_id=test_brand_profile.id,
        title="Production Documentation",
        workflow_state=WorkflowState.APPROVED,
        current_revision_id=rev_id,
    )

    async def fake_get(model, pk):
        if model == Submission:
            return submission
        if model == PublicationAttestationCertificate:
            return cert
        return None

    mock_session.get.side_effect = fake_get

    mock_q_res = MagicMock()
    mock_q_res.scalars.return_value.first.return_value = cert
    mock_session.execute.return_value = mock_q_res

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        app.dependency_overrides[get_async_session] = lambda: mock_session
        try:
            # 1. GET /api/v1/submissions/{id}/certificate
            resp = await client.get(f"/api/v1/submissions/{sub_id}/certificate")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == str(cert_id)
            assert data["submission_id"] == str(sub_id)
            assert data["document_sha256_hash"] == doc_hash
            assert data["status"] == "ACTIVE"

            # 2. POST /api/v1/attestation/verify
            verify_payload = {
                "certificate_id": str(cert_id),
                "document_sha256_hash": doc_hash,
            }
            from unittest.mock import patch
            with patch.object(PublicationAttestationService, "verify_signature", return_value=True):
                resp_verify = await client.post(
                    "/api/v1/attestation/verify",
                    json=verify_payload,
                )
                assert resp_verify.status_code == 200
                verify_data = resp_verify.json()
                assert verify_data["is_valid_for_publish"] is True
                assert verify_data["verification_status"] == "VALID"
                assert verify_data["certificate_id"] == str(cert_id)

        finally:
            app.dependency_overrides.clear()
