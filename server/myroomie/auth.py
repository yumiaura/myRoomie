"""Lightweight token auth: pbkdf2 password hashing + opaque bearer tokens.

This is hobby-grade auth — no token expiry, no rate limiting — enough to scope
roomies to an account and gate the API, not a production identity stack. It
uses only the standard library, so the server keeps its tiny dependency set.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 200_000


def pbkdf2(password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return derived.hex()


def hash_password(password: str) -> tuple[str, str]:
    """Return (salt, hash) for a fresh password."""
    salt = secrets.token_hex(16)
    return salt, pbkdf2(password, salt)


def verify_password(password: str, salt: str, expected: str) -> bool:
    return hmac.compare_digest(pbkdf2(password, salt), expected)


def generate_token() -> str:
    return secrets.token_urlsafe(32)
