"""
BrandShield AI - Protected At-Rest Storage & Transparent Envelope Encryption.
Fulfills Enterprise Privacy & Responsible AI guarantees by encrypting
sensitive brand assets, documents, and tokens at rest with authenticated
symmetric AES-128-CBC / HMAC-SHA256 (Fernet / MultiFernet) with active key rotation.
"""

import base64
import hashlib
import hmac
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import get_settings

logger = logging.getLogger("brandshield.core.crypto_storage")

ENCRYPTION_PREFIX = "enc:fernet:"
ENCRYPTION_PREFIX_BYTES = b"enc:fernet:"


class CryptoStorageEngine:
    """
    Symmetric authenticated encryption engine for protecting customer confidential content at rest.
    Derives deterministic, cryptographically secure 32-byte Fernet keys from application secrets
    and supports zero-downtime key rotation via MultiFernet ring.
    """
    _multi_fernet: Optional[MultiFernet] = None
    _active_primary_key_id: Optional[str] = None

    @classmethod
    def _derive_fernet_key(cls, secret_str: str) -> bytes:
        """Derives a urlsafe base64 32-byte key from arbitrary secret string via SHA-256."""
        digest = hashlib.sha256(secret_str.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    @classmethod
    def get_fernet_ring(cls) -> MultiFernet:
        """
        Initializes or retrieves the MultiFernet key ring supporting the active primary key
        and historical rotated fallback keys for seamless decrypt & key rotation.
        """
        if cls._multi_fernet is None:
            settings = get_settings()
            primary_secret = getattr(settings, "STORAGE_ENCRYPTION_KEY", None) or settings.SECRET_KEY
            fallback_secrets_raw = getattr(settings, "STORAGE_KEY_ROTATION_FALLBACKS", "")

            keys = [Fernet(cls._derive_fernet_key(primary_secret))]

            if fallback_secrets_raw:
                if isinstance(fallback_secrets_raw, str):
                    fallbacks = [fb.strip() for fb in fallback_secrets_raw.split(",") if fb.strip()]
                elif isinstance(fallback_secrets_raw, (list, tuple)):
                    fallbacks = [str(fb).strip() for fb in fallback_secrets_raw if str(fb).strip()]
                else:
                    fallbacks = []

                for fb_secret in fallbacks:
                    keys.append(Fernet(cls._derive_fernet_key(fb_secret)))

            cls._multi_fernet = MultiFernet(keys)
        return cls._multi_fernet

    @classmethod
    def is_encrypted(cls, text: Optional[str]) -> bool:
        """
        Determines if the payload is encrypted under BrandShield envelope
        using constant-time prefix comparison.
        """
        if not text:
            return False
        if len(text) < len(ENCRYPTION_PREFIX):
            return False
        prefix = text[:len(ENCRYPTION_PREFIX)]
        return hmac.compare_digest(prefix, ENCRYPTION_PREFIX)

    @classmethod
    def encrypt_content(cls, plain_text: str) -> str:
        """
        Encrypts plaintext string returning ciphertext prefixed with 'enc:fernet:'.
        Idempotent: if already encrypted, returns as-is.
        """
        if not plain_text or cls.is_encrypted(plain_text):
            return plain_text

        ring = cls.get_fernet_ring()
        token = ring.encrypt(plain_text.encode("utf-8")).decode("utf-8")
        return f"{ENCRYPTION_PREFIX}{token}"

    @classmethod
    def decrypt_content(cls, cipher_text: str) -> str:
        """
        Decrypts ciphertext if prefixed with 'enc:fernet:'.
        If plaintext, transparently returns original string.
        """
        if not cipher_text or not cls.is_encrypted(cipher_text):
            return cipher_text

        raw_token = cipher_text[len(ENCRYPTION_PREFIX):]
        ring = cls.get_fernet_ring()
        try:
            return ring.decrypt(raw_token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            logger.error("Failed to decrypt envelope token: invalid key or corrupted payload: %s", exc)
            raise ValueError("Corrupted encrypted payload: could not decrypt with active key ring.") from exc

    @classmethod
    def rotate_content(cls, cipher_text: str) -> str:
        """
        Re-encrypts ciphertext under the newest primary key if it was encrypted
        under an older key in the rotation ring.
        """
        if not cipher_text or not cls.is_encrypted(cipher_text):
            return cipher_text

        raw_token = cipher_text[len(ENCRYPTION_PREFIX):]
        ring = cls.get_fernet_ring()
        try:
            rotated_token = ring.rotate(raw_token.encode("utf-8")).decode("utf-8")
            return f"{ENCRYPTION_PREFIX}{rotated_token}"
        except InvalidToken as exc:
            logger.error("Failed to rotate key on payload: %s", exc)
            raise ValueError("Could not rotate encryption key for payload.") from exc

    @classmethod
    def encrypt_bytes(cls, plain_bytes: bytes) -> bytes:
        """
        Encrypts raw binary asset (e.g. brand logos, vector graphics, proprietary media)
        with authenticated symmetric envelope encryption.
        """
        if not plain_bytes:
            return plain_bytes
        if plain_bytes.startswith(ENCRYPTION_PREFIX_BYTES):
            return plain_bytes

        ring = cls.get_fernet_ring()
        encrypted = ring.encrypt(plain_bytes)
        return ENCRYPTION_PREFIX_BYTES + encrypted

    @classmethod
    def decrypt_bytes(cls, cipher_bytes: bytes) -> bytes:
        """
        Decrypts raw binary asset if encrypted, or returns original bytes if unencrypted.
        """
        if not cipher_bytes or not cipher_bytes.startswith(ENCRYPTION_PREFIX_BYTES):
            return cipher_bytes

        raw_token = cipher_bytes[len(ENCRYPTION_PREFIX_BYTES):]
        ring = cls.get_fernet_ring()
        try:
            return ring.decrypt(raw_token)
        except InvalidToken as exc:
            logger.error("Failed to decrypt binary asset token: %s", exc)
            raise ValueError("Corrupted encrypted asset: could not decrypt with active key ring.") from exc

    @classmethod
    def should_protect(cls, brand_profile: Any) -> bool:
        """Evaluates whether at-rest protected encryption is required for the brand profile."""
        if not brand_profile:
            return False
        config = getattr(brand_profile, "privacy_gate_config", {})
        if isinstance(config, dict):
            return bool(config.get("protected_storage_enabled", False))
        return False
