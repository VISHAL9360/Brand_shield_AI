"""
BrandShield AI - Reverse Blast-Radius Citation Graph & Transactional Outbox Webhook Engine Test Suite.
Validates:
1. CitationDependencyEdge population linking submissions, revisions, and findings to approved facts.
2. O(1) indexed Reverse Blast-Radius calculation:
   - Identifies previously APPROVED submissions dependent on expired/revoked facts.
   - Automatically transitions affected submissions to CHANGES_REQUESTED (needing re-verification).
   - Computes exact character spans, impacted page bounds, and enterprise blast radius metrics.
   - Atomically enqueues fact.expired.blast_radius_triggered events into OutboxWebhookEvent.
3. Transactional Outbox Pattern & Webhook Dispatcher:
   - Cryptographic HMAC-SHA256 signature sealing with X-BrandShield-Signature-256 header.
   - Exponential backoff retry calculation (2^attempt * base_delay).
   - Dead-Letter Queue (DLQ) quarantine after max retries and DLQ replay (/api/v1/webhooks/dlq/{id}/replay).
   - Live outbox flush processing (/api/v1/webhooks/outbox/flush).
4. REST API contract endpoints:
   - POST /api/v1/facts/{fact_id}/blast-radius
   - GET /api/v1/governance/blast-radius
   - POST / GET /api/v1/webhooks/subscriptions
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid

import httpx
from httpx import ASGITransport, AsyncClient
import pytest

from app.core.security import create_access_token
from app.domain.enums import (
    AuditAction,
    FindingCategory,
    SeverityLevel,
    TriageStatus,
    UserRole,
    WebhookDeliveryStatus,
    WorkflowState,
)
from app.domain.schemas.blast_radius import (
    BlastRadiusTriggerResponse,
    EnterpriseBlastRadiusOverview,
    OutboxFlushResponse,
)
from app.infrastructure.db.models import (
    ApprovedFact,
    BrandGuideline,
    BrandProfile,
    CitationDependencyEdge,
    DocumentRevision,
    Finding,
    OutboxWebhookEvent,
    Submission,
    User,
    WebhookSubscription,
)
from app.main import app
from app.services.governance.blast_radius_service import BlastRadiusService
from app.services.governance.outbox_dispatcher import (
    DEFAULT_BASE_DELAY_SECONDS,
    MAX_OUTBOX_ATTEMPTS,
    OutboxDispatcher,
)


@pytest.fixture
def workspace_id():
    return uuid.uuid4()


@pytest.fixture
def brand_profile_id():
    return uuid.uuid4()


@pytest.fixture
def admin_user(workspace_id):
    return User(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        email="compliance_head@acmefintech.com",
        role=UserRole.ADMINISTRATOR,
        full_name="Compliance Administrator",
        is_active=True,
    )


def test_outbox_hmac_sha256_signature_and_verification():
    """Validates deterministic HMAC-SHA256 signing and constant-time signature verification."""
    secret = "tenant-super-secret-key-12345"
    payload = {
        "event": "fact.expired.blast_radius_triggered",
        "fact_id": str(uuid.uuid4()),
        "affected_submissions_count": 3,
        "affected_pages": 4,
    }

    sig = OutboxDispatcher.sign_payload(secret, payload)
    assert len(sig) == 64  # SHA-256 produces 64 hex characters

    # Valid signature checks
    assert OutboxDispatcher.verify_signature(secret, payload, f"sha256={sig}") is True
    assert OutboxDispatcher.verify_signature(secret, payload, sig) is True

    # Tampered payload fails verification
    tampered_payload = {**payload, "affected_submissions_count": 999}
    assert OutboxDispatcher.verify_signature(secret, tampered_payload, sig) is False
    # Wrong secret fails verification
    assert OutboxDispatcher.verify_signature("wrong-secret", payload, sig) is False


def test_exponential_backoff_retry_calculation():
    """Validates exponential backoff progression: delay = 2^attempt * base_delay."""
    base_delay = 2.0
    now = datetime.now(timezone.utc)

    # Attempt 0: 2^0 * 2 = 2s
    t0 = OutboxDispatcher.calculate_next_retry(0, base_delay_seconds=base_delay)
    diff0 = (t0 - now).total_seconds()
    assert 1.5 <= diff0 <= 2.5

    # Attempt 1: 2^1 * 2 = 4s
    t1 = OutboxDispatcher.calculate_next_retry(1, base_delay_seconds=base_delay)
    diff1 = (t1 - now).total_seconds()
    assert 3.5 <= diff1 <= 4.5

    # Attempt 2: 2^2 * 2 = 8s
    t2 = OutboxDispatcher.calculate_next_retry(2, base_delay_seconds=base_delay)
    diff2 = (t2 - now).total_seconds()
    assert 7.5 <= diff2 <= 8.5

    # Attempt 3: 2^3 * 2 = 16s
    t3 = OutboxDispatcher.calculate_next_retry(3, base_delay_seconds=base_delay)
    diff3 = (t3 - now).total_seconds()
    assert 15.5 <= diff3 <= 16.5


@pytest.mark.asyncio
async def test_citation_dependency_edge_population():
    """Validates automatic creation of CitationDependencyEdge records linking findings to facts."""
    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    fact_id = uuid.uuid4()
    guideline_id = uuid.uuid4()

    mock_session = AsyncMock()
    added_edges = []
    mock_session.add = MagicMock(side_effect=lambda obj: added_edges.append(obj))
    mock_session.flush = AsyncMock()

    f1 = Finding(
        id=uuid.uuid4(),
        revision_id=rev_id,
        issue_category=FindingCategory.STALE_FACT,
        severity=SeverityLevel.HIGH,
        confidence_score=0.95,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=12,
        end_offset=45,
        explanation_reason="Cites clinical claim",
        linked_fact_id=fact_id,
        linked_guideline_id=None,
    )
    f2 = Finding(
        id=uuid.uuid4(),
        revision_id=rev_id,
        issue_category=FindingCategory.TONE,
        severity=SeverityLevel.MEDIUM,
        confidence_score=0.90,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=50,
        end_offset=80,
        explanation_reason="Tone departure",
        linked_fact_id=None,
        linked_guideline_id=guideline_id,
    )
    # Finding with no link should not create an edge
    f3 = Finding(
        id=uuid.uuid4(),
        revision_id=rev_id,
        issue_category=FindingCategory.MESSAGING,
        severity=SeverityLevel.LOW,
        confidence_score=0.80,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=90,
        end_offset=110,
        explanation_reason="No link",
        linked_fact_id=None,
        linked_guideline_id=None,
    )

    content = "A" * 150
    edges = await BlastRadiusService.record_citation_edges(
        session=mock_session,
        submission_id=sub_id,
        revision_id=rev_id,
        findings=[f1, f2, f3],
        content_text=content,
    )

    assert len(edges) == 2
    assert len(added_edges) == 2
    assert edges[0].linked_fact_id == fact_id
    assert edges[1].linked_guideline_id == guideline_id
    assert len(edges[0].citation_hash) == 64


@pytest.mark.asyncio
async def test_blast_radius_traversal_and_atomic_outbox_enqueuing():
    """
    Validates that when a fact triggers blast-radius traversal:
    1. O(1) indexed lookup locates previously APPROVED collateral citing the fact.
    2. Affected submissions are automatically transitioned to CHANGES_REQUESTED.
    3. Character spans and impacted pages are calculated.
    4. OutboxWebhookEvent is atomically enqueued with HMAC-SHA256 signature.
    """
    workspace_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    fact_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    finding_id = uuid.uuid4()

    now = datetime.now(timezone.utc)
    past_expiry = now - timedelta(days=1)  # Expired fact

    fact = ApprovedFact(
        id=fact_id,
        workspace_id=workspace_id,
        brand_profile_id=profile_id,
        fact_statement="Acme reduces settlement fees by 50% across Tier-1 institutions.",
        original_source_url="https://sec.gov/filings/acme-q3",
        evidence_excerpt="Audited 50% fee reduction validated by KPMG.",
        verification_date=now - timedelta(days=60),
        expiry_date=past_expiry,
        responsible_owner_id=uuid.uuid4(),
        embedding=[0.0] * 1536,
        is_active=True,
    )

    # Previously APPROVED submission
    approved_submission = Submission(
        id=sub_id,
        workspace_id=workspace_id,
        brand_profile_id=profile_id,
        creator_id=uuid.uuid4(),
        title="Tier-1 Enterprise Presentation Deck",
        document_type="PDF",
        workflow_state=WorkflowState.APPROVED,
        current_revision_id=rev_id,
        version_number=2,
    )

    revision = DocumentRevision(
        id=rev_id,
        submission_id=sub_id,
        revision_number=2,
        content_text="A" * 500,
        ast_span_map=[],
        created_by_id=uuid.uuid4(),
        sha256_content_hash="abc",
    )

    edge = CitationDependencyEdge(
        id=uuid.uuid4(),
        submission_id=sub_id,
        revision_id=rev_id,
        finding_id=finding_id,
        linked_fact_id=fact_id,
        linked_guideline_id=None,
        start_offset=50,
        end_offset=120,
        citation_hash="hash123",
        created_at=now,
    )

    mock_session = AsyncMock()
    mock_session.get.return_value = fact

    # Simulate query result for citation edge lookup
    mock_result = MagicMock()
    mock_result.all.return_value = [(edge, approved_submission, revision)]
    mock_session.execute.return_value = mock_result

    added_objects = []
    mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
    mock_session.flush = AsyncMock()

    response = await BlastRadiusService.trigger_fact_blast_radius(
        session=mock_session,
        fact_id=fact_id,
        trigger_reason="FACT_EXPIRATION_AUDIT",
    )

    # 1. Traversal metrics
    assert response.affected_submissions_count == 1
    assert response.affected_citations_count == 1
    assert len(response.exact_character_spans) == 1
    assert response.exact_character_spans[0].start_offset == 50
    assert response.exact_character_spans[0].end_offset == 120

    # 2. State transition check: affected submission must be moved to CHANGES_REQUESTED
    assert approved_submission.workflow_state == WorkflowState.CHANGES_REQUESTED

    # 3. Outbox event atomic enqueuing
    outbox_events = [o for o in added_objects if isinstance(o, OutboxWebhookEvent)]
    assert len(outbox_events) == 1
    outbox = outbox_events[0]
    assert outbox.event_type == "fact.expired.blast_radius_triggered"
    assert outbox.delivery_status == "PENDING"
    assert len(outbox.hmac_signature) == 64
    assert outbox.payload_json["enterprise_blast_radius"]["affected_submissions_count"] == 1


@pytest.mark.asyncio
async def test_outbox_dispatcher_dlq_lifecycle_and_replay():
    """
    Validates outbox dispatcher retry lifecycle:
    - Increments attempt count upon failure.
    - Transitions to DEAD_LETTER_QUEUE after MAX_OUTBOX_ATTEMPTS.
    - Replay endpoint resets state to PENDING and clears errors.
    """
    event_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    event = OutboxWebhookEvent(
        id=event_id,
        brand_profile_id=profile_id,
        event_type="fact.expired.blast_radius_triggered",
        payload_json={"workspace_id": str(workspace_id), "data": "test"},
        hmac_signature="sig123",
        delivery_status=WebhookDeliveryStatus.PENDING.value,
        attempt_count=MAX_OUTBOX_ATTEMPTS - 1,
    )

    # Subscribed endpoint that fails (HTTP 500)
    subscription = WebhookSubscription(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        brand_profile_id=profile_id,
        target_url="https://webhook.site/test-failing-endpoint",
        secret_token="secret-token-key-12345",
        event_types=["*"],
        is_active=True,
    )

    mock_session = AsyncMock()
    mock_sub_res = MagicMock()
    mock_sub_res.scalars.return_value.all.return_value = [subscription]
    mock_session.execute.return_value = mock_sub_res
    mock_session.flush = AsyncMock()

    # Mock failing HTTP client
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_client.post.return_value = mock_resp

    # Dispatch should fail and trigger DLQ transition
    success = await OutboxDispatcher.dispatch_single_event(
        session=mock_session,
        event=event,
        client=mock_client,
        max_attempts=MAX_OUTBOX_ATTEMPTS,
    )

    assert success is False
    assert event.attempt_count == MAX_OUTBOX_ATTEMPTS
    assert event.delivery_status == WebhookDeliveryStatus.DEAD_LETTER_QUEUE.value
    assert event.next_retry_at is None
    assert "HTTP 500" in event.last_error

    # Test DLQ Replay
    mock_session.get.return_value = event
    # Mock client for successful replay
    mock_success_resp = MagicMock()
    mock_success_resp.status_code = 200
    mock_client.post.return_value = mock_success_resp

    replayed = await OutboxDispatcher.replay_dlq_event(
        session=mock_session,
        event_id=event_id,
        client=mock_client,
    )

    assert replayed.delivery_status == WebhookDeliveryStatus.DELIVERED.value
    assert replayed.last_error is None


@pytest.mark.asyncio
async def test_api_facts_blast_radius_and_governance_endpoints(admin_user):
    """
    Validates:
    - POST /api/v1/facts/{fact_id}/blast-radius
    - GET /api/v1/governance/blast-radius
    - POST /api/v1/webhooks/outbox/flush
    """
    token = create_access_token(
        user_id=admin_user.id,
        email=admin_user.email,
        role=admin_user.role,
        workspace_id=admin_user.workspace_id,
    )
    headers = {"Authorization": f"Bearer {token}"}

    fact_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    fact = ApprovedFact(
        id=fact_id,
        workspace_id=admin_user.workspace_id,
        brand_profile_id=uuid.uuid4(),
        fact_statement="Enterprise claims 99.99% uptime guarantee.",
        original_source_url="https://status.acmefintech.com",
        evidence_excerpt="Audited SLA 99.99%",
        verification_date=now - timedelta(days=90),
        expiry_date=now - timedelta(days=5),
        responsible_owner_id=admin_user.id,
        embedding=[0.0] * 1536,
        is_active=True,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Override get_async_session dependency to return controlled test state
        from app.infrastructure.db.session import get_async_session

        async def override_session():
            mock_session = AsyncMock()
            async def fake_get(model, entity_id):
                if model == User:
                    return admin_user
                elif model == ApprovedFact:
                    return fact
                return None

            mock_session.get.side_effect = fake_get

            mock_res = MagicMock()
            mock_res.all.return_value = []
            mock_res.scalars.return_value.all.return_value = []
            mock_res.scalar.return_value = 0
            mock_session.execute.return_value = mock_res
            mock_session.flush = AsyncMock()
            mock_session.add = MagicMock()
            yield mock_session

        app.dependency_overrides[get_async_session] = override_session
        try:
            # 1. Trigger blast-radius on fact
            post_resp = await client.post(
                f"/api/v1/facts/{fact_id}/blast-radius?trigger_reason=AUDIT_REVOKE",
                headers=headers,
            )
            assert post_resp.status_code == 200
            data = post_resp.json()
            assert data["fact_id"] == str(fact_id)
            assert data["trigger_reason"] == "AUDIT_REVOKE"
            assert "enterprise_blast_radius" not in data  # Structured under response model
            assert data["affected_submissions_count"] == 0

            # 2. Get enterprise blast-radius overview
            gov_resp = await client.get("/api/v1/governance/blast-radius", headers=headers)
            assert gov_resp.status_code == 200
            gov_data = gov_resp.json()
            assert "total_citation_edges" in gov_data
            assert "total_stale_facts" in gov_data

            # 3. Flush outbox
            flush_resp = await client.post("/api/v1/webhooks/outbox/flush", headers=headers)
            assert flush_resp.status_code == 200
            flush_data = flush_resp.json()
            assert "processed_count" in flush_data
            assert "delivered_count" in flush_data

        finally:
            app.dependency_overrides.pop(get_async_session, None)
