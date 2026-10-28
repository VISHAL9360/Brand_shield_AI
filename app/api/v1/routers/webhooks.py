"""
BrandShield AI - Transactional Outbox & Webhook Router.
Exposes endpoints to:
1. Trigger outbox queue processing (POST /api/v1/webhooks/outbox/flush).
2. Replay quarantined Dead-Letter Queue events (POST /api/v1/webhooks/dlq/{id}/replay).
3. Register and inspect tenant webhook endpoints (POST / GET /api/v1/webhooks/subscriptions).
4. Inspect outbox events and delivery diagnostics (GET /api/v1/webhooks/outbox).
"""

from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentUser, SessionDep
from app.core.exceptions import NotFoundProblem
from app.domain.enums import UserRole
from app.domain.schemas.blast_radius import (
    OutboxEventRead,
    OutboxFlushResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionRead,
)
from app.infrastructure.db.models import OutboxWebhookEvent, WebhookSubscription
from app.services.governance.outbox_dispatcher import OutboxDispatcher

router = APIRouter()


@router.post(
    "/outbox/flush",
    response_model=OutboxFlushResponse,
    status_code=status.HTTP_200_OK,
    summary="Flush Outbox Queue & Dispatch Webhooks",
)
async def flush_outbox_queue(
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=100),
) -> OutboxFlushResponse:
    """
    Executes an outbox dispatcher sweep, attempting delivery of all PENDING or
    FAILED_RETRYING webhook events whose exponential backoff threshold has arrived.
    """
    res = await OutboxDispatcher.flush_outbox(session=session, limit=limit)
    return OutboxFlushResponse(**res)


@router.post(
    "/dlq/{event_id}/replay",
    response_model=OutboxEventRead,
    status_code=status.HTTP_200_OK,
    summary="Replay Quarantined Dead-Letter Queue (DLQ) Event",
)
async def replay_dlq_event(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> OutboxWebhookEvent:
    """
    Requeues a permanently failed webhook event quarantined in DEAD_LETTER_QUEUE,
    resetting its attempt counter and triggering an immediate redelivery attempt.
    """
    return await OutboxDispatcher.replay_dlq_event(session=session, event_id=event_id)


@router.post(
    "/subscriptions",
    response_model=WebhookSubscriptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Webhook Subscription",
)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> WebhookSubscription:
    """
    Registers a new tenant webhook callback URI with shared secret for HMAC-SHA256 verification.
    """
    subscription = WebhookSubscription(
        id=uuid.uuid4(),
        workspace_id=payload.workspace_id or current_user.workspace_id,
        brand_profile_id=payload.brand_profile_id,
        target_url=payload.target_url,
        secret_token=payload.secret_token,
        event_types=payload.event_types,
        is_active=True,
    )
    session.add(subscription)
    await session.flush()
    return subscription


@router.get(
    "/subscriptions",
    response_model=list[WebhookSubscriptionRead],
    status_code=status.HTTP_200_OK,
    summary="List Registered Webhook Subscriptions",
)
async def list_webhook_subscriptions(
    current_user: CurrentUser,
    session: SessionDep,
    brand_profile_id: Optional[uuid.UUID] = Query(None),
) -> list[WebhookSubscription]:
    """Retrieves all active webhook subscriptions for tenant workspace."""
    query = select(WebhookSubscription).where(
        WebhookSubscription.workspace_id == current_user.workspace_id,
        WebhookSubscription.is_active == True,  # noqa: E712
    )
    if brand_profile_id:
        query = query.where(WebhookSubscription.brand_profile_id == brand_profile_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get(
    "/outbox",
    response_model=list[OutboxEventRead],
    status_code=status.HTTP_200_OK,
    summary="Inspect Outbox Webhook Events",
)
async def list_outbox_events(
    current_user: CurrentUser,
    session: SessionDep,
    delivery_status: Optional[str] = Query(None),
    brand_profile_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[OutboxWebhookEvent]:
    """Inspects pending, delivered, or DLQ outbox events."""
    query = select(OutboxWebhookEvent).order_by(OutboxWebhookEvent.created_at.desc()).limit(limit)
    if delivery_status:
        query = query.where(OutboxWebhookEvent.delivery_status == delivery_status)
    if brand_profile_id:
        query = query.where(OutboxWebhookEvent.brand_profile_id == brand_profile_id)
    result = await session.execute(query)
    return list(result.scalars().all())
