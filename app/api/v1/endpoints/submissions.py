"""
BrandShield AI - Submissions, Immutable Revision DAG, and Review Decisions.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_current_user, require_role
from app.domain.enums import UserRole
from app.domain.schemas.submission import (
    DocumentRevisionCreate,
    DocumentRevisionRead,
    ReviewDecisionCreate,
    ReviewDecisionRead,
    SubmissionCreate,
    SubmissionRead,
)
from app.infrastructure.db.models import DocumentRevision, ReviewDecision, Submission, User
from app.infrastructure.db.session import get_async_session
from app.services.submission_service import SubmissionService

router = APIRouter()


@router.post("/", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreate,
    current_user: Annotated[User, Depends(require_role([UserRole.CREATOR, UserRole.ADMINISTRATOR]))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Submission:
    """Ingests a document asset and establishes Genesis revision (v1) in the immutable DAG."""
    try:
        submission = await SubmissionService.create_submission(
            session=session,
            payload=payload,
            creator_id=current_user.id,
        )
        return submission
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{submission_id}/revisions",
    response_model=DocumentRevisionRead,
    status_code=status.HTTP_201_CREATED,
)
async def commit_revision(
    submission_id: uuid.UUID,
    payload: DocumentRevisionCreate,
    current_user: Annotated[User, Depends(require_role([UserRole.CREATOR, UserRole.ADMINISTRATOR]))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> DocumentRevision:
    """Appends an immutable revision node to the submission DAG."""
    try:
        revision = await SubmissionService.commit_revision(
            session=session,
            submission_id=submission_id,
            new_content=payload.content_text,
            ast_span_map=payload.ast_span_map,
            creator_id=current_user.id,
        )
        return revision
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{submission_id}/revisions", response_model=list[DocumentRevisionRead])
async def list_submission_revisions(
    submission_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[DocumentRevision]:
    """Retrieves full immutable commit history DAG for a submission."""
    submission = await session.get(Submission, submission_id)
    if not submission or submission.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")

    query = (
        select(DocumentRevision)
        .where(DocumentRevision.submission_id == submission_id)
        .order_by(DocumentRevision.revision_number.asc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post(
    "/{submission_id}/decisions",
    response_model=ReviewDecisionRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_review_decision(
    submission_id: uuid.UUID,
    payload: ReviewDecisionCreate,
    current_user: Annotated[User, Depends(require_role([UserRole.REVIEWER, UserRole.ADMINISTRATOR]))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ReviewDecision:
    """Records human compliance review sign-off (APPROVED or CHANGES_REQUESTED)."""
    try:
        decision = await SubmissionService.record_review_decision(
            session=session,
            submission_id=submission_id,
            reviewer_id=current_user.id,
            payload=payload,
        )
        return decision
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
