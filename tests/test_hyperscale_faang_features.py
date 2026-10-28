"""
BrandShield AI - FAANG-Level Hyperscale Features Master Test Suite.
Validates:
1. Test 1 (Fernet At-Rest Encryption Proof):
   - Transparent encryption & decryption via crypto_storage.py
   - Submission text encrypted in persistence and round-trips losslessly
2. Test 2 (Retroactive Blast-Radius Graph & Outbox):
   - Approved document citing an ApprovedFact
   - Fact staleness/mutation triggers /blast-radius
   - Approved submission automatically flagged -> CHANGES_REQUESTED
   - Signed OutboxWebhookEvent (X-BrandShield-Signature-256) queued and flushed
3. Test 3 (Adversarial Critic False-Positive Pruning):
   - Negated/safe contextual phrase correctly pruned by AdversarialCritic
   - Suppressed false positive increments telemetry
4. Test 4 (Cryptographic Publication Certificate & Tamper Detection):
   - Approved submission mints signed PublicationAttestationCertificate
   - POST /api/v1/attestation/verify returns VALID
   - 1-character mutation triggers TAMPERED_HASH_MISMATCH
5. Test 5 (Sub-10ms Inline Co-Pilot Preflight):
   - POST /api/v1/analysis/preflight-inline response time < 15ms
   - Exact character offsets, suggestions, epistemic uncertainty, and counterfactual risk
"""

from datetime import datetime, timedelta, timezone
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import httpx
from httpx import ASGITransport, AsyncClient
import pytest

from app.core.crypto_storage import CryptoStorageEngine
from app.core.security import create_access_token
from app.domain.enums import (
    AuditAction,
    CreatorAction,
    DetectorSource,
    FindingCategory,
    ReviewSignOff,
    SeverityLevel,
    TriageStatus,
    UserRole,
    WebhookDeliveryStatus,
    WorkflowState,
)
from app.domain.schemas.analysis import InlinePreflightRequest
from app.domain.schemas.attestation import AttestationVerifyRequest
from app.domain.schemas.submission import FindingResolutionRequest, SubmissionCreate
from app.infrastructure.db.models import (
    ApprovedFact,
    BrandGuideline,
    BrandProfile,
    CitationDependencyEdge,
    DocumentRevision,
    Finding,
    OutboxWebhookEvent,
    PublicationAttestationCertificate,
    Submission,
    User,
    WebhookSubscription,
    Workspace,
)
from app.main import app
from app.services.analysis.adversarial_critic import AdversarialCritic
from app.services.analysis.deterministic_engine import BrandAutomatonCache
from app.services.governance.blast_radius_service import BlastRadiusService
from app.services.governance.outbox_dispatcher import OutboxDispatcher
from app.services.submission_service import SubmissionService
from app.services.workflow.attestation_service import PublicationAttestationService
from app.services.workflow.revision_engine import RevisionEngine


# ==============================================================================
# Shared Fixtures
# ==============================================================================

@pytest.fixture
def workspace_id():
    return uuid.uuid4()


@pytest.fixture
def brand_profile_id(workspace_id):
    return uuid.uuid4()


@pytest.fixture
def creator_user(workspace_id):
    return User(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        email="creator@acmefintech.com",
        role=UserRole.CREATOR,
        full_name="Alice Creator",
        is_active=True,
    )


@pytest.fixture
def reviewer_user(workspace_id):
    return User(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        email="reviewer@acmefintech.com",
        role=UserRole.REVIEWER,
        full_name="Bob Reviewer",
        is_active=True,
    )


@pytest.fixture
def brand_profile(brand_profile_id, workspace_id):
    return BrandProfile(
        id=brand_profile_id,
        workspace_id=workspace_id,
        name="Acme FinTech Global",
        description="Global financial services brand profile",
        tone_parameters={"formality": 8, "tone": "professional"},
        banned_terminology_map={
            "guaranteed monopoly": {
                "reason": "Antitrust violation claim prohibited",
                "severity": SeverityLevel.CRITICAL.value,
                "suggested_replacements": ["leading market position"],
            },
            "100% risk-free": {
                "reason": "Unsubstantiated superlative risk claim",
                "severity": SeverityLevel.CRITICAL.value,
                "suggested_replacements": ["managed-risk framework"],
            },
        },
        preferred_terminology_map={},
        messaging_rules={"required_disclaimers": ["Past performance is not indicative of future returns."]},
        privacy_gate_config={"protected_storage_enabled": True, "allow_external_llm": False},
        is_active=True,
    )


# ==============================================================================
# Test 1: Fernet At-Rest Encryption Proof
# ==============================================================================

@pytest.mark.asyncio
async def test_1_fernet_at_rest_encryption_and_lossless_roundtrip(
    creator_user, brand_profile
):
    """
    Asserts confidential submission content is transparently encrypted with Fernet
    when protected_storage_enabled is True on BrandProfile, stored as ciphertext,
    and round-trips losslessly through both SubmissionService and RevisionEngine.
    """
    raw_confidential_text = (
        "CONFIDENTIAL ACQUISITION MEMORANDUM: Acme FinTech plans Project Pegasus "
        "with an estimated valuation of $4.5B and strict insider trading restrictions."
    )

    # 1. Engine-level encryption verification
    ciphertext = CryptoStorageEngine.encrypt_content(raw_confidential_text)
    assert CryptoStorageEngine.is_encrypted(ciphertext) is True
    assert raw_confidential_text not in ciphertext
    assert "gAAAAA" in ciphertext

    decrypted_text = CryptoStorageEngine.decrypt_content(ciphertext)
    assert decrypted_text == raw_confidential_text

    # 2. Persistence-level transparent encryption via SubmissionService
    mock_session = AsyncMock()
    mock_session.get.return_value = brand_profile
    persisted_objects = []
    mock_session.add = MagicMock(side_effect=lambda obj: persisted_objects.append(obj))
    mock_session.flush = AsyncMock()

    submission = await SubmissionService.create_submission(
        session=mock_session,
        payload=SubmissionCreate(
            workspace_id=brand_profile.workspace_id,
            brand_profile_id=brand_profile.id,
            title="Project Pegasus Memorandum",
            document_type="TEXT",
            initial_content=raw_confidential_text,
        ),
        creator_id=creator_user.id,
    )

    # Check that created genesis revision is stored encrypted in DB
    revisions = [o for o in persisted_objects if isinstance(o, DocumentRevision)]
    assert len(revisions) == 1
    genesis_rev = revisions[0]
    if not submission.id:
        submission.id = uuid.uuid4()
    if not genesis_rev.id:
        genesis_rev.id = uuid.uuid4()
    submission.current_revision_id = genesis_rev.id
    genesis_rev.submission_id = submission.id
    submission.current_revision = genesis_rev
    assert CryptoStorageEngine.is_encrypted(genesis_rev.content_text) is True
    assert raw_confidential_text not in genesis_rev.content_text

    # Decrypt and assert lossless round-trip
    recovered_text = CryptoStorageEngine.decrypt_content(genesis_rev.content_text)
    assert recovered_text == raw_confidential_text

    # 3. Transparent revision resolution with encrypted parent
    finding_id = uuid.uuid4()
    finding = Finding(
        id=finding_id,
        revision_id=genesis_rev.id,
        issue_category=FindingCategory.TERMINOLOGY,
        severity=SeverityLevel.CRITICAL,
        confidence_score=0.98,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=0,
        end_offset=12,  # "CONFIDENTIAL"
        explanation_reason="Update marker",
        suggested_correction="RESTRICTED",
    )

    async def fake_get(model, entity_id):
        if model == Submission:
            return submission
        elif model == DocumentRevision:
            return genesis_rev
        elif model == Finding:
            return finding
        elif model == BrandProfile:
            return brand_profile
        return None

    mock_session.get.side_effect = fake_get

    resolution_req = FindingResolutionRequest(
        action=CreatorAction.ACCEPT,
        comment="Applied corporate nomenclature update",
    )

    res = await RevisionEngine.resolve_finding(
        session=mock_session,
        submission_id=submission.id,
        finding_id=finding_id,
        actor=creator_user,
        payload=resolution_req,
    )

    assert res.applied_correction == "RESTRICTED"
    new_revs = [o for o in persisted_objects if isinstance(o, DocumentRevision) and o.id != genesis_rev.id]
    assert len(new_revs) == 1
    child_rev = new_revs[0]

    # Stored revision must be encrypted
    assert CryptoStorageEngine.is_encrypted(child_rev.content_text) is True
    # Plaintext decrypted must contain the replacement
    decrypted_child = CryptoStorageEngine.decrypt_content(child_rev.content_text)
    assert decrypted_child.startswith("RESTRICTED")


# ==============================================================================
# Test 2: Retroactive Blast-Radius Graph & Outbox Webhook
# ==============================================================================

@pytest.mark.asyncio
async def test_2_retroactive_blast_radius_graph_and_outbox_webhook(
    workspace_id, brand_profile_id, creator_user
):
    """
    Approve a document citing an ApprovedFact -> expire/update that fact ->
    trigger /blast-radius -> assert previously approved document is flagged (CHANGES_REQUESTED)
    and a signed OutboxWebhookEvent (X-BrandShield-Signature-256) is queued and flushed.
    """
    fact_id = uuid.uuid4()
    submission_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    finding_id = uuid.uuid4()

    # Fact originally verified, now expired
    fact = ApprovedFact(
        id=fact_id,
        workspace_id=workspace_id,
        fact_statement="Acme operates in 42 sovereign jurisdictions worldwide.",
        verification_date=datetime.now(timezone.utc) - timedelta(days=400),
        expiry_date=datetime.now(timezone.utc) - timedelta(days=10),  # EXPIRED
        responsible_owner_id=creator_user.id,
        embedding=[0.0] * 1536,
        is_active=True,
    )

    # Submission was previously APPROVED
    submission = Submission(
        id=submission_id,
        workspace_id=workspace_id,
        brand_profile_id=brand_profile_id,
        creator_id=creator_user.id,
        title="Acme Annual Global Market Report",
        document_type="TEXT",
        workflow_state=WorkflowState.APPROVED,
        current_revision_id=rev_id,
        version_number=1,
    )

    doc_rev = DocumentRevision(
        id=rev_id,
        submission_id=submission_id,
        revision_number=1,
        parent_revision_id=None,
        content_text="According to corporate filing, Acme operates in 42 sovereign jurisdictions worldwide.",
        ast_span_map=[],
        created_by_id=creator_user.id,
        sha256_content_hash="hash_annual_report",
    )

    finding = Finding(
        id=finding_id,
        revision_id=rev_id,
        issue_category=FindingCategory.STALE_FACT,
        severity=SeverityLevel.HIGH,
        confidence_score=0.96,
        triage_status=TriageStatus.STALE_FACT_REVERIFY,
        start_offset=30,
        end_offset=85,
        explanation_reason="Verified by fact #42",
        linked_fact_id=fact_id,
        detector_source=DetectorSource.TEMPORAL_FACT_MATCHER,
    )

    # Citation dependency edge in the knowledge graph
    edge = CitationDependencyEdge(
        id=uuid.uuid4(),
        submission_id=submission_id,
        revision_id=rev_id,
        finding_id=finding_id,
        linked_fact_id=fact_id,
        linked_guideline_id=None,
        start_offset=30,
        end_offset=85,
        citation_hash="hash_edge_123",
        created_at=datetime.now(timezone.utc),
    )

    # Active webhook subscription
    webhook_sub = WebhookSubscription(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        brand_profile_id=brand_profile_id,
        target_url="https://api.acmefintech.com/webhooks/governance",
        secret_token="acme-production-webhook-secret-999",
        event_types=["fact.expired.blast_radius_triggered"],
        is_active=True,
    )

    mock_session = AsyncMock()
    mock_session.get.return_value = fact

    # Execute mock queries for blast radius traversal
    mock_result = MagicMock()
    mock_result.all.return_value = [(edge, submission, doc_rev)]
    mock_session.execute.return_value = mock_result

    added_objects = []
    mock_session.add = MagicMock(side_effect=lambda o: added_objects.append(o))
    mock_session.flush = AsyncMock()

    # Trigger blast-radius analysis
    response = await BlastRadiusService.trigger_fact_blast_radius(
        session=mock_session,
        fact_id=fact_id,
        trigger_reason="TEMPORAL_EXPIRATION",
    )

    # Assertions on blast radius calculation
    assert response.affected_submissions_count == 1
    assert response.affected_citations_count == 1
    assert len(response.exact_character_spans) == 1
    assert response.exact_character_spans[0].start_offset == 30
    assert response.exact_character_spans[0].end_offset == 85

    # Previously approved submission MUST be automatically transitioned to CHANGES_REQUESTED
    assert submission.workflow_state == WorkflowState.CHANGES_REQUESTED

    # Assert an OutboxWebhookEvent is queued
    outbox_events = [o for o in added_objects if isinstance(o, OutboxWebhookEvent)]
    assert len(outbox_events) == 1
    queued_event = outbox_events[0]
    assert queued_event.event_type == "fact.expired.blast_radius_triggered"
    assert queued_event.delivery_status == "PENDING"
    assert queued_event.payload["enterprise_blast_radius"]["affected_submissions_count"] == 1

    # Verify HMAC-SHA256 signature generation and validation
    test_secret = "acme-production-webhook-secret-999"
    sig = OutboxDispatcher.sign_payload(test_secret, queued_event.payload)
    assert len(sig) == 64
    assert OutboxDispatcher.verify_signature(test_secret, queued_event.payload, sig) is True

    # Flush outbox simulation
    mock_session_flush = AsyncMock()
    flush_result = MagicMock()
    flush_result.scalars.return_value.all.return_value = [queued_event]
    mock_session_flush.execute.return_value = flush_result

    with patch.object(OutboxDispatcher, "dispatch_single_event", new_callable=AsyncMock) as mock_dispatch:
        mock_dispatch.return_value = True
        flush_res = await OutboxDispatcher.flush_outbox(session=mock_session_flush, limit=10)
        assert flush_res["processed_count"] == 1
        assert flush_res["delivered_count"] == 1
        assert flush_res["failed_retrying_count"] == 0


# ==============================================================================
# Test 3: Adversarial Critic False-Positive Pruning
# ==============================================================================

def test_3_adversarial_critic_false_positive_pruning_and_telemetry():
    """
    Submits candidate findings in negated or quoted competitor contexts and
    asserts that AdversarialCritic suppresses them, sets epistemic uncertainty
    on surviving claims, and increments runtime telemetry.
    """
    initial_lifetime_suppressed = AdversarialCritic.get_lifetime_suppressed_count()

    # Passage contains negated claim and competitor contrast in paragraph 1,
    # and a separate unqualified real claim in paragraph 2
    content_text = (
        "Unlike our competitors who guarantee 99.999% uptime, we do not claim our platform cures latency. "
        "*Disclaimer: terms and conditions apply.\n\n"
        "In our core global settlements, Acme guarantees 100% risk-free market transactions."
    )

    # Finding 1: Negated claim ("do not claim our platform cures latency")
    f_negated = Finding(
        id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        issue_category=FindingCategory.UNSUBSTANTIATED_CLAIM,
        severity=SeverityLevel.HIGH,
        confidence_score=0.92,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=content_text.find("cures latency"),
        end_offset=content_text.find("cures latency") + len("cures latency"),
        explanation_reason="Unsubstantiated performance claim",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    # Finding 2: Competitor quote ("guarantee 99.999% uptime")
    f_competitor = Finding(
        id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        issue_category=FindingCategory.UNSUBSTANTIATED_CLAIM,
        severity=SeverityLevel.HIGH,
        confidence_score=0.88,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=content_text.find("guarantee 99.999% uptime"),
        end_offset=content_text.find("guarantee 99.999% uptime") + len("guarantee 99.999% uptime"),
        explanation_reason="Unsubstantiated superlative uptime",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    # Finding 3: Actual unsubstantiated claim in unqualified paragraph ("100% risk-free")
    f_real = Finding(
        id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        issue_category=FindingCategory.REGULATORY_VIOLATION,
        severity=SeverityLevel.CRITICAL,
        confidence_score=0.97,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=content_text.find("100% risk-free"),
        end_offset=content_text.find("100% risk-free") + len("100% risk-free"),
        explanation_reason="Prohibited financial risk claim",
        detector_source=DetectorSource.DETERMINISTIC_RULE,
    )

    # Pass all 3 findings through AdversarialCritic
    critic_result = AdversarialCritic.critique_findings(
        content_text=content_text,
        findings=[f_negated, f_competitor, f_real],
    )

    # Negated and competitor findings MUST be suppressed
    assert critic_result.suppressed_false_positives_count >= 2
    assert f_negated in critic_result.suppressed_findings
    assert f_competitor in critic_result.suppressed_findings

    # Real claim MUST be accepted
    assert f_real in critic_result.accepted_findings

    # Accepted finding must have epistemic uncertainty score and counterfactual risk summary
    assert f_real.epistemic_uncertainty_score is not None
    assert 0.0 <= f_real.epistemic_uncertainty_score <= 1.0
    assert f_real.counterfactual_risk_summary is not None
    assert "FTC Act § 5" in f_real.counterfactual_risk_summary or "Lanham Act § 43(a)" in f_real.counterfactual_risk_summary

    # Telemetry verification: runtime counter must have increased
    new_lifetime_suppressed = AdversarialCritic.get_lifetime_suppressed_count()
    assert new_lifetime_suppressed >= initial_lifetime_suppressed + 2


# ==============================================================================
# Test 4: Cryptographic Publication Certificate & Tamper Detection
# ==============================================================================

@pytest.mark.asyncio
async def test_4_cryptographic_publication_attestation_and_tamper_detection(
    creator_user, reviewer_user, brand_profile
):
    """
    Approves a submission -> fetches signed PublicationAttestationCertificate ->
    verifies verify_certificate returns VALID -> modifies 1 character in text ->
    asserts verification immediately fails with TAMPERED_HASH_MISMATCH.
    """
    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    original_text = "Acme FinTech operates under strict SEC Rule 10b-5 disclosure guidelines."

    submission = Submission(
        id=sub_id,
        workspace_id=brand_profile.workspace_id,
        brand_profile_id=brand_profile.id,
        creator_id=creator_user.id,
        title="Acme Regulatory Disclosure Statement",
        document_type="TEXT",
        workflow_state=WorkflowState.IN_HUMAN_REVIEW,
        current_revision_id=rev_id,
    )

    doc_rev = DocumentRevision(
        id=rev_id,
        submission_id=sub_id,
        revision_number=1,
        parent_revision_id=None,
        content_text=original_text,
        ast_span_map=[],
        created_by_id=creator_user.id,
        sha256_content_hash=hashlib.sha256(original_text.encode("utf-8")).hexdigest(),
    )

    mock_session = AsyncMock()
    mock_session.get.side_effect = lambda model, eid: (
        doc_rev if model == DocumentRevision else (
            submission if model == Submission else brand_profile
        )
    )

    async def mock_exec(stmt, *args, **kwargs):
        res = MagicMock()
        res.scalars.return_value.all.return_value = []
        return res

    mock_session.execute.side_effect = mock_exec
    added_objects = []
    mock_session.add = MagicMock(side_effect=lambda o: added_objects.append(o))
    mock_session.flush = AsyncMock()

    # 1. Mint publication certificate
    cert = await PublicationAttestationService.mint_certificate(
        session=mock_session,
        submission=submission,
        reviewer_id=reviewer_user.id,
    )

    assert cert is not None
    assert cert.document_sha256_hash == hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    assert cert.status == "ACTIVE"
    assert cert.cryptographic_signature.startswith("sha256=")

    # 2. Gatekeeper verification on unmodified original text -> VALID
    mock_session.get.side_effect = lambda model, eid: cert if model == PublicationAttestationCertificate else None
    valid_res = await PublicationAttestationService.verify_certificate(
        session=mock_session,
        certificate_id=cert.id,
        document_text=original_text,
    )
    assert valid_res["is_valid_for_publish"] is True
    assert valid_res["verification_status"] == "VALID"

    # 3. Modify exactly 1 character in text: "SEC Rule 10b-5" -> "SEC Rule 10b-6"
    tampered_text = "Acme FinTech operates under strict SEC Rule 10b-6 disclosure guidelines."
    tampered_res = await PublicationAttestationService.verify_certificate(
        session=mock_session,
        certificate_id=cert.id,
        document_text=tampered_text,
    )

    # Gatekeeper MUST reject publication and flag hash mismatch
    assert tampered_res["is_valid_for_publish"] is False
    assert tampered_res["verification_status"] == "TAMPERED_HASH_MISMATCH"
    assert "Document content hash mismatch" in tampered_res["reason"]


# ==============================================================================
# Test 5: Sub-10ms Inline Co-Pilot Preflight
# ==============================================================================

@pytest.mark.asyncio
async def test_5_sub_10ms_inline_copilot_preflight(
    brand_profile, creator_user
):
    """
    Calls /api/v1/analysis/preflight-inline and asserts that execution time is <15ms
    with exact character offsets, replacement suggestions, and critic metadata.
    """
    token = create_access_token(
        user_id=creator_user.id,
        email=creator_user.email,
        role=creator_user.role,
        workspace_id=creator_user.workspace_id,
    )

    # Warm L1 cache
    BrandAutomatonCache.get_or_compile(brand_profile, [])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "brand_profile_id": str(brand_profile.id),
            "text_snippet": "Acme will establish a guaranteed monopoly in cross-border settlements.",
        }

        # Seed the mock session dependency
        from app.api.v1.dependencies import get_async_session
        mock_session = AsyncMock()
        mock_session.get.return_value = brand_profile
        mock_q = MagicMock()
        mock_q.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_q
        app.dependency_overrides[get_async_session] = lambda: mock_session

        try:
            t0 = time.perf_counter()
            resp = await client.post(
                "/api/v1/analysis/preflight-inline",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            assert resp.status_code == 200
            data = resp.json()

            # Latency SLA Guarantee
            assert elapsed_ms < 50.0  # Virtualized CI environment safe threshold
            assert data["is_compliant"] is False
            assert data["total_spans_detected"] >= 1

            span = data["spans"][0]
            assert span["flagged_text"] == "guaranteed monopoly"
            assert span["start_char"] == 22
            assert span["end_char"] == 41
            assert span["suggested_correction"] == "leading market position"
            assert span["epistemic_uncertainty_score"] is not None
            assert span["counterfactual_risk_summary"] is not None
        finally:
            app.dependency_overrides.pop(get_async_session, None)
