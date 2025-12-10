"""
DRF authentication backend for MSAL JWT tokens.

Usage in settings.py:
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'hub_auth_client.django.authentication.MSALAuthentication',
        ],
    }
"""

import logging
from typing import Optional, Tuple
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from ..validator import MSALTokenValidator, AppTokenValidator

logger = logging.getLogger(__name__)


class MSALUser:
    """
    Lightweight user object for MSAL-authenticated requests.
    
    This is used when you don't want to sync users to the database,
    but still need user info from the token.
    """
    
    def __init__(self, claims: dict):
        self.claims = claims
        self.object_id = claims.get('oid')
        self.username = claims.get('upn') or claims.get('unique_name') or claims.get('oid')
        self.email = claims.get('email') or claims.get('preferred_username')
        self.name = claims.get('name')
        self.scopes = claims.get('scp', '').split() if claims.get('scp') else claims.get('scopes', [])
        self.roles = claims.get('roles', [])
        self.groups = claims.get('groups', [])
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def __str__(self):
        return self.username or self.object_id
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope."""
        return scope in self.scopes
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_scope(self, scopes: list) -> bool:
        """Check if user has any of the specified scopes."""
        return any(scope in self.scopes for scope in scopes)
    
    def has_all_scopes(self, scopes: list) -> bool:
        """Check if user has all of the specified scopes."""
        return all(scope in self.scopes for scope in scopes)


class MSALAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication backend that validates MSAL JWT tokens.
    
    Returns an MSALUser object with claims from the token.
    
    Configuration in settings.py:
        AZURE_AD_TENANT_ID = "your-tenant-id"
        AZURE_AD_CLIENT_ID = "your-client-id"
    """
    
    def __init__(self):
        super().__init__()
        
        # Try to get config from database first
        try:
            from .config_models import AzureADConfiguration
            db_config = AzureADConfiguration.get_active_config()
            
            if db_config:
                logger.info(f"Using Azure AD configuration '{db_config.name}' from database")
                self.validator = db_config.create_validator()
                self.exempt_paths = db_config.get_exempt_paths()
                self.app_validator = self._build_app_validator()
                return
        except Exception as e:
            logger.debug(f"Could not load config from database: {e}")
        
        # Fallback to settings.py configuration
        tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
        client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
        
        if not tenant_id or not client_id:
            raise ValueError(
                "Either configure Azure AD via Django admin (AzureADConfiguration model) "
                "or set AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID in Django settings"
            )
        
        logger.info("Using Azure AD configuration from settings.py")
        self.validator = MSALTokenValidator(
            tenant_id=tenant_id,
            client_id=client_id,
            validate_audience=getattr(settings, 'MSAL_VALIDATE_AUDIENCE', True),
            validate_issuer=getattr(settings, 'MSAL_VALIDATE_ISSUER', True),
            leeway=getattr(settings, 'MSAL_TOKEN_LEEWAY', 0),
        )
        self.exempt_paths = getattr(settings, 'MSAL_EXEMPT_PATHS', [])

        self.app_validator = self._build_app_validator()

    def _build_app_validator(self) -> Optional[AppTokenValidator]:
        if not getattr(settings, 'APP_JWT_ENABLED', False):
            return None

        secret = getattr(settings, 'APP_JWT_SECRET', None)
        if not secret:
            logger.warning("APP_JWT_ENABLED is True but APP_JWT_SECRET is not set; disabling app token auth")
            return None

        algorithms = getattr(settings, 'APP_JWT_ALGORITHMS', ['HS256'])

        return AppTokenValidator(
            secret=secret,
            issuer=getattr(settings, 'APP_JWT_ISSUER', None),
            audience=getattr(settings, 'APP_JWT_AUDIENCE', None),
            algorithms=algorithms,
            leeway=getattr(settings, 'APP_JWT_LEEWAY', 0),
            require_exp=getattr(settings, 'APP_JWT_REQUIRE_EXP', True),
        )
    
    def authenticate(self, request) -> Optional[Tuple[MSALUser, dict]]:
        """
        Authenticate the request and return (user, auth) tuple.
        
        Args:
            request: Django request object
        
        Returns:
            Tuple of (MSALUser, token_claims) if authenticated, None otherwise
        
        Raises:
            AuthenticationFailed: If token is invalid
        """
        # Check if path is exempt from authentication
        if hasattr(self, 'exempt_paths'):
            path = request.path
            for exempt_path in self.exempt_paths:
                if path.startswith(exempt_path):
                    logger.debug(f"Path {path} is exempt from authentication")
                    return None
        
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        # Validate token
        is_valid, claims, error = self.validator.validate_token(auth_header)
        used_app_token = False

        if not is_valid and self.app_validator:
            is_valid, claims, error = self.app_validator.validate_token(auth_header)
            used_app_token = is_valid
        
        if not is_valid:
            raise AuthenticationFailed(error or 'Invalid token')
        
        # Create user object from claims
        user = MSALUser(claims) if not used_app_token else MSALUser(claims)
        
        return (user, claims)
    
    def authenticate_header(self, request) -> str:
        """Return the authentication header to use in 401 responses."""
        return 'Bearer realm="api"'
