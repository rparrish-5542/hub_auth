"""Custom exceptions for hub_auth_client."""


class TokenValidationError(Exception):
    """Base exception for token validation errors."""


class TokenExpiredError(TokenValidationError):
    """Exception raised when token has expired."""


class InvalidTokenError(TokenValidationError):
    """Exception raised when token is invalid."""


class InsufficientScopesError(TokenValidationError):
    """Exception raised when token doesn't have required scopes."""


class InvalidAudienceError(TokenValidationError):
    """Exception raised when token audience doesn't match."""


class InvalidIssuerError(TokenValidationError):
    """Exception raised when token issuer is invalid."""


class MissingClaimError(TokenValidationError):
    """Exception raised when required claim is missing from token."""
