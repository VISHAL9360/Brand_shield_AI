"""
BrandShield AI - Publication Attestation & Cryptographic CMS Clearance Router.
Implements Feature 2:
1. GET /submissions/{id}/certificate - Retrieves signed clearance passport.
2. POST /attestation/verify - Ultra-fast <1ms CMS Gatekeeper endpoint verifying content integrity and active citations.
"""

from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundProblem
from app.core.security import get_current_user_optional
from app.domain.schemas.attestation import (
    AttestationVerifyRequest,
    AttestationVerifyResponse,
    PublicationAttestationCertificateRead,
)
from app.infrastructure.db.models import Submission, User
from app.infrastructure.db.session import get_async_session
from app.services.workflow.attestation_service import PublicationAttestationService

router = APIRouter()
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]


@router.get(
    "/submissions/{submission_id}/certificate",
    response_model=PublicationAttestationCertificateRead,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Publication Attestation Clearance Passport",
)
@router.get(
    "/{submission_id}/certificate",
    response_model=PublicationAttestationCertificateRead,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Publication Attestation Clearance Passport",
)
async def get_submission_publication_certificate(
    submission_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: OptionalUser = None,
) -> PublicationAttestationCertificateRead:
    """
    Retrieves the signed cryptographic publication clearance certificate for an approved submission.
    Contains document SHA-256 hash, Merkle root of cited facts/guidelines, and validity window.
    """
    submission = await session.get(Submission, submission_id)
    if not submission:
        raise NotFoundProblem(
            detail=f"Submission '{submission_id}' not found.",
            resource_type="Submission",
            resource_id=str(submission_id),
        )

    cert = await PublicationAttestationService.get_certificate_for_submission(
        session=session,
        submission_id=submission_id,
    )
    if not cert:
        raise NotFoundProblem(
            detail=f"Publication clearance certificate for submission '{submission_id}' not found. Document may not be approved.",
            resource_type="PublicationAttestationCertificate",
            resource_id=str(submission_id),
        )

    return PublicationAttestationCertificateRead.model_validate(cert)


@router.post(
    "/verify",
    response_model=AttestationVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Ultra-Fast <1ms CMS Publication Gatekeeper Verification",
)
async def verify_publication_certificate_gatekeeper(
    payload: AttestationVerifyRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AttestationVerifyResponse:
    """
    Sub-millisecond verification endpoint for external CMS publishing pipelines:
    1. Verifies HMAC-SHA256 signature sealing canonical certificate contents.
    2. Validates document SHA-256 hash matches the approved revision (zero post-approval tampering).
    3. Confirms temporal certificate validity window has not elapsed.
    4. Evaluates dynamic ground truth: confirms none of the cited facts have expired or been revoked.
    """
    result = await PublicationAttestationService.verify_certificate(
        session=session,
        certificate_id=payload.certificate_id,
        document_text=payload.document_text,
        document_sha256_hash=payload.document_sha256_hash,
    )
    return AttestationVerifyResponse(**result)
