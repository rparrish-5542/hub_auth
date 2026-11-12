"""
Hub Auth Client - MSAL JWT validation library with Entra ID RBAC support.

This package provides standalone JWT token validation for Microsoft Entra ID (Azure AD)
tokens with support for scope-based RBAC.
"""

__version__ = "1.0.37"
__author__ = "Ryan Parrish - Wedgwood Christian Services"

from .exceptions import (
    InsufficientScopesError,
    InvalidTokenError,
    TokenExpiredError,
    TokenValidationError,
)
from .minting import mint_app_token
from .validator import AppTokenValidator, MSALTokenValidator

__all__ = [
    "MSALTokenValidator",
    "AppTokenValidator",
    "mint_app_token",
    "TokenValidationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientScopesError",
]
