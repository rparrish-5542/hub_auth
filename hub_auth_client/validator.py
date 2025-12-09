"""
MSAL JWT Token Validator with Entra ID Scope-based RBAC support.

This module provides comprehensive JWT token validation for Microsoft Entra ID (Azure AD)
with support for:
- Token signature verification using Azure AD public keys
- Standard JWT claim validation (exp, nbf, iat, aud, iss)
- Scope-based RBAC validation
- Role-based access control
- Custom claim validation
"""

import logging
import time
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timezone
import jwt
from jwt import PyJWKClient

from .exceptions import (
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientScopesError,
    InvalidAudienceError,
    InvalidIssuerError,
    MissingClaimError,
)

logger = logging.getLogger(__name__)


class MSALTokenValidator:
    """
    Validates JWT tokens issued by Microsoft Entra ID (Azure AD).
    
    Supports both v1.0 and v2.0 tokens with comprehensive validation including:
    - Cryptographic signature verification
    - Standard JWT claims (exp, iat, nbf, aud, iss)
    - Tenant validation
    - Scope-based RBAC
    - Role-based RBAC
    - Custom claim validation
    
    Example:
        >>> validator = MSALTokenValidator(
        ...     tenant_id="your-tenant-id",
        ...     client_id="your-client-id"
        ... )
        >>> is_valid, claims, error = validator.validate_token(token)
        >>> if is_valid:
        ...     print(f"User: {claims['upn']}")
        ...     print(f"Scopes: {claims.get('scp', '').split()}")
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        validate_audience: bool = True,
        validate_issuer: bool = True,
        leeway: int = 0,
        cache_jwks: bool = True,
        max_cached_keys: int = 16,
    ):
        """
        Initialize the MSAL token validator.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID registered in Azure AD
            validate_audience: Whether to validate the audience claim (default: True)
            validate_issuer: Whether to validate the issuer claim (default: True)
            leeway: Leeway in seconds for time-based claims (default: 0)
            cache_jwks: Whether to cache JWKS keys (default: True)
            max_cached_keys: Maximum number of keys to cache (default: 16)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.validate_audience = validate_audience
        self.validate_issuer = validate_issuer
        self.leeway = leeway
        
        # Support both v1.0 and v2.0 endpoints
        self.issuer_v1 = f"https://sts.windows.net/{tenant_id}/"
        self.issuer_v2 = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        self.jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        
        # Initialize JWK client for fetching public keys
        self.jwks_client = PyJWKClient(
            self.jwks_uri,
            cache_keys=cache_jwks,
            max_cached_keys=max_cached_keys
        )
    
    def validate_token(
        self,
        token: str,
        required_scopes: Optional[List[str]] = None,
        required_roles: Optional[List[str]] = None,
        require_all_scopes: bool = False,
        require_all_roles: bool = False,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a JWT token from MSAL/Entra ID.
        
        Args:
            token: The JWT token string (without 'Bearer ' prefix)
            required_scopes: List of required scopes (any or all based on require_all_scopes)
            required_roles: List of required roles (any or all based on require_all_roles)
            require_all_scopes: If True, token must have ALL required scopes (default: False = any)
            require_all_roles: If True, token must have ALL required roles (default: False = any)
        
        Returns:
            Tuple of (is_valid, decoded_token, error_message)
            
        Example:
            >>> is_valid, claims, error = validator.validate_token(
            ...     token,
            ...     required_scopes=["User.Read", "Files.ReadWrite"],
            ...     require_all_scopes=False  # User needs at least one scope
            ... )
        """
        start_time = time.time()
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            # Decode header to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                return False, None, "Token missing 'kid' in header"
            
            # Decode without verification to see claims for debugging
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"Token tenant_id: {unverified_claims.get('tid')}, expected: {self.tenant_id}")
            logger.debug(f"Token audience: {unverified_claims.get('aud')}, expected: {self.client_id}")
            logger.debug(f"Token issuer: {unverified_claims.get('iss')}, expected: {self.issuer_v1} or {self.issuer_v2}")
            
            # Get the signing key from Azure AD's JWKS endpoint
            signing_key = self.jwks_client.get_signing_key(kid)
            
            # Prepare validation options
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,  # We'll validate audience manually to support both formats
                "verify_iss": self.validate_issuer,
            }
            
            # Decode and validate the token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=None,  # We'll validate audience manually to support both formats
                issuer=None,  # We'll validate issuer manually to support both v1 and v2
                options=options,
                leeway=self.leeway,
            )
            
            # Validate audience manually (support both "client_id" and "api://client_id")
            if self.validate_audience:
                token_audience = decoded_token.get('aud')
                valid_audiences = [
                    self.client_id,
                    f"api://{self.client_id}",
                ]
                if token_audience not in valid_audiences:
                    return False, decoded_token, f"Invalid audience: {token_audience}. Expected: {self.client_id} or api://{self.client_id}"
            
            # Validate issuer manually (support both v1.0 and v2.0)
            if self.validate_issuer:
                issuer = decoded_token.get('iss')
                if issuer not in [self.issuer_v1, self.issuer_v2]:
                    return False, decoded_token, f"Invalid issuer: {issuer}"
            
            # Additional validations
            validation_error = self._validate_claims(
                decoded_token,
                required_scopes,
                required_roles,
                require_all_scopes,
                require_all_roles,
            )
            
            if validation_error:
                return False, decoded_token, validation_error
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Token validated successfully in {elapsed_ms}ms for user: "
                f"{decoded_token.get('upn') or decoded_token.get('unique_name') or decoded_token.get('oid')}"
            )
            
            return True, decoded_token, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidAudienceError as e:
            logger.error(f"Invalid audience error: {str(e)}")
            return False, None, f"Invalid audience: {str(e)}"
        except jwt.InvalidIssuerError as e:
            logger.error(f"Invalid issuer error: {str(e)}")
            return False, None, f"Invalid issuer: {str(e)}"
        except jwt.InvalidSignatureError as e:
            logger.error(f"Invalid signature error: {str(e)}. JWKS URI: {self.jwks_uri}")
            return False, None, "Invalid signature"
        except jwt.DecodeError as e:
            logger.error(f"Token decode error: {str(e)}")
            return False, None, f"Token decode error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}", exc_info=True)
            return False, None, f"Validation error: {str(e)}"
    
    def _validate_claims(
        self,
        decoded_token: Dict[str, Any],
        required_scopes: Optional[List[str]],
        required_roles: Optional[List[str]],
        require_all_scopes: bool,
        require_all_roles: bool,
    ) -> Optional[str]:
        """
        Perform additional claim validation.
        
        Args:
            decoded_token: The decoded JWT payload
            required_scopes: Required scopes
            required_roles: Required roles
            require_all_scopes: Whether all scopes are required
            require_all_roles: Whether all roles are required
        
        Returns:
            Error message if validation fails, None otherwise
        """
        # Verify tenant ID matches expected
        token_tenant = decoded_token.get('tid')
        if token_tenant != self.tenant_id:
            return f"Token from wrong tenant. Expected: {self.tenant_id}, Got: {token_tenant}"
        
        # Ensure token has required claims
        required_claims = ['oid', 'tid']  # Object ID and Tenant ID
        for claim in required_claims:
            if claim not in decoded_token:
                return f"Missing required claim: {claim}"
        
        # Validate scopes if required
        if required_scopes:
            error = self._validate_scopes(decoded_token, required_scopes, require_all_scopes)
            if error:
                return error
        
        # Validate roles if required
        if required_roles:
            error = self._validate_roles(decoded_token, required_roles, require_all_roles)
            if error:
                return error
        
        return None
    
    def _validate_scopes(
        self,
        decoded_token: Dict[str, Any],
        required_scopes: List[str],
        require_all: bool,
    ) -> Optional[str]:
        """
        Validate token has required scopes.
        
        Scopes can be in 'scp' claim (space-separated string) or 'scopes' claim (list).
        
        Args:
            decoded_token: Decoded token claims
            required_scopes: List of required scopes
            require_all: If True, all scopes must be present; if False, at least one
        
        Returns:
            Error message if validation fails, None otherwise
        """
        # Get scopes from token (can be 'scp' or 'scopes')
        token_scopes = []
        
        # Check 'scp' claim (space-separated string)
        scp = decoded_token.get('scp', '')
        if scp:
            token_scopes.extend(scp.split())
        
        # Check 'scopes' claim (list)
        scopes_list = decoded_token.get('scopes', [])
        if scopes_list:
            token_scopes.extend(scopes_list)
        
        if not token_scopes:
            return f"Token has no scopes. Required: {required_scopes}"
        
        # Validate scopes
        if require_all:
            missing_scopes = set(required_scopes) - set(token_scopes)
            if missing_scopes:
                return f"Missing required scopes: {missing_scopes}. Token has: {token_scopes}"
        else:
            # At least one scope must match
            has_scope = any(scope in token_scopes for scope in required_scopes)
            if not has_scope:
                return f"Token missing any of required scopes: {required_scopes}. Token has: {token_scopes}"
        
        return None
    
    def _validate_roles(
        self,
        decoded_token: Dict[str, Any],
        required_roles: List[str],
        require_all: bool,
    ) -> Optional[str]:
        """
        Validate token has required roles.
        
        Roles are in the 'roles' claim (list).
        
        Args:
            decoded_token: Decoded token claims
            required_roles: List of required roles
            require_all: If True, all roles must be present; if False, at least one
        
        Returns:
            Error message if validation fails, None otherwise
        """
        token_roles = decoded_token.get('roles', [])
        
        if not token_roles:
            return f"Token has no roles. Required: {required_roles}"
        
        # Validate roles
        if require_all:
            missing_roles = set(required_roles) - set(token_roles)
            if missing_roles:
                return f"Missing required roles: {missing_roles}. Token has: {token_roles}"
        else:
            # At least one role must match
            has_role = any(role in token_roles for role in required_roles)
            if not has_role:
                return f"Token missing any of required roles: {required_roles}. Token has: {token_roles}"
        
        return None
    
    def extract_user_info(self, decoded_token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from decoded token.
        
        Args:
            decoded_token: The decoded JWT payload
        
        Returns:
            Dictionary with user information
        """
        return {
            'object_id': decoded_token.get('oid'),
            'tenant_id': decoded_token.get('tid'),
            'user_principal_name': decoded_token.get('upn') or decoded_token.get('unique_name'),
            'email': decoded_token.get('email') or decoded_token.get('preferred_username'),
            'name': decoded_token.get('name'),
            'given_name': decoded_token.get('given_name'),
            'family_name': decoded_token.get('family_name'),
            'scopes': decoded_token.get('scp', '').split() if decoded_token.get('scp') else decoded_token.get('scopes', []),
            'roles': decoded_token.get('roles', []),
            'groups': decoded_token.get('groups', []),
            'app_id': decoded_token.get('appid'),
            'app_displayname': decoded_token.get('app_displayname'),
        }
    
    def get_token_expiry(self, decoded_token: Dict[str, Any]) -> Optional[datetime]:
        """
        Get token expiration datetime.
        
        Args:
            decoded_token: Decoded token claims
        
        Returns:
            Token expiration as datetime object, or None if not present
        """
        exp = decoded_token.get('exp')
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    
    def has_scope(self, decoded_token: Dict[str, Any], scope: str) -> bool:
        """
        Check if token has a specific scope.
        
        Args:
            decoded_token: Decoded token claims
            scope: Scope to check for
        
        Returns:
            True if token has the scope, False otherwise
        """
        scopes = decoded_token.get('scp', '').split() or decoded_token.get('scopes', [])
        return scope in scopes
    
    def has_role(self, decoded_token: Dict[str, Any], role: str) -> bool:
        """
        Check if token has a specific role.
        
        Args:
            decoded_token: Decoded token claims
            role: Role to check for
        
        Returns:
            True if token has the role, False otherwise
        """
        roles = decoded_token.get('roles', [])
        return role in roles
    
    def has_any_scope(self, decoded_token: Dict[str, Any], scopes: List[str]) -> bool:
        """
        Check if token has any of the specified scopes.
        
        Args:
            decoded_token: Decoded token claims
            scopes: List of scopes to check for
        
        Returns:
            True if token has at least one scope, False otherwise
        """
        token_scopes = decoded_token.get('scp', '').split() or decoded_token.get('scopes', [])
        return any(scope in token_scopes for scope in scopes)
    
    def has_all_scopes(self, decoded_token: Dict[str, Any], scopes: List[str]) -> bool:
        """
        Check if token has all of the specified scopes.
        
        Args:
            decoded_token: Decoded token claims
            scopes: List of scopes to check for
        
        Returns:
            True if token has all scopes, False otherwise
        """
        token_scopes = set(decoded_token.get('scp', '').split() or decoded_token.get('scopes', []))
        return set(scopes).issubset(token_scopes)
