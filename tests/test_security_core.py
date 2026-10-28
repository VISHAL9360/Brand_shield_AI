"""
BrandShield AI - Security, RBAC, and Cryptographic Controls Test Suite.
Validates Argon2id hashing, JWT role claims, RequireRole enforcement, and audit ledger breach logging.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.core.exceptions import ForbiddenProblem, UnauthorizedProblem
from app.core.security import (
    RequireRole,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)
from app.domain.enums import UserRole
from app.infrastructure.db.models import User


def test_argon2id_password_hashing_and_verification():
    """Validates Argon2id PHC string formatting and constant-time verification."""
    password = "EnterpriseSecureP@ssw0rd!2026"
    hashed = hash_password(password)

    # Validate PHC format
    assert hashed.startswith("$argon2id$v=19$m=65536,t=1,p=4$")
    parts = hashed.split("$")
    assert len(parts) == 6

    # Validate verification
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_jwt_token_generation_and_role_claims():
    """Validates JWT access & refresh tokens carrying strict RBAC claims."""
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    email = "compliance_officer@brandshield.ai"
    role = UserRole.ADMINISTRATOR

    # Access Token
    access_token = create_access_token(
        user_id=user_id,
        email=email,
        role=role,
        workspace_id=workspace_id,
    )
    claims = decode_jwt_token(access_token, expected_type="access")
    assert claims["sub"] == str(user_id)
    assert claims["email"] == email
    assert claims["role"] == UserRole.ADMINISTRATOR.value
    assert claims["workspace_id"] == str(workspace_id)
    assert claims["type"] == "access"
    assert "jti" in claims
    assert claims["exp"] > claims["iat"]

    # Refresh Token
    refresh_token = create_refresh_token(
        user_id=user_id,
        email=email,
        role=role,
        workspace_id=workspace_id,
    )
    r_claims = decode_jwt_token(refresh_token, expected_type="refresh")
    assert r_claims["sub"] == str(user_id)
    assert r_claims["type"] == "refresh"

    # Mismatched expected type raises UnauthorizedProblem
    with pytest.raises(UnauthorizedProblem):
        decode_jwt_token(access_token, expected_type="refresh")


@pytest.mark.asyncio
async def test_require_role_rbac_authorization_success():
    """Validates authorized user passes RequireRole guard."""
    guard = RequireRole(UserRole.ADMINISTRATOR, UserRole.REVIEWER)
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/brands/profiles"
    mock_request.method = "POST"
    mock_session = AsyncMock()

    user = User(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        email="admin@brandshield.ai",
        hashed_password="hash",
        full_name="Admin User",
        role=UserRole.ADMINISTRATOR,
        is_active=True,
    )

    authorized_user = await guard(
        request=mock_request,
        current_user=user,
        session=mock_session,
    )
    assert authorized_user == user


@pytest.mark.asyncio
async def test_require_role_rbac_breach_logs_to_audit_ledger():
    """Validates unauthorized access attempt logs breach to audit_ledger and raises RFC 7807 ForbiddenProblem."""
    guard = RequireRole(UserRole.ADMINISTRATOR)
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/brands/profiles"
    mock_request.method = "DELETE"
    mock_request.client.host = "192.168.1.50"
    mock_request.headers = {"user-agent": "PytestClient/1.0"}

    mock_session = AsyncMock()

    creator_user = User(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        email="creator@brandshield.ai",
        hashed_password="hash",
        full_name="Creator User",
        role=UserRole.CREATOR,
        is_active=True,
    )

    with pytest.raises(ForbiddenProblem) as exc_info:
        await guard(
            request=mock_request,
            current_user=creator_user,
            session=mock_session,
        )

    assert exc_info.value.status_code == 403
    assert "ADMINISTRATOR" in exc_info.value.detail
    assert "CREATOR" in exc_info.value.detail
    assert exc_info.value.extensions["required_roles"] == ["ADMINISTRATOR"]
    assert exc_info.value.extensions["current_role"] == "CREATOR"


def test_crypto_storage_engine_fernet_and_hmac():
    """Validates envelope encryption, prefix detection, and symmetric Fernet decryption."""
    from app.core.crypto_storage import CryptoStorageEngine, ENCRYPTION_PREFIX

    plain = "Confidential Enterprise Strategy Document 2026."
    encrypted = CryptoStorageEngine.encrypt_content(plain)
    assert encrypted != plain
    assert encrypted.startswith(ENCRYPTION_PREFIX)
    assert CryptoStorageEngine.is_encrypted(encrypted) is True
    assert CryptoStorageEngine.is_encrypted(plain) is False

    decrypted = CryptoStorageEngine.decrypt_content(encrypted)
    assert decrypted == plain

    # Idempotence: encrypting already encrypted payload returns as-is
    assert CryptoStorageEngine.encrypt_content(encrypted) == encrypted
    # Plain text passed to decrypt returns unchanged
    assert CryptoStorageEngine.decrypt_content(plain) == plain


@pytest.mark.asyncio
async def test_submission_service_wires_crypto_storage_at_rest():
    """
    Validates that when protected_storage_enabled is True on the BrandProfile,
    SubmissionService transparently encrypts content at rest, and commit_revision
    decrypts parent text to compute diffs.
    """
    from app.core.crypto_storage import CryptoStorageEngine
    from app.domain.schemas.submission import SubmissionCreate
    from app.infrastructure.db.models import BrandProfile, DocumentRevision, Submission
    from app.services.submission_service import SubmissionService

    workspace_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    creator_id = uuid.uuid4()

    # BrandProfile with protected_storage_enabled: True
    protected_profile = BrandProfile(
        id=profile_id,
        workspace_id=workspace_id,
        name="Protected Enterprise Brand",
        privacy_gate_config={"protected_storage_enabled": True},
    )

    mock_session = AsyncMock()
    mock_session.get.return_value = protected_profile

    raw_text = "Acme FinTech confidential roadmap and Q4 earnings summary."
    payload = SubmissionCreate(
        workspace_id=workspace_id,
        brand_profile_id=profile_id,
        title="Protected Q4 Brief",
        document_type="TEXT",
        initial_content=raw_text,
        ast_span_map=[{"span_id": 1, "start": 0, "end": 10}],
    )

    added_objects = []
    def fake_add(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        added_objects.append(obj)

    mock_session.add = MagicMock(side_effect=fake_add)
    mock_session.flush = AsyncMock()

    submission = await SubmissionService.create_submission(
        session=mock_session,
        payload=payload,
        creator_id=creator_id,
    )

    # Find the genesis revision created
    revisions = [o for o in added_objects if isinstance(o, DocumentRevision)]
    assert len(revisions) == 1
    genesis_rev = revisions[0]

    # Verify content_text is encrypted at rest with Fernet
    assert CryptoStorageEngine.is_encrypted(genesis_rev.content_text) is True
    assert genesis_rev.content_text.startswith("enc:fernet:")
    # Verify content can be decrypted back to raw_text
    assert CryptoStorageEngine.decrypt_content(genesis_rev.content_text) == raw_text


@pytest.mark.asyncio
async def test_revision_engine_wires_crypto_storage_on_finding_resolution():
    """
    Validates that RevisionEngine transparently decrypts parent content,
    applies the finding replacement slice, and re-encrypts the new revision.
    """
    from app.core.crypto_storage import CryptoStorageEngine
    from app.domain.enums import CreatorAction, FindingCategory, SeverityLevel, TriageStatus, WorkflowState
    from app.domain.schemas.submission import FindingResolutionRequest
    from app.infrastructure.db.models import BrandProfile, DocumentRevision, Finding, Submission
    from app.services.workflow.revision_engine import RevisionEngine

    sub_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    finding_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    actor = User(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        email="creator@acmefintech.com",
        role=UserRole.CREATOR,
    )

    raw_parent_text = "Acme is a 100% risk-free investment platform."
    encrypted_parent_text = CryptoStorageEngine.encrypt_content(raw_parent_text)

    submission = Submission(
        id=sub_id,
        workspace_id=workspace_id,
        brand_profile_id=profile_id,
        creator_id=actor.id,
        title="Investment Deck",
        document_type="TEXT",
        workflow_state=WorkflowState.TRIAGED,
        current_revision_id=rev_id,
        version_number=1,
    )

    parent_rev = DocumentRevision(
        id=rev_id,
        submission_id=sub_id,
        revision_number=1,
        content_text=encrypted_parent_text,
        ast_span_map=[],
        created_by_id=actor.id,
        sha256_content_hash="abc",
    )

    finding = Finding(
        id=finding_id,
        revision_id=rev_id,
        issue_category=FindingCategory.TERMINOLOGY,
        severity=SeverityLevel.CRITICAL,
        confidence_score=0.99,
        triage_status=TriageStatus.FLAGGED_HIGH_CONFIDENCE,
        start_offset=10,
        end_offset=24,  # "100% risk-free"
        explanation_reason="Superlative prohibited",
        suggested_correction="managed-risk",
    )

    brand_profile = BrandProfile(
        id=profile_id,
        workspace_id=workspace_id,
        name="Acme FinTech",
        privacy_gate_config={"protected_storage_enabled": True},
    )

    mock_session = AsyncMock()
    async def fake_get(model, entity_id):
        if model == Submission:
            return submission
        elif model == DocumentRevision:
            return parent_rev
        elif model == Finding:
            return finding
        elif model == BrandProfile:
            return brand_profile
        return None

    mock_session.get.side_effect = fake_get
    added_objects = []
    mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
    mock_session.flush = AsyncMock()

    resolution_req = FindingResolutionRequest(
        action=CreatorAction.ACCEPT,
        comment="Accepted compliant phrasing",
    )

    res = await RevisionEngine.resolve_finding(
        session=mock_session,
        submission_id=sub_id,
        finding_id=finding_id,
        actor=actor,
        payload=resolution_req,
    )

    assert res.applied_correction == "managed-risk"
    new_revs = [o for o in added_objects if isinstance(o, DocumentRevision)]
    assert len(new_revs) == 1
    new_rev = new_revs[0]

    # Stored content must be encrypted with Fernet
    assert CryptoStorageEngine.is_encrypted(new_rev.content_text) is True
    # Decrypted content must reflect the replacement slice on plaintext
    decrypted = CryptoStorageEngine.decrypt_content(new_rev.content_text)
    assert "managed-risk" in decrypted
    assert "100% risk-free" not in decrypted

