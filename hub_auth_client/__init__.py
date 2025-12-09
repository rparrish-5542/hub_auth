"""
Hub Auth Client - MSAL JWT validation library with Entra ID RBAC support.

This package provides standalone JWT token validation for Microsoft Entra ID (Azure AD)
tokens with support for scope-based RBAC.
"""

__version__ = "1.0.34"
__author__ = "Your Organization"

from .validator import MSALTokenValidator
from .exceptions import (
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientScopesError,
)

__all__ = [
    "MSALTokenValidator",
    "TokenValidationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientScopesError",
]
