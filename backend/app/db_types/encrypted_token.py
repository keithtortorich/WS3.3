"""SQLAlchemy TypeDecorator that transparently encrypts/decrypts string values.

Why a decorator instead of service-layer plumbing:
- Minimizes changes across routers/services/routers.
- Keeps encryption logic in one place: the ORM boundary.
- Works with repository methods unchanged.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.sql.type_api import TypeDecorator

from app.core.token_encryption import TokenEncryptionError, get_token_encryption

logger = logging.getLogger(__name__)


class EncryptedOAuthTokenType(TypeDecorator[str]):
    """Store OAuth token strings encrypted at rest using Fernet."""

    impl = Text
    cache_ok = False

    def process_bind_param(self, value: Optional[str], dialect: object) -> Optional[str]:  # noqa: A003
        if value is None or value == "":
            return value
        try:
            return get_token_encryption().encrypt(value)
        except TokenEncryptionError as exc:
            raise ValueError(str(exc)) from exc

    def process_result_value(self, value: Optional[str], dialect: object) -> Optional[str]:  # noqa: A003
        if value is None or value == "":
            return value
        try:
            return get_token_encryption().decrypt(value)
        except TokenEncryptionError as exc:
            raise ValueError(str(exc)) from exc
        except InvalidToken:
            # Log but return raw value to avoid breaking reads during rollback/
            # re-encryption transitions or bootstrap config gaps.
            logger.warning("OAuth token decryption failed; returning raw value")
            return value
