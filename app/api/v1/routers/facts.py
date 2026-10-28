"""
BrandShield AI - Substantiated Facts & Temporal Staleness Router.
Provides verified fact ingestion, staleness sweep, and vector semantic grounding.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.dependencies import CurrentUser, ReviewerUser, SessionDep
from app.domain.schemas.blast_radius import BlastRadiusTriggerResponse
from app.domain.schemas.fact import ApprovedFactCreate, ApprovedFactRead
from app.infrastructure.db.models import ApprovedFact

router = APIRouter()


@router.get("/", response_model=list[ApprovedFactRead])
async def list_approved_facts(
    current_user: CurrentUser,
    session: SessionDep,
    brand_profile_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ApprovedFact]:
    """Lists approved facts with temporal validity metadata."""
    query = (
        select(ApprovedFact)
        .where(ApprovedFact.workspace_id == current_user.workspace_id)
        .order_by(ApprovedFact.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if brand_profile_id:
        query = query.where(ApprovedFact.brand_profile_id == brand_profile_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=ApprovedFactRead, status_code=status.HTTP_201_CREATED)
async def create_approved_fact(
    payload: ApprovedFactCreate,
    current_user: ReviewerUser,
    session: SessionDep,
) -> ApprovedFact:
    """Ingests a verified fact with strict expiry dates and 1536-dim vector embedding."""
    fact = ApprovedFact(
        workspace_id=payload.workspace_id or current_user.workspace_id,
        brand_profile_id=payload.brand_profile_id,
        fact_statement=payload.fact_statement,
        original_source_url=payload.original_source_url,
        evidence_excerpt=payload.evidence_excerpt,
        verification_date=payload.verification_date,
        expiry_date=payload.expiry_date,
        responsible_owner_id=payload.responsible_owner_id,
        embedding=payload.embedding,
    )
    session.add(fact)
    await session.flush()
    return fact


@router.get("/stale", response_model=list[ApprovedFactRead])
async def list_stale_facts(
    current_user: CurrentUser,
    session: SessionDep,
) -> list[ApprovedFact]:
    """Retrieves all expired facts triggering automated re-verification sweeps."""
    now = datetime.now(timezone.utc)
    query = (
        select(ApprovedFact)
        .where(
            ApprovedFact.workspace_id == current_user.workspace_id,
            ApprovedFact.expiry_date <= now,
            ApprovedFact.is_active == True,  # noqa: E712
        )
        .order_by(ApprovedFact.expiry_date.asc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/search/semantic", response_model=list[ApprovedFactRead])
async def search_facts_semantic(
    query_embedding: list[float],
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=5, ge=1, le=20),
) -> list[ApprovedFact]:
    """HNSW-accelerated semantic vector search for verified facts."""
    if len(query_embedding) != 1536:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query embedding must be exactly 1536 dimensions, got {len(query_embedding)}",
        )

    now = datetime.now(timezone.utc)
    # Cosine distance ordering utilizing pgvector index or portable dialect
    query = (
        select(ApprovedFact)
        .where(
            ApprovedFact.workspace_id == current_user.workspace_id,
            ApprovedFact.expiry_date > now,  # Exclude expired facts from active claim grounding
            ApprovedFact.is_active == True,  # noqa: E712
        )
        .order_by(ApprovedFact.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post(
    "/{fact_id}/blast-radius",
    response_model=BlastRadiusTriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Reverse Blast-Radius Traversal on Fact",
)
async def trigger_fact_blast_radius(
    fact_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    trigger_reason: str = Query(default="EXPIRED"),
) -> BlastRadiusTriggerResponse:
    """
    Traverses the bi-directional citation knowledge graph in O(1) indexed time to locate
    all previously APPROVED collateral citing or depending on this fact. Automatically flags
    affected submissions as needing re-verification and atomically enqueues transactional outbox events.
    """
    from app.services.governance.blast_radius_service import BlastRadiusService
    return await BlastRadiusService.trigger_fact_blast_radius(
        session=session,
        fact_id=fact_id,
        trigger_reason=trigger_reason,
        actor_id=current_user.id,
    )

