"""
Minting service-to-service app tokens.

The counterpart of AppTokenValidator. In the service-to-service model each
service owns its own secret, mints tokens for its callers with it, and checks
incoming tokens with AppTokenValidator(secret=<own secret>, audience=<own aud>).
Callers store the token they were given, never the secret.

    token = mint_app_token(settings.APP_JWT_SECRET, sub="checkin_service",
                           aud="teams_connector", expires_in_seconds=365 * 86400)

Django services: ``python manage.py mint_app_token <sub>``.
Anything else: ``python -m hub_auth_client.mint <sub> --aud <aud>``.
"""

import time
import uuid
from typing import Optional

import jwt

ALGORITHM = "HS256"
# PyJWT warns below this; RFC 7518 3.2 asks for a key at least as long as the hash.
MIN_SECRET_BYTES = 32
DEFAULT_EXPIRES_IN_SECONDS = 365 * 24 * 3600


def mint_app_token(
    secret: str,
    *,
    sub: str,
    aud: str,
    expires_in_seconds: int = DEFAULT_EXPIRES_IN_SECONDS,
    issuer: Optional[str] = None,
) -> str:
    """Return an HS256 JWT that AppTokenValidator(secret, audience=aud) accepts.

    Args:
        secret: The minting service's own secret (its APP_JWT_SECRET).
        sub: Who the token is for: the calling service's name. The receiving
            service maps this to the caller.
        aud: Who the token is for use against: the minting service itself.
        expires_in_seconds: Lifetime. Must be positive; tokens always expire.
        issuer: ``iss`` claim. Defaults to ``aud`` (the minting service). Set it
            to whatever the receiver's APP_JWT_ISSUER is, if it checks one.

    Claims: sub, aud, iss, iat, exp, and a random jti for tracing in logs.
    """
    if not secret:
        raise ValueError("secret is required")
    if len(secret.encode()) < MIN_SECRET_BYTES:
        raise ValueError(f"secret must be at least {MIN_SECRET_BYTES} bytes")
    if not sub or not aud:
        raise ValueError("sub and aud are required")
    if expires_in_seconds <= 0:
        raise ValueError("expires_in_seconds must be positive")

    now = int(time.time())
    claims = {
        "sub": sub,
        "aud": aud,
        "iss": issuer or aud,
        "iat": now,
        "exp": now + int(expires_in_seconds),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, secret, algorithm=ALGORITHM)
