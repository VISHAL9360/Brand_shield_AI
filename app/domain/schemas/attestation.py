"""
BrandShield AI - Pydantic v2 Schemas for Publication Attestation Certificates & CMS Verification.
"""

from datetime import datetime
from typing import Any, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PublicationAttestationCertificateRead(BaseModel):
    """Immutable Cryptographic Clearance Certificate returned upon submission approval."""
    id: uuid.UUID
    certificate_id: Optional[uuid.UUID] = None
    submission_id: uuid.UUID
    approved_revision_id: uuid.UUID
    document_sha256_hash: str
    reviewer_id: uuid.UUID
    brand_profile_id: uuid.UUID
    merkle_root_of_cited_facts_and_guidelines: str
    issued_at: datetime
    valid_until: datetime
    cryptographic_signature: str
    status: str = "ACTIVE"
    metadata_json: Optional[dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def populate_certificate_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" in data and not data.get("certificate_id"):
                data["certificate_id"] = data["id"]
        elif hasattr(data, "id"):
            setattr(data, "certificate_id", getattr(data, "id", None))
        return data

    model_config = ConfigDict(from_attributes=True)


class AttestationVerifyRequest(BaseModel):
    """Payload for ultra-fast <1ms CMS Gatekeeper verification endpoint."""
    certificate_id: uuid.UUID = Field(..., description="UUID of the publication attestation certificate")
    document_text: Optional[str] = Field(default=None, description="Plaintext content to hash and verify against clearance")
    document_content: Optional[str] = Field(default=None, description="Alias for document_text")
    document_sha256_hash: Optional[str] = Field(default=None, description="Pre-computed SHA-256 digest of document content")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "document_content" in data and not data.get("document_text"):
                data["document_text"] = data["document_content"]
        return data


class AttestationVerifyResponse(BaseModel):
    """Ultra-fast verification response for external CMS gatekeepers."""
    is_valid_for_publish: bool
    is_valid: bool = True
    certificate_id: uuid.UUID
    submission_id: Optional[uuid.UUID] = None
    verification_status: str = Field(
        ...,
        description="One of: VALID, TAMPERED_HASH_MISMATCH, EXPIRED_FACT_REVOKED, SIGNATURE_INVALID, CERTIFICATE_NOT_FOUND"
    )
    verification_code: str = "VALID"
    reason: str
    valid_until: Optional[datetime] = None
    checked_at: datetime
    latency_ms: float
    merkle_root: Optional[str] = None
    cited_facts_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "is_valid_for_publish" in data:
                data["is_valid"] = data["is_valid_for_publish"]
            if "verification_status" in data:
                data["verification_code"] = data["verification_status"]
        return data

    model_config = ConfigDict(from_attributes=True)
