"""
BrandShield AI - API v1 Master Router.
Aggregates enterprise authentication, brand administration, facts, findings, audit,
document ingestion, intelligence analysis, governance, and workflow sub-routers.
All handlers are consolidated into canonical routers under app/api/v1/routers/.
"""

from fastapi import APIRouter

from app.api.v1.routers import (
    analysis,
    attestation,
    audit,
    auth,
    brands,
    facts,
    findings,
    governance,
    submissions,
    system,
    webhooks,
    workflow,
)

api_router = APIRouter()

# 1. Core Infrastructure, Probes & Diagnostics
api_router.include_router(system.router, tags=["Health & Probes"])
api_router.include_router(system.router, prefix="/system", tags=["System Diagnostics & Introspection"])

# 2. Security & Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Session"])

# 3. Enterprise Administration & Brand Governance
api_router.include_router(brands.router, prefix="/brands", tags=["Enterprise Brands Administration"])
api_router.include_router(brands.router, prefix="/brand-profiles", tags=["Brand Profiles & Governance"])

# 4. Approved Facts & Staleness Engine
api_router.include_router(facts.router, prefix="/facts", tags=["Approved Facts & Staleness Engine"])

# 5. Findings & Triage Actions
api_router.include_router(findings.router, prefix="/findings", tags=["Findings & Triage"])

# 6. Workflow, Revision Engine & Human Review
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow Lifecycle"])
api_router.include_router(workflow.router, prefix="/submissions", tags=["Workflow, Revision Engine & Human Review"])

# 7. Document Ingestion, Revision DAG & Review Decisions
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions, Ingestion & Revision DAG"])

# 8. Intelligence Analysis Pipeline & Confidence Triage
api_router.include_router(analysis.router, prefix="/analysis", tags=["Intelligence Analysis & Triage"])

# 9. Cryptographic Governance & Audit Verification
api_router.include_router(governance.router, prefix="/governance", tags=["Cryptographic Governance & Audit Verification"])
api_router.include_router(audit.router, prefix="/audit", tags=["Cryptographic Audit Ledger"])

# 10. Transactional Outbox Webhooks & Dead-Letter Queue
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Transactional Outbox & Webhooks"])

# 11. Cryptographic Publication Attestation & Clearance Authority
api_router.include_router(attestation.router, tags=["Publication Attestation & Cryptographic Passports"])
api_router.include_router(attestation.router, prefix="/attestation", tags=["Publication Attestation & Cryptographic Passports"])

