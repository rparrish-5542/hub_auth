# hub_auth_client/utils/jwt_helpers.py
"""
JWT helper functions for token processing.
"""
import jwt
from typing import Dict, Any


def strip_bearer(token: str) -> str:
    """Remove 'Bearer ' prefix from token if present."""
    return token[7:] if token.startswith("Bearer ") else token


def decode_unverified(token: str) -> Dict[str, Any]:
    """Decode JWT without verifying signature."""
    return jwt.decode(token, options={"verify_signature": False})


def get_kid(token: str) -> str:
    """Extract 'kid' from JWT header."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise ValueError("Token missing 'kid' in header")
    return kid
