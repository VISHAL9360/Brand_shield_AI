"""
BrandShield AI - Enterprise Database Domain Models
Production-Grade Asynchronous PostgreSQL Schema with pgvector and strict constraints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from app.infrastructure.db.custom_types import PortableVector, PortableSearchVector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    CheckConstraint,
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    AuditAction,
    CreatorAction,
    DetectorSource,
    FindingCategory,
    GuidelineCategory,
    ReviewSignOff,
    SeverityLevel,
    TriageStatus,
    UserRole,
    WebhookDeliveryStatus,
    WorkflowState,
)
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ==============================================================================
# Custom PostgreSQL Native Enum Types
# ==============================================================================

user_role_enum = ENUM(
    UserRole,
    name="user_role_enum",
    create_type=False,
    metadata=Base.metadata,
)
workflow_state_enum = ENUM(
    WorkflowState,
    name="workflow_state_enum",
    create_type=False,
    metadata=Base.metadata,
)
guideline_category_enum = ENUM(
    GuidelineCategory,
    name="guideline_category_enum",
    create_type=False,
    metadata=Base.metadata,
)
finding_category_enum = ENUM(
    FindingCategory,
    name="finding_category_enum",
    create_type=False,
    metadata=Base.metadata,
)
severity_level_enum = ENUM(
    SeverityLevel,
    name="severity_level_enum",
    create_type=False,
    metadata=Base.metadata,
)
triage_status_enum = ENUM(
    TriageStatus,
    name="triage_status_enum",
    create_type=False,
    metadata=Base.metadata,
)
detector_source_enum = ENUM(
    DetectorSource,
    name="detector_source_enum",
    create_type=False,
    metadata=Base.metadata,
)
creator_action_enum = ENUM(
    CreatorAction,
    name="creator_action_enum",
    create_type=False,
    metadata=Base.metadata,
)
review_signoff_enum = ENUM(
    ReviewSignOff,
    name="review_signoff_enum",
    create_type=False,
    metadata=Base.metadata,
)


# ==============================================================================
# 1. Multi-Tenant Workspaces & RBAC Users
# ==============================================================================

class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Multi-tenant isolation boundary for enterprise brand assets and policies.
    """
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-readable enterprise client organization name."
    )
    slug: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-safe unique identifier for tenant routing."
    )
    api_key_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="SHA-256 hash of provisioned programmatic API key."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Soft-disable flag for suspended enterprise tenants."
    )

    # Relationships
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    brand_profiles: Mapped[list[BrandProfile]] = relationship(
        "BrandProfile",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    approved_facts: Mapped[list[ApprovedFact]] = relationship(
        "ApprovedFact",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list[AuditLedger]] = relationship(
        "AuditLedger",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Enterprise actor supporting strict RBAC: CREATOR, REVIEWER, ADMINISTRATOR.
    """
    __tablename__ = "users"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent tenant identifier."
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Primary login identity."
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt/Argon2 password hash."
    )
    full_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Legal actor display name."
    )
    role: Mapped[UserRole] = mapped_column(
        user_role_enum,
        nullable=False,
        index=True,
        doc="RBAC role governing platform authorization."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Account active status flag."
    )

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint("workspace_id", "email", name="uq_users_workspace_email"),
        Index("ix_users_workspace_role", "workspace_id", "role"),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="users")
    created_submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="creator",
        foreign_keys="Submission.creator_id",
    )
    assigned_submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="assigned_reviewer",
        foreign_keys="Submission.assigned_reviewer_id",
    )
    created_revisions: Mapped[list[DocumentRevision]] = relationship(
        "DocumentRevision",
        back_populates="created_by",
    )
    owned_facts: Mapped[list[ApprovedFact]] = relationship(
        "ApprovedFact",
        back_populates="responsible_owner",
    )
    review_decisions: Mapped[list[ReviewDecision]] = relationship(
        "ReviewDecision",
        back_populates="reviewer",
    )


# ==============================================================================
# 2. Brand Profiles & Privacy Gate Configuration
# ==============================================================================

class BrandProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Configurable brand guidelines container, terminology matrices, and zero-trust privacy gate.
    """
    __tablename__ = "brand_profiles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent tenant identifier."
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Brand profile identity (e.g., 'North America Enterprise B2B')."
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Contextual briefing and organizational scope."
    )
    tone_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        doc="Target formality (1-10), enthusiasm, reading grade level, and forbidden sentiments."
    )
    banned_terminology_map: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        doc="Map of strictly prohibited terms -> {reason, violation_severity, suggested_replacements}."
    )
    preferred_terminology_map: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        doc="Map of deprecated or discouraged phrases -> approved corporate vocabulary."
    )
    messaging_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        doc="Mandatory legal disclaimers, required footnotes, and positioning directives."
    )
    privacy_gate_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "allow_external_llm": False,
            "approved_providers": [],
            "contract_verified_at": None,
            "retention_days": 30,
        },
        server_default=text(
            '\'{"allow_external_llm": false, "approved_providers": [], "contract_verified_at": null, "retention_days": 30}\'::jsonb'
        ),
        doc="Zero-trust privacy gate policy: external LLM egress clearance and data retention bounds."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Active status flag."
    )

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_brand_profile_workspace_name"),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="brand_profiles")
    guidelines: Mapped[list[BrandGuideline]] = relationship(
        "BrandGuideline",
        back_populates="brand_profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="brand_profile",
    )


# ==============================================================================
# 3. Brand Guidelines (Hybrid RAG: Vector + Full-Text Search)
# ==============================================================================

class BrandGuideline(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Granular regulatory and brand directive clauses indexed with HNSW and GIN search vectors.
    """
    __tablename__ = "brand_guidelines"

    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent brand profile."
    )
    clause_identifier: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Enterprise citation clause ID (e.g. 'SEC-TONE-01', 'LEGAL-DISCLAIMER-04')."
    )
    clause_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Normative compliance requirement and policy wording."
    )
    category: Mapped[GuidelineCategory] = mapped_column(
        guideline_category_enum,
        nullable=False,
        index=True,
        doc="Directive classification (TONE, TERMINOLOGY, MESSAGING, ACCESSIBILITY)."
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        severity_level_enum,
        nullable=False,
        index=True,
        doc="Default enforcement severity if breached."
    )
    embedding: Mapped[list[float]] = mapped_column(
        PortableVector(1536),
        nullable=False,
        doc="1536-dimensional semantic dense vector representation."
    )
    search_vector: Mapped[str] = mapped_column(
        PortableSearchVector,
        Computed("to_tsvector('english', clause_text)", persisted=True),
        nullable=False,
        doc="Generated TSVECTOR index column for hybrid BM25 lexical retrieval."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Active flag."
    )

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint(
            "brand_profile_id", "clause_identifier", name="uq_guidelines_profile_clause"
        ),
        Index(
            "ix_brand_guidelines_profile_cat_sev",
            "brand_profile_id",
            "category",
            "severity",
        ),
        # HNSW Vector Index for dense cosine similarity
        Index(
            "ix_brand_guidelines_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # GIN Full-Text Index for sparse keyword search
        Index(
            "ix_brand_guidelines_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    # Relationships
    brand_profile: Mapped[BrandProfile] = relationship(
        "BrandProfile", back_populates="guidelines"
    )
    findings: Mapped[list[Finding]] = relationship(
        "Finding", back_populates="linked_guideline"
    )


# ==============================================================================
# 4. Approved Facts & Temporal Staleness Engine
# ==============================================================================

class ApprovedFact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Substantiated ground-truth repository carrying strict verification windows.
    Zero-hallucination safeguard rejects ungrounded or expired marketing statements.
    """
    __tablename__ = "approved_facts"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent tenant boundary."
    )
    brand_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        default=None,
        doc="Optional brand profile association boundary."
    )
    fact_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Factual marketing or quantitative claim approved by legal/clinical reviewers."
    )
    original_source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Canonical URI or repository path containing primary substantiation."
    )
    evidence_excerpt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Exact excerpted citation proving the factual validity of the claim."
    )
    verification_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp when the claim was certified by compliance counsel."
    )
    last_updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("clock_timestamp()"),
        doc="Timestamp of most recent substantive review or metric re-evaluation."
    )
    expiry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Strict temporal validity threshold; facts past this timestamp trigger staleness triage."
    )
    responsible_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Internal corporate owner responsible for fact recertification."
    )
    embedding: Mapped[list[float]] = mapped_column(
        PortableVector(1536),
        nullable=False,
        doc="1536-dimensional dense embedding of the fact statement."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Active flag."
    )

    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint("expiry_date > verification_date", name="chk_facts_valid_expiry_window"),
        # Index tailored for rapid temporal staleness queries and background re-verification sweeps
        Index(
            "ix_approved_facts_workspace_expiry",
            "workspace_id",
            "expiry_date",
            "is_active",
        ),
        # HNSW index for sub-10ms semantic fact lookup
        Index(
            "ix_approved_facts_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="approved_facts")
    responsible_owner: Mapped[User] = relationship("User", back_populates="owned_facts")
    findings: Mapped[list[Finding]] = relationship("Finding", back_populates="linked_fact")

    @property
    def source_url(self) -> str:
        return self.original_source_url

    @source_url.setter
    def source_url(self, val: str) -> None:
        self.original_source_url = val


class ApprovedBrandAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Organization brand asset registry tracking logos, icons, and graphics with perceptual hashes.
    """
    __tablename__ = "approved_brand_assets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent tenant boundary.",
    )
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent brand profile.",
    )
    asset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Official brand asset title.",
    )
    asset_category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="LOGO",
        doc="Asset classification (LOGO, ICON, BADGE, PRODUCT_GRAPHIC).",
    )
    phash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="64-bit perceptual frequency hash in hex format.",
    )
    dhash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="64-bit perceptual difference hash in hex format.",
    )
    color_palette: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        doc="Primary and secondary hex color palette.",
    )
    aspect_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        doc="Native width/height ratio.",
    )
    file_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="CDN asset storage location.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Active flag.",
    )


# ==============================================================================
# 5. Submissions & Immutable Git-Like Revision DAG
# ==============================================================================

class Submission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Root document entity tracking governance workflow progression.
    """
    __tablename__ = "submissions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent tenant identifier."
    )
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Brand profile against which this document is governed."
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Authoring user who submitted the asset."
    )
    assigned_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Assigned human reviewer for ambiguous triage and final sign-off."
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Asset document title or campaign name."
    )
    document_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Input MIME classification (e.g. 'PDF', 'DOCX', 'MARKDOWN')."
    )
    workflow_state: Mapped[WorkflowState] = mapped_column(
        workflow_state_enum,
        nullable=False,
        default=WorkflowState.SUBMITTED,
        index=True,
        doc="Current state machine location."
    )
    current_revision_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_revisions.id",
            use_alter=True,
            name="fk_submissions_current_revision_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        doc="Pointer to tip revision in the immutable DAG."
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        doc="Optimistic concurrency control version counter."
    )

    # Indexes
    __table_args__ = (
        Index("ix_submissions_workspace_state", "workspace_id", "workflow_state"),
        Index("ix_submissions_reviewer_state", "assigned_reviewer_id", "workflow_state"),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="submissions")
    brand_profile: Mapped[BrandProfile] = relationship("BrandProfile", back_populates="submissions")
    creator: Mapped[User] = relationship(
        "User", back_populates="created_submissions", foreign_keys=[creator_id]
    )
    assigned_reviewer: Mapped[Optional[User]] = relationship(
        "User", back_populates="assigned_submissions", foreign_keys=[assigned_reviewer_id]
    )
    revisions: Mapped[list[DocumentRevision]] = relationship(
        "DocumentRevision",
        back_populates="submission",
        foreign_keys="DocumentRevision.submission_id",
        order_by="DocumentRevision.revision_number",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    current_revision: Mapped[Optional[DocumentRevision]] = relationship(
        "DocumentRevision",
        foreign_keys=[current_revision_id],
        post_update=True,
    )
    review_decisions: Mapped[list[ReviewDecision]] = relationship(
        "ReviewDecision",
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DocumentRevision(Base, UUIDPrimaryKeyMixin):
    """
    Append-only revision node in the immutable document revision DAG.
    Original content is NEVER overwritten. Revisions form an explicit parent-child lineage.
    """
    __tablename__ = "document_revisions"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Root submission lineage."
    )
    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Monotonically increasing ordinal revision number (1, 2, ...)."
    )
    parent_revision_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        doc="Pointer to parent revision node. Null only for initial genesis commit (v1)."
    )
    content_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full immutable snapshot of parsed document text content."
    )
    ast_span_map: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Granular AST map linking sentence/clause spans to character offsets and visual coordinates."
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Actor committing this revision."
    )
    sha256_content_hash: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        index=True,
        doc="SHA-256 cryptographic digest of content_text ensuring tamper detection."
    )
    diff_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Computed RFC 6902 JSON Patch or character-diff against parent revision."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        nullable=False,
        doc="Append-only revision creation timestamp."
    )

    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint("revision_number >= 1", name="chk_revision_number_positive"),
        UniqueConstraint("submission_id", "revision_number", name="uq_submission_revision_number"),
        Index("ix_revisions_submission_created", "submission_id", "created_at"),
    )

    # Relationships
    submission: Mapped[Submission] = relationship(
        "Submission", back_populates="revisions", foreign_keys=[submission_id]
    )
    created_by: Mapped[User] = relationship("User", back_populates="created_revisions")
    parent_revision: Mapped[Optional[DocumentRevision]] = relationship(
        "DocumentRevision",
        remote_side="DocumentRevision.id",
        back_populates="child_revisions",
    )
    child_revisions: Mapped[list[DocumentRevision]] = relationship(
        "DocumentRevision",
        back_populates="parent_revision",
    )
    findings: Mapped[list[Finding]] = relationship(
        "Finding",
        back_populates="revision",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    review_decisions: Mapped[list[ReviewDecision]] = relationship(
        "ReviewDecision",
        back_populates="revision",
    )


# ==============================================================================
# 6. Findings & Multi-Tier Confidence Triage Engine
# ==============================================================================

class Finding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Granular detection generated during document verification linked to an immutable revision.
    Enforces tri-state confidence triage and random anti-automation-bias audits.
    """
    __tablename__ = "findings"

    revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent immutable revision snapshot."
    )
    issue_category: Mapped[FindingCategory] = mapped_column(
        finding_category_enum,
        nullable=False,
        index=True,
        doc="Category of detected compliance anomaly."
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        severity_level_enum,
        nullable=False,
        index=True,
        doc="Finding severity level."
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Normalized algorithmic or model confidence score [0.0, 1.0]."
    )
    triage_status: Mapped[TriageStatus] = mapped_column(
        triage_status_enum,
        nullable=False,
        index=True,
        doc="Tri-state triage classification governing human vs. automated resolution."
    )
    start_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Starting character offset in revision content_text."
    )
    end_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Ending character offset in revision content_text."
    )
    explanation_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Actionable legal or policy justification for the finding."
    )
    suggested_correction: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Suggested replacement compliant with brand guidelines."
    )
    linked_guideline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_guidelines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Direct pointer to breached guideline clause."
    )
    linked_fact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approved_facts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Direct pointer to substantiated fact or stale reference."
    )
    detector_source: Mapped[DetectorSource] = mapped_column(
        detector_source_enum,
        nullable=False,
        index=True,
        doc="Pipeline origin: DETERMINISTIC_RULE, TEMPORAL_FACT_MATCHER, or EXTERNAL_LLM."
    )
    is_automation_bias_audit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        index=True,
        doc="Stochastic double-check safeguard injected to prevent reviewer rubber-stamping."
    )
    creator_action: Mapped[CreatorAction] = mapped_column(
        creator_action_enum,
        nullable=False,
        default=CreatorAction.PENDING,
        server_default=text("'PENDING'"),
        index=True,
        doc="Resolution action taken by author (PENDING, ACCEPTED, REJECTED, EDITED)."
    )
    creator_comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional rationale provided by author if rejecting or editing the finding."
    )
    epistemic_uncertainty_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0,
        server_default=text("0.0"),
        doc="Epistemic uncertainty score computed by Adversarial Critic [0.0, 1.0]."
    )
    counterfactual_risk_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Adversarial Critic explanation of brand/legal risk if published unedited."
    )

    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="chk_findings_confidence_range",
        ),
        CheckConstraint(
            "end_offset >= start_offset",
            name="chk_findings_offset_bounds",
        ),
        CheckConstraint(
            "start_offset >= 0",
            name="chk_findings_start_offset_non_negative",
        ),
        Index("ix_findings_revision_triage", "revision_id", "triage_status"),
        Index("ix_findings_revision_severity", "revision_id", "severity"),
        Index("ix_findings_audit_safeguard", "detector_source", "is_automation_bias_audit"),
    )

    # Relationships
    revision: Mapped[DocumentRevision] = relationship("DocumentRevision", back_populates="findings")
    linked_guideline: Mapped[Optional[BrandGuideline]] = relationship(
        "BrandGuideline", back_populates="findings"
    )
    linked_fact: Mapped[Optional[ApprovedFact]] = relationship(
        "ApprovedFact", back_populates="findings"
    )


# ==============================================================================
# 7. Review Decisions & Cryptographically Hash-Chained Audit Ledger
# ==============================================================================

class ReviewDecision(Base, UUIDPrimaryKeyMixin):
    """
    Formal human sign-off record executed by an authorized compliance Reviewer.
    """
    __tablename__ = "review_decisions"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Governed submission identifier."
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Specific revision snapshot evaluated."
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Reviewer identity executing the verdict."
    )
    decision: Mapped[ReviewSignOff] = mapped_column(
        review_signoff_enum,
        nullable=False,
        doc="Final human disposition: APPROVED or CHANGES_REQUESTED."
    )
    comments: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed reviewer guidance, legal stipulations, or approval rationale."
    )
    stipulations: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Structured conditions or mandatory disclosures attached to approval."
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        nullable=False,
        doc="Timestamp of human governance determination."
    )

    # Constraints & Indexes
    __table_args__ = (
        Index("ix_review_decisions_submission_decided", "submission_id", "decided_at"),
    )

    # Relationships
    submission: Mapped[Submission] = relationship("Submission", back_populates="review_decisions")
    revision: Mapped[DocumentRevision] = relationship("DocumentRevision", back_populates="review_decisions")
    reviewer: Mapped[User] = relationship("User", back_populates="review_decisions")


class AuditLedger(Base):
    """
    Append-only, cryptographically hash-chained tamper-evident audit ledger.
    Every row commits: current_hash = SHA-256(previous_hash || actor_id || action || payload || timestamp).
    Provides zero-repudiation regulatory guarantees for FTC, FDA, and SEC compliance.
    """
    __tablename__ = "audit_ledger"

    sequence_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="Monotonically increasing sequence index providing strict deterministic ordering."
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Tenant boundary for multi-tenant audit isolation."
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User initiating the action (null if automated system daemon)."
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Domain operation (e.g., 'DOCUMENT_SUBMITTED', 'EXTERNAL_LLM_DISCLOSED')."
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Comprehensive state snapshot or cryptographic diff of the operation."
    )
    previous_hash: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        doc="SHA-256 digest of the immediate predecessor audit row."
    )
    current_hash: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Cryptographic digest sealing this audit entry into the hash chain."
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        nullable=False,
        index=True,
        doc="Microsecond-accurate monotonic clock timestamp."
    )

    # Constraints & Indexes
    __table_args__ = (
        Index("ix_audit_ledger_workspace_timestamp", "workspace_id", "timestamp"),
        Index("ix_audit_ledger_action_timestamp", "action", "timestamp"),
    )

    # Relationships
    workspace: Mapped[Optional[Workspace]] = relationship("Workspace", back_populates="audit_logs")
    actor: Mapped[Optional[User]] = relationship("User")


# ==============================================================================
# 8. Bi-Directional Citation Knowledge Graph & Blast-Radius Engine
# ==============================================================================

class CitationDependencyEdge(Base, UUIDPrimaryKeyMixin):
    """
    Bi-directional citation knowledge graph edge.
    Explicitly tracks citation lineage between immutable revisions/findings and
    upstream compliance directives (BrandGuideline) or ground-truth evidence (ApprovedFact).
    Enables O(1) indexed reverse blast-radius traversal when facts expire or are revoked.
    """
    __tablename__ = "citation_dependency_edges"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Governed submission lineage root."
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Specific immutable document revision snapshot."
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Specific detection finding referencing the citation."
    )
    linked_fact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approved_facts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Pointer to upstream ApprovedFact ground-truth claim."
    )
    linked_guideline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_guidelines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Pointer to upstream BrandGuideline policy clause."
    )
    start_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Start character index of the cited claim in revision content_text."
    )
    end_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="End character index of the cited claim in revision content_text."
    )
    citation_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 fingerprint sealing the citation text span and target fact/guideline."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        nullable=False,
        doc="Edge creation timestamp."
    )

    # Constraints & Indexes
    __table_args__ = (
        Index("ix_citation_fact_sub", "linked_fact_id", "submission_id"),
        Index("ix_citation_guideline_sub", "linked_guideline_id", "submission_id"),
        Index("ix_citation_rev_finding", "revision_id", "finding_id"),
    )

    # Relationships
    submission: Mapped[Submission] = relationship("Submission")
    revision: Mapped[DocumentRevision] = relationship("DocumentRevision")
    finding: Mapped[Finding] = relationship("Finding")
    linked_fact: Mapped[Optional[ApprovedFact]] = relationship("ApprovedFact")
    linked_guideline: Mapped[Optional[BrandGuideline]] = relationship("BrandGuideline")


# ==============================================================================
# 9. Transactional Outbox Pattern & Webhook Subscriptions (AWS/Stripe Model)
# ==============================================================================

class OutboxWebhookEvent(Base, UUIDPrimaryKeyMixin):
    """
    Transactional Outbox event record (AWS/Stripe Pattern).
    Guarantees at-least-once asynchronous webhook delivery without two-phase commit (2PC) overhead.
    Events are committed within the same database transaction as blast-radius state mutations.
    """
    __tablename__ = "outbox_webhook_events"

    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target brand profile boundary."
    )
    event_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="Domain event name (e.g. 'fact.expired.blast_radius_triggered')."
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        doc="Event payload body dispatched to webhook endpoints."
    )
    hmac_signature: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="HMAC-SHA256 signature calculated over payload_json."
    )
    delivery_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
        index=True,
        doc="Outbox lifecycle: PENDING, DELIVERED, FAILED_RETRYING, DEAD_LETTER_QUEUE."
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Total delivery attempts executed."
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Timestamp after which dispatcher will retry with exponential backoff."
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Diagnostic response body or exception trace from most recent attempt."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        nullable=False,
        index=True,
        doc="Creation timestamp."
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Successful delivery timestamp."
    )

    __table_args__ = (
        Index("ix_outbox_status_next_retry", "delivery_status", "next_retry_at"),
        Index("ix_outbox_brand_status", "brand_profile_id", "delivery_status"),
    )

    # Relationships
    brand_profile: Mapped[BrandProfile] = relationship("BrandProfile")

    @property
    def payload(self) -> dict[str, Any]:
        """Convenience property alias for payload_json."""
        return self.payload_json

    @payload.setter
    def payload(self, val: dict[str, Any]) -> None:
        self.payload_json = val


class WebhookSubscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tenant webhook registration endpoint subscribing to governance & blast-radius events.
    """
    __tablename__ = "webhook_subscriptions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary."
    )
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target brand profile boundary."
    )
    target_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="HTTPS destination callback URI."
    )
    secret_token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Shared tenant secret key for HMAC-SHA256 signature verification."
    )
    event_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["*"],
        server_default=text("'[\"*\"]'::jsonb"),
        doc="List of subscribed event names or wildcard ['*']."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
        doc="Subscription active status flag."
    )

    __table_args__ = (
        Index("ix_webhook_subs_brand_active", "brand_profile_id", "is_active"),
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship("Workspace")
    brand_profile: Mapped[BrandProfile] = relationship("BrandProfile")


class PublicationAttestationCertificate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable Cryptographic Publication Clearance Certificate Authority.
    Minted when an authorized Reviewer or Administrator approves a submission.
    Binds the approved revision's SHA-256 hash, Merkle root of cited facts/guidelines,
    reviewer identity, and temporal validity window bounded by earliest fact expiry.
    """
    __tablename__ = "publication_attestation_certificates"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Approved submission reference."
    )
    approved_revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Exact approved document revision snapshot."
    )
    document_sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 digest of plaintext approved document content."
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Reviewer or Administrator who certified approval."
    )
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated brand profile authority."
    )
    merkle_root_of_cited_facts_and_guidelines: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Merkle root of cited facts and brand guideline clauses at time of clearance."
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC timestamp when clearance was minted."
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC expiration bounded by the earliest cited fact expiration."
    )
    cryptographic_signature: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="HMAC-SHA256 signature sealing canonical certificate contents."
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        nullable=False,
        index=True,
        doc="Attestation status: ACTIVE, REVOKED, or EXPIRED."
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Supplementary audit metadata including cited fact IDs and reviewer stipulations."
    )

    __table_args__ = (
        Index("ix_pub_attest_sub_active", "submission_id", "status"),
        Index("ix_pub_attest_validity", "valid_until", "status"),
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission")
    approved_revision: Mapped["DocumentRevision"] = relationship("DocumentRevision")
    reviewer: Mapped["User"] = relationship("User")
    brand_profile: Mapped["BrandProfile"] = relationship("BrandProfile")

