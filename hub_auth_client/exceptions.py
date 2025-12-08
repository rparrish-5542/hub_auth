"""Custom exceptions for hub_auth_client."""


class TokenValidationError(Exception):
    """Base exception for token validation errors."""
    pass


class TokenExpiredError(TokenValidationError):
    """Exception raised when token has expired."""
    pass


class InvalidTokenError(TokenValidationError):
    """Exception raised when token is invalid."""
    pass


class InsufficientScopesError(TokenValidationError):
    """Exception raised when token doesn't have required scopes."""
    pass


class InvalidAudienceError(TokenValidationError):
    """Exception raised when token audience doesn't match."""
    pass


class InvalidIssuerError(TokenValidationError):
    """Exception raised when token issuer is invalid."""
    pass


class MissingClaimError(TokenValidationError):
    """Exception raised when required claim is missing from token."""
    pass
