from typing import Dict, Any, List, Optional


def extract_scopes(decoded_token: Dict[str, Any]) -> List[str]:
    """Extract scopes from the token."""
    scopes = []
    if decoded_token.get("scp"):
        scopes.extend(decoded_token["scp"].split())
    if decoded_token.get("scopes"):
        scopes.extend(decoded_token["scopes"])
    return scopes


def extract_roles(decoded_token: Dict[str, Any]) -> List[str]:
    """Extract roles from the token."""
    return decoded_token.get("roles", [])


def validate_scopes(
    decoded_token: Dict[str, Any],
    required_scopes: List[str],
    require_all: bool,
) -> Optional[str]:
    """Validate that the token contains the required scopes."""
    token_scopes = extract_scopes(decoded_token)

    if not token_scopes:
        return f"Token has no scopes. Required: {required_scopes}"

    if require_all:
        missing = set(required_scopes) - set(token_scopes)
        if missing:
            return f"Missing required scopes: {missing}. Token has: {token_scopes}"
    else:
        if not any(scope in token_scopes for scope in required_scopes):
            return f"Token missing any of required scopes: {required_scopes}. Token has: {token_scopes}"

    return None


def validate_roles(
    decoded_token: Dict[str, Any],
    required_roles: List[str],
    require_all: bool,
) -> Optional[str]:
    """Validate that the token contains the required roles."""
    token_roles = extract_roles(decoded_token)

    if not token_roles:
        return f"Token has no roles. Required: {required_roles}"

    if require_all:
        missing = set(required_roles) - set(token_roles)
        if missing:
            return f"Missing required roles: {missing}. Token has: {token_roles}"
    else:
        if not any(role in token_roles for role in required_roles):
            return f"Token missing any of required roles: {required_roles}. Token has: {token_roles}"

    return None
