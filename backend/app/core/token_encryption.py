"""Column-level encryption for OAuth tokens.

Best practice: use a single application-level key for existing rows.
New row writes always use the encrypted path regardless of initial key source.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class TokenEncryptionError(Exception):
    """Raised when token encryption or decryption cannot proceed."""


class TokenEncryption:
    """Thin wrapper around Fernet for OAuth token columns."""

    def __init__(self, key: Optional[str] = None) -> None:
        raw = key or os.environ.get("OAUTH_TOKEN_ENCRYPTION_KEY", "")
        if not raw:
            raise TokenEncryptionError(
                "No token encryption key configured. Set OAUTH_TOKEN_ENCRYPTION_KEY."
            )
        try:
            self.fernet = Fernet(raw.encode("utf-8"))
        except Exception as exc:
            raise TokenEncryptionError(f"Invalid OAUTH token encryption key: {exc}") from exc

    def encrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            token = self.fernet.encrypt(value.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            raise TokenEncryptionError(f"Failed to encrypt token: {exc}") from exc

    def decrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            raw = self.fernet.decrypt(value.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken as exc:
            logger.warning("Failed to decrypt OAuth token; value may be plaintext or re-encrypted")
            return value
        except Exception as exc:
            raise TokenEncryptionError(f"Failed to decrypt token: {exc}") from exc


_encryption: Optional[TokenEncryption] = None


def get_token_encryption() -> TokenEncryption:
    """Return a process-level TokenEncryption instance configured from env."""
    global _encryption
    if _encryption is None:
        _encryption = TokenEncryption()
    return _encryption


def encrypt_token(value: Optional[str]) -> Optional[str]:
    return get_token_encryption().encrypt(value)


def decrypt_token(value: Optional[str]) -> Optional[str]:
    return get_token_encryption().decrypt(value)
