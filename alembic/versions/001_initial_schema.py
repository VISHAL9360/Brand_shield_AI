"""Initial schema migration for BrandShield AI enterprise production system.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-24 00:00:00.000000

Dual-dialect schema migration supporting:
1. Production PostgreSQL 16+ with native UUID, JSONB, ENUM, and pgvector(1536).
2. Portable zero-config SQLite with CHAR(36), JSON, and Text fallbacks.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # PostgreSQL-specific extensions and native ENUM types
    if is_postgres:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        for type_name, values in [
            ("user_role_enum", ("CREATOR", "REVIEWER", "ADMINISTRATOR")),
            ("workflow_state_enum", ("SUBMITTED", "ANALYZING", "TRIAGED", "IN_CREATOR_REVISION", "IN_HUMAN_REVIEW", "CHANGES_REQUESTED", "APPROVED")),
            ("guideline_category_enum", ("TONE", "TERMINOLOGY", "MESSAGING", "ACCESSIBILITY")),
            ("finding_category_enum", ("TONE", "TERMINOLOGY", "MESSAGING", "ACCESSIBILITY", "UNSUBSTANTIATED_CLAIM", "STALE_FACT", "REGULATORY_VIOLATION")),
            ("severity_level_enum", ("CRITICAL", "HIGH", "MEDIUM", "LOW")),
            ("triage_status_enum", ("FLAGGED_HIGH_CONFIDENCE", "ROUTED_TO_HUMAN_LOW_CONFIDENCE", "STALE_FACT_REVERIFY", "NEEDS_VERIFICATION_MISSING_EVIDENCE", "CLEARED_COMPLIANT")),
            ("detector_source_enum", ("DETERMINISTIC_RULE_ENGINE", "TEMPORAL_FACT_RAG", "PRIVACY_GATE_LLM", "MANUAL_REVIEWER")),
            ("creator_action_enum", ("PENDING", "ACCEPTED", "REJECTED", "EDITED")),
            ("review_signoff_enum", ("APPROVED", "CHANGES_REQUESTED")),
            ("audit_action_enum", (
                "USER_LOGGED_IN", "DOCUMENT_SUBMITTED", "ANALYSIS_PIPELINE_STARTED",
                "ANALYSIS_PIPELINE_COMPLETED", "FINDINGS_TRIAGED", "CREATOR_FEEDBACK_APPLIED",
                "HUMAN_REVIEW_DECIDED", "SUBMISSION_APPROVED", "BRAND_PROFILE_CREATED",
                "BRAND_PROFILE_UPDATED", "BRAND_PROFILE_DELETED", "BRAND_GUIDELINE_CREATED",
                "BRAND_GUIDELINE_UPDATED", "BRAND_GUIDELINE_DELETED", "APPROVED_FACT_CREATED",
                "APPROVED_FACT_UPDATED", "APPROVED_FACT_DELETED", "RETENTION_POLICY_PURGED",
                "RBAC_ACCESS_DENIED"
            )),
        ]:
            val_str = ", ".join(f"'{v}'" for v in values)
            op.execute(f"""
            DO $$ BEGIN
                CREATE TYPE {type_name} AS ENUM ({val_str});
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """)

    # 1. workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("api_key_hash", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"])
    op.create_index("ix_workspaces_api_key_hash", "workspaces", ["api_key_hash"])

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("CREATOR", "REVIEWER", "ADMINISTRATOR", name="user_role_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "email", name="uq_users_workspace_email"),
    )
    op.create_index("ix_users_workspace_id", "users", ["workspace_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_workspace_role", "users", ["workspace_id", "role"])

    # 3. brand_profiles
    op.create_table(
        "brand_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tone_parameters", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("banned_terminology_map", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("preferred_terminology_map", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("messaging_rules", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("privacy_gate_config", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "name", name="uq_brand_profile_workspace_name"),
    )
    op.create_index("ix_brand_profiles_workspace_id", "brand_profiles", ["workspace_id"])

    # 4. brand_guidelines
    op.create_table(
        "brand_guidelines",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_identifier", sa.String(64), nullable=False),
        sa.Column("clause_text", sa.Text(), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM("TONE", "TERMINOLOGY", "MESSAGING", "ACCESSIBILITY", name="guideline_category_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column(
            "severity",
            postgresql.ENUM("CRITICAL", "HIGH", "MEDIUM", "LOW", name="severity_level_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column("embedding", postgresql.JSONB() if not is_postgres else sa.dialects.postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("search_vector", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("brand_profile_id", "clause_identifier", name="uq_guidelines_profile_clause"),
    )
    op.create_index("ix_brand_guidelines_brand_profile_id", "brand_guidelines", ["brand_profile_id"])
    op.create_index("ix_brand_guidelines_category", "brand_guidelines", ["category"])
    op.create_index("ix_brand_guidelines_severity", "brand_guidelines", ["severity"])

    # 5. approved_facts
    op.create_table(
        "approved_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("fact_statement", sa.Text(), nullable=False),
        sa.Column("original_source_url", sa.String(2048), nullable=False),
        sa.Column("evidence_excerpt", sa.Text(), nullable=False),
        sa.Column("verification_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responsible_owner_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("embedding", postgresql.JSONB() if not is_postgres else sa.dialects.postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("search_vector", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approved_facts_workspace_id", "approved_facts", ["workspace_id"])
    op.create_index("ix_approved_facts_expiry_date", "approved_facts", ["expiry_date"])

    # 6. approved_brand_assets
    op.create_table(
        "approved_brand_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_name", sa.String(255), nullable=False),
        sa.Column("asset_category", sa.String(64), nullable=False),
        sa.Column("phash", sa.String(64), nullable=False),
        sa.Column("color_palette", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("aspect_ratio", sa.Float(), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approved_brand_assets_workspace_id", "approved_brand_assets", ["workspace_id"])
    op.create_index("ix_approved_brand_assets_phash", "approved_brand_assets", ["phash"])

    # 7. submissions
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_reviewer_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("document_type", sa.String(32), nullable=False),
        sa.Column(
            "workflow_state",
            postgresql.ENUM(
                "SUBMITTED", "ANALYZING", "TRIAGED", "IN_CREATOR_REVISION", "IN_HUMAN_REVIEW", "CHANGES_REQUESTED", "APPROVED",
                name="workflow_state_enum", create_type=False
            ) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_submissions_workspace_id", "submissions", ["workspace_id"])
    op.create_index("ix_submissions_workflow_state", "submissions", ["workflow_state"])

    # 8. document_revisions
    op.create_table(
        "document_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("document_revisions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("ast_span_map", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sha256_content_hash", sa.String(64), nullable=False),
        sa.Column("diff_summary", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "revision_number", name="uq_submission_revision_number"),
    )
    op.create_index("ix_document_revisions_submission_id", "document_revisions", ["submission_id"])
    op.create_index("ix_document_revisions_sha256_content_hash", "document_revisions", ["sha256_content_hash"])

    # Add foreign key from submissions.current_revision_id to document_revisions.id
    if is_postgres:
        op.create_foreign_key(
            "fk_submissions_current_revision",
            "submissions",
            "document_revisions",
            ["current_revision_id"],
            ["id"],
            ondelete="SET NULL",
            use_alter=True,
        )

    # 9. findings
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("matched_text", sa.Text(), nullable=False),
        sa.Column(
            "issue_category",
            postgresql.ENUM("TONE", "TERMINOLOGY", "MESSAGING", "ACCESSIBILITY", "UNSUBSTANTIATED_CLAIM", "STALE_FACT", "REGULATORY_VIOLATION", name="finding_category_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column(
            "severity",
            postgresql.ENUM("CRITICAL", "HIGH", "MEDIUM", "LOW", name="severity_level_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column(
            "detector_source",
            postgresql.ENUM("DETERMINISTIC_RULE_ENGINE", "TEMPORAL_FACT_RAG", "PRIVACY_GATE_LLM", "MANUAL_REVIEWER", name="detector_source_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column(
            "triage_status",
            postgresql.ENUM("FLAGGED_HIGH_CONFIDENCE", "ROUTED_TO_HUMAN_LOW_CONFIDENCE", "STALE_FACT_REVERIFY", "NEEDS_VERIFICATION_MISSING_EVIDENCE", "CLEARED_COMPLIANT", name="triage_status_enum", create_type=False) if is_postgres else sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "creator_action",
            postgresql.ENUM("PENDING", "ACCEPTED", "REJECTED", "EDITED", name="creator_action_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("author_notes", sa.Text(), nullable=True),
        sa.Column("linked_guideline_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("brand_guidelines.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_fact_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("approved_facts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_revision_id", "findings", ["revision_id"])
    op.create_index("ix_findings_triage_status", "findings", ["triage_status"])
    op.create_index("ix_findings_issue_category", "findings", ["issue_category"])
    op.create_index("ix_findings_severity", "findings", ["severity"])

    # 10. review_decisions
    op.create_table(
        "review_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "decision",
            postgresql.ENUM("APPROVED", "CHANGES_REQUESTED", name="review_signoff_enum", create_type=False) if is_postgres else sa.String(32),
            nullable=False,
        ),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.Column("stipulations", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_decisions_submission_id", "review_decisions", ["submission_id"])
    op.create_index("ix_review_decisions_revision_id", "review_decisions", ["revision_id"])

    # 11. audit_ledger
    op.create_table(
        "audit_ledger",
        sa.Column("sequence_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "action",
            postgresql.ENUM(
                "USER_LOGGED_IN", "DOCUMENT_SUBMITTED", "ANALYSIS_PIPELINE_STARTED",
                "ANALYSIS_PIPELINE_COMPLETED", "FINDINGS_TRIAGED", "CREATOR_FEEDBACK_APPLIED",
                "HUMAN_REVIEW_DECIDED", "SUBMISSION_APPROVED", "BRAND_PROFILE_CREATED",
                "BRAND_PROFILE_UPDATED", "BRAND_PROFILE_DELETED", "BRAND_GUIDELINE_CREATED",
                "BRAND_GUIDELINE_UPDATED", "BRAND_GUIDELINE_DELETED", "APPROVED_FACT_CREATED",
                "APPROVED_FACT_UPDATED", "APPROVED_FACT_DELETED", "RETENTION_POLICY_PURGED",
                "RBAC_ACCESS_DENIED",
                name="audit_action_enum", create_type=False
            ) if is_postgres else sa.String(64),
            nullable=False,
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=True),
        sa.Column("payload", postgresql.JSONB() if is_postgres else sa.JSON(), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("current_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_audit_ledger_workspace_id", "audit_ledger", ["workspace_id"])
    op.create_index("ix_audit_ledger_timestamp", "audit_ledger", ["timestamp"])
    op.create_index("ix_audit_ledger_action", "audit_ledger", ["action"])

    # 12. retention_policy_logs
    op.create_table(
        "retention_policy_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=False),
        sa.Column("brand_profile_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.CHAR(36), nullable=True),
        sa.Column("submissions_evaluated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("revisions_purged", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_retention_policy_logs_workspace_id", "retention_policy_logs", ["workspace_id"])


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Drop tables in reverse dependency order
    op.drop_table("retention_policy_logs")
    op.drop_table("audit_ledger")
    op.drop_table("review_decisions")
    op.drop_table("findings")
    if is_postgres:
        op.drop_constraint("fk_submissions_current_revision", "submissions", type_="foreignkey")
    op.drop_table("document_revisions")
    op.drop_table("submissions")
    op.drop_table("approved_brand_assets")
    op.drop_table("approved_facts")
    op.drop_table("brand_guidelines")
    op.drop_table("brand_profiles")
    op.drop_table("users")
    op.drop_table("workspaces")

    # Drop Postgres native ENUM types
    if is_postgres:
        for type_name in [
            "audit_action_enum", "review_signoff_enum", "creator_action_enum",
            "detector_source_enum", "triage_status_enum", "severity_level_enum",
            "finding_category_enum", "guideline_category_enum", "workflow_state_enum",
            "user_role_enum"
        ]:
            op.execute(f"DROP TYPE IF EXISTS {type_name};")
