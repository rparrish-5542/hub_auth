"""
Hub Auth Client - MSAL JWT validation library with Entra ID RBAC support.

This package provides standalone JWT token validation for Microsoft Entra ID (Azure AD)
tokens with support for scope-based RBAC.
"""

__version__ = "1.0.37"
__author__ = "Ryan Parrish - Wedgwood Christian Services"

from .validator import MSALTokenValidator, AppTokenValidator
from .exceptions import (
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientScopesError,
)

__all__ = [
    "MSALTokenValidator",
    "AppTokenValidator",
    "TokenValidationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientScopesError",
]
