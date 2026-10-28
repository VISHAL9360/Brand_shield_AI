"""
BrandShield AI - Transactional Outbox Webhook Dispatcher.
Implements the AWS/Stripe Transactional Outbox pattern:
- Cryptographic HMAC-SHA256 signature sealing (X-BrandShield-Signature-256).
- Exponential backoff retry calculations (2^attempt * base_delay).
- Dead-Letter Queue (DLQ) state transitions and replay capabilities.
- Atomic commit within the same database transaction as blast-radius mutations.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Optional
import uuid

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundProblem
from app.domain.enums import AuditAction, WebhookDeliveryStatus
from app.infrastructure.db.models import OutboxWebhookEvent, WebhookSubscription
from app.services.audit_service import AuditService

logger = logging.getLogger("brandshield.services.governance.outbox")
settings = get_settings()

MAX_OUTBOX_ATTEMPTS = 5
DEFAULT_BASE_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 3600.0


class OutboxDispatcher:
    """
    Engine driving transactional outbox webhook processing, HMAC signing,
    and DLQ lifecycle operations.
    """

    @staticmethod
    def canonical_json(payload: Any) -> str:
        """Produces deterministic, compact JSON for cryptographic HMAC signing."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def sign_payload(cls, secret_token: str, payload: Any) -> str:
        """
        Signs outgoing webhook payload using HMAC-SHA256.
        Returns the hex digest.
        """
        canonical_str = cls.canonical_json(payload)
        return hmac.new(
            secret_token.encode("utf-8"),
            canonical_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def verify_signature(cls, secret_token: str, payload: Any, signature_header: str) -> bool:
        """Validates incoming or recorded HMAC-SHA256 signature in constant time."""
        clean_sig = signature_header.removeprefix("sha256=")
        expected = cls.sign_payload(secret_token, payload)
        return hmac.compare_digest(expected, clean_sig)

    @classmethod
    def calculate_next_retry(
        cls,
        attempt_count: int,
        base_delay_seconds: float = DEFAULT_BASE_DELAY_SECONDS,
        max_delay_seconds: float = MAX_DELAY_SECONDS,
    ) -> datetime:
        """
        Calculates exponential backoff: delay = min(max_delay, 2^attempt * base_delay).
        """
        delay = min(max_delay_seconds, (2 ** attempt_count) * base_delay_seconds)
        return datetime.now(timezone.utc) + timedelta(seconds=delay)

    @classmethod
    async def enqueue_event(
        cls,
        session: AsyncSession,
        brand_profile_id: uuid.UUID,
        event_type: str,
        payload_json: dict[str, Any],
        secret_token: Optional[str] = None,
    ) -> OutboxWebhookEvent:
        """
        Atomically enqueues a webhook event into OutboxWebhookEvent within the active DB transaction.
        """
        secret = secret_token
        if not secret:
            # Query subscription for this brand profile
            sub_q = select(WebhookSubscription).where(
                WebhookSubscription.brand_profile_id == brand_profile_id,
                WebhookSubscription.is_active == True,  # noqa: E712
            )
            sub_res = await session.execute(sub_q)
            scalars_res = sub_res.scalars()
            subscription = scalars_res.first() if hasattr(scalars_res, "first") else None
            if subscription and hasattr(subscription, "secret_token") and isinstance(subscription.secret_token, str):
                secret = subscription.secret_token
            else:
                raw_secret = getattr(settings, "WEBHOOK_SECRET_KEY", None) or getattr(settings, "SECRET_KEY", "brandshield-secret-2026")
                secret = str(raw_secret)

        if not isinstance(secret, str):
            secret = "brandshield-secret-key-32-chars-long"

        signature = cls.sign_payload(secret, payload_json)
        now = datetime.now(timezone.utc)

        outbox_event = OutboxWebhookEvent(
            id=uuid.uuid4(),
            brand_profile_id=brand_profile_id,
            event_type=event_type,
            payload_json=payload_json,
            hmac_signature=signature,
            delivery_status=WebhookDeliveryStatus.PENDING.value,
            attempt_count=0,
            next_retry_at=now,
            last_error=None,
            created_at=now,
            delivered_at=None,
        )
        session.add(outbox_event)
        await session.flush()

        await AuditService.record_event(
            session=session,
            action=AuditAction.WEBHOOK_OUTBOX_ENQUEUED,
            workspace_id=payload_json.get("workspace_id"),
            actor_id=None,
            payload={
                "outbox_event_id": str(outbox_event.id),
                "brand_profile_id": str(brand_profile_id),
                "event_type": event_type,
                "hmac_signature_prefix": signature[:12] + "...",
            },
        )
        return outbox_event

    @classmethod
    async def dispatch_single_event(
        cls,
        session: AsyncSession,
        event: OutboxWebhookEvent,
        client: Optional[httpx.AsyncClient] = None,
        max_attempts: int = MAX_OUTBOX_ATTEMPTS,
    ) -> bool:
        """
        Attempts HTTP delivery for an outbox event with HMAC header and backoff retry.
        """
        # Resolve target endpoint from active subscriptions
        sub_q = select(WebhookSubscription).where(
            WebhookSubscription.brand_profile_id == event.brand_profile_id,
            WebhookSubscription.is_active == True,  # noqa: E712
        )
        sub_res = await session.execute(sub_q)
        subscriptions = list(sub_res.scalars().all())

        now = datetime.now(timezone.utc)

        # If no explicit external subscriptions are registered, simulate internal delivery sink
        if not subscriptions:
            event.delivery_status = WebhookDeliveryStatus.DELIVERED.value
            event.delivered_at = now
            event.last_error = None
            await session.flush()
            return True

        target_urls = [s.target_url for s in subscriptions]
        delivery_success = True
        last_error_msg = None

        headers = {
            "Content-Type": "application/json",
            "X-BrandShield-Signature-256": f"sha256={event.hmac_signature}",
            "X-BrandShield-Event": event.event_type,
            "X-BrandShield-Delivery": str(event.id),
            "User-Agent": "BrandShield-WebhookDispatcher/2.0",
        }

        should_close_client = False
        http_client = client
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=5.0)
            should_close_client = True

        try:
            for url in target_urls:
                try:
                    resp = await http_client.post(url, json=event.payload_json, headers=headers)
                    if not (200 <= resp.status_code < 300):
                        delivery_success = False
                        last_error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        break
                except Exception as exc:
                    delivery_success = False
                    last_error_msg = f"Connection error to {url}: {str(exc)}"
                    break
        finally:
            if should_close_client:
                await http_client.aclose()

        if delivery_success:
            event.delivery_status = WebhookDeliveryStatus.DELIVERED.value
            event.delivered_at = now
            event.last_error = None
            await session.flush()
            await AuditService.record_event(
                session=session,
                action=AuditAction.WEBHOOK_DISPATCHED,
                workspace_id=event.payload_json.get("workspace_id"),
                actor_id=None,
                payload={
                    "outbox_event_id": str(event.id),
                    "event_type": event.event_type,
                    "target_urls": target_urls,
                },
            )
            return True
        else:
            event.attempt_count += 1
            event.last_error = last_error_msg

            if event.attempt_count >= max_attempts:
                event.delivery_status = WebhookDeliveryStatus.DEAD_LETTER_QUEUE.value
                event.next_retry_at = None
                logger.error(
                    "Outbox event %s moved to DEAD_LETTER_QUEUE after %d attempts: %s",
                    event.id,
                    event.attempt_count,
                    last_error_msg,
                )
            else:
                event.delivery_status = WebhookDeliveryStatus.FAILED_RETRYING.value
                event.next_retry_at = cls.calculate_next_retry(event.attempt_count)
                logger.warning(
                    "Outbox event %s failed (attempt %d/%d). Next retry at %s: %s",
                    event.id,
                    event.attempt_count,
                    max_attempts,
                    event.next_retry_at,
                    last_error_msg,
                )

            await session.flush()
            await AuditService.record_event(
                session=session,
                action=AuditAction.WEBHOOK_FAILED,
                workspace_id=event.payload_json.get("workspace_id"),
                actor_id=None,
                payload={
                    "outbox_event_id": str(event.id),
                    "attempt_count": event.attempt_count,
                    "delivery_status": event.delivery_status,
                    "last_error": last_error_msg,
                },
            )
            return False

    @classmethod
    async def flush_outbox(
        cls,
        session: AsyncSession,
        limit: int = 50,
        client: Optional[httpx.AsyncClient] = None,
    ) -> dict[str, Any]:
        """
        Dispatches all pending and retrying webhook events whose retry timestamp has arrived.
        """
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc)

        query = (
            select(OutboxWebhookEvent)
            .where(
                OutboxWebhookEvent.delivery_status.in_([
                    WebhookDeliveryStatus.PENDING.value,
                    WebhookDeliveryStatus.FAILED_RETRYING.value,
                ]),
                or_(
                    OutboxWebhookEvent.next_retry_at == None,  # noqa: E711
                    OutboxWebhookEvent.next_retry_at <= now,
                ),
            )
            .order_by(OutboxWebhookEvent.created_at.asc())
            .limit(limit)
        )
        result = await session.execute(query)
        events = list(result.scalars().all())

        delivered = 0
        failed_retrying = 0
        dlq = 0

        for event in events:
            ok = await cls.dispatch_single_event(session=session, event=event, client=client)
            if ok:
                delivered += 1
            elif event.delivery_status == WebhookDeliveryStatus.DEAD_LETTER_QUEUE.value:
                dlq += 1
            else:
                failed_retrying += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "processed_count": len(events),
            "delivered_count": delivered,
            "failed_retrying_count": failed_retrying,
            "dlq_count": dlq,
            "duration_ms": round(elapsed_ms, 2),
        }

    @classmethod
    async def replay_dlq_event(
        cls,
        session: AsyncSession,
        event_id: uuid.UUID,
        client: Optional[httpx.AsyncClient] = None,
    ) -> OutboxWebhookEvent:
        """
        Replays an event quarantined in Dead-Letter Queue (DLQ), resetting attempts and redelivering.
        """
        event = await session.get(OutboxWebhookEvent, event_id)
        if not event:
            raise NotFoundProblem(
                detail=f"OutboxWebhookEvent '{event_id}' not found.",
                resource_type="OutboxWebhookEvent",
                resource_id=str(event_id),
            )

        event.delivery_status = WebhookDeliveryStatus.PENDING.value
        event.attempt_count = 0
        event.next_retry_at = datetime.now(timezone.utc)
        event.last_error = None
        await session.flush()

        await AuditService.record_event(
            session=session,
            action=AuditAction.WEBHOOK_DLQ_REPLAYED,
            workspace_id=event.payload_json.get("workspace_id"),
            actor_id=None,
            payload={"outbox_event_id": str(event.id), "event_type": event.event_type},
        )

        # Attempt immediate dispatch
        await cls.dispatch_single_event(session=session, event=event, client=client)
        return event
