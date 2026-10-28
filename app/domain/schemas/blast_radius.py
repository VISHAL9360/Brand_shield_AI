"""
BrandShield AI - Blast-Radius & Transactional Outbox Schemas.
Pydantic v2 contracts for the reverse blast-radius citation graph,
transactional outbox events, and webhook subscriptions.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CharacterSpanCitation(BaseModel):
    """Granular character-level citation span affected by fact mutation or staleness."""
    submission_id: uuid.UUID
    submission_title: str
    revision_id: uuid.UUID
    revision_number: int
    finding_id: uuid.UUID
    start_offset: int = Field(..., ge=0)
    end_offset: int = Field(..., ge=0)
    citation_hash: str

    model_config = ConfigDict(from_attributes=True)


class BlastRadiusTriggerResponse(BaseModel):
    """
    Enterprise Blast-Radius calculation and outbox dispatch result.
    Returned when a fact expires, is revoked, or triggers retroactive re-verification.
    """
    fact_id: uuid.UUID
    fact_statement: str
    expiry_date: Optional[datetime] = None
    trigger_reason: str = "EXPIRED"
    brand_profile_id: Optional[uuid.UUID] = None
    affected_submissions_count: int = Field(..., ge=0, description="Total previously APPROVED submissions affected")
    affected_pages: int = Field(..., ge=0, description="Estimated total pages impacted across enterprise collateral")
    affected_citations_count: int = Field(..., ge=0, description="Total citation dependency edges traversed")
    exact_character_spans: list[CharacterSpanCitation] = Field(default_factory=list)
    outbox_event_id: Optional[uuid.UUID] = None
    outbox_delivery_status: str = "PENDING"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class EnterpriseBlastRadiusOverview(BaseModel):
    """Executive enterprise-wide citation graph & blast radius diagnostic overview."""
    workspace_id: uuid.UUID
    brand_profile_id: Optional[uuid.UUID] = None
    total_citation_edges: int = Field(..., ge=0)
    total_stale_facts: int = Field(..., ge=0)
    total_affected_approved_submissions: int = Field(..., ge=0)
    total_outbox_events_pending: int = Field(..., ge=0)
    total_outbox_events_delivered: int = Field(..., ge=0)
    total_outbox_events_dlq: int = Field(..., ge=0)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WebhookSubscriptionCreate(BaseModel):
    """Payload to register a new webhook destination."""
    workspace_id: uuid.UUID
    brand_profile_id: uuid.UUID
    target_url: str = Field(..., description="HTTPS callback endpoint")
    secret_token: str = Field(..., min_length=16, description="Shared secret for HMAC-SHA256 signature verification")
    event_types: list[str] = Field(default_factory=lambda: ["*"])

    model_config = ConfigDict(from_attributes=True)


class WebhookSubscriptionRead(BaseModel):
    """Subscription record returned to tenant."""
    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_profile_id: uuid.UUID
    target_url: str
    event_types: list[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutboxEventRead(BaseModel):
    """Outbox event record detailing delivery status and retry schedule."""
    id: uuid.UUID
    brand_profile_id: uuid.UUID
    event_type: str
    payload_json: dict[str, Any]
    hmac_signature: str
    delivery_status: str
    attempt_count: int
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OutboxFlushResponse(BaseModel):
    """Summary of outbox events flushed to external webhooks."""
    processed_count: int
    delivered_count: int
    failed_retrying_count: int
    dlq_count: int
    duration_ms: float
