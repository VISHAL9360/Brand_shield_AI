"""Add reverse blast-radius citation graph, outbox dispatcher, and publication attestation CA.

Revision ID: 002_blast_radius_outbox_attestation
Revises: 001_initial_schema
Create Date: 2026-10-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_blast_radius_outbox_attestation"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Extend Audit Action ENUM in PostgreSQL if applicable
    if is_postgres:
        new_audit_actions = [
            "BLAST_RADIUS_EVALUATED",
            "OUTBOX_EVENT_QUEUED",
            "OUTBOX_DISPATCH_SUCCESS",
            "OUTBOX_DISPATCH_FAILURE",
            "WEBHOOK_SUBSCRIBED",
            "WEBHOOK_UNSUBSCRIBED",
            "ATTESTATION_CERTIFICATE_MINTED",
            "ATTESTATION_VERIFIED",
            "ATTESTATION_VERIFICATION_FAILED",
            "FALSE_POSITIVE_CRITIQUE_APPLIED",
        ]
        for action in new_audit_actions:
            op.execute(f"ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS '{action}';")

    # 2. Add Adversarial Critic fields to findings table
    op.add_column(
        "findings",
        sa.Column("epistemic_uncertainty_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("counterfactual_risk_summary", sa.Text(), nullable=True),
    )

    # 3. citation_dependency_edges table
    op.create_table(
        "citation_dependency_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_fact_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("approved_facts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("linked_guideline_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_guidelines.id", ondelete="CASCADE"), nullable=True),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("cited_text_snippet", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_citation_edges_fact_id", "citation_dependency_edges", ["linked_fact_id"])
    op.create_index("ix_citation_edges_sub_rev", "citation_dependency_edges", ["submission_id", "revision_id"])

    # 4. outbox_events table
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=False),
        sa.Column("delivery_status", sa.String(32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("backoff_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outbox_status_backoff", "outbox_events", ["delivery_status", "backoff_until"])
    op.create_index("ix_outbox_brand_status", "outbox_events", ["brand_profile_id", "delivery_status"])

    # 5. webhook_subscriptions table
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_url", sa.String(512), nullable=False),
        sa.Column("secret_token", sa.String(255), nullable=False),
        sa.Column("event_types", postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'[\"*\"]'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_webhook_subs_brand_active", "webhook_subscriptions", ["brand_profile_id", "is_active"])

    # 6. publication_attestation_certificates table
    op.create_table(
        "publication_attestation_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approved_revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_sha256_hash", sa.String(64), nullable=False, index=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merkle_root_of_cited_facts_and_guidelines", sa.String(64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("cryptographic_signature", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pub_attest_sub_active", "publication_attestation_certificates", ["submission_id", "status"])
    op.create_index("ix_pub_attest_validity", "publication_attestation_certificates", ["valid_until", "status"])


def downgrade() -> None:
    op.drop_table("publication_attestation_certificates")
    op.drop_table("webhook_subscriptions")
    op.drop_table("outbox_events")
    op.drop_table("citation_dependency_edges")
    op.drop_column("findings", "counterfactual_risk_summary")
    op.drop_column("findings", "epistemic_uncertainty_score")
