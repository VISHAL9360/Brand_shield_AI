"""
BrandShield AI - API v1 Canonical Routers Package.
Aggregates enterprise authentication, brand administration, facts, findings, audit,
document ingestion, intelligence analysis, governance, and workflow sub-routers.
"""

from app.api.v1.routers import (
    analysis,
    audit,
    auth,
    brands,
    facts,
    findings,
    governance,
    submissions,
    system,
    workflow,
)

__all__ = [
    "analysis",
    "audit",
    "auth",
    "brands",
    "facts",
    "findings",
    "governance",
    "submissions",
    "system",
    "workflow",
]
