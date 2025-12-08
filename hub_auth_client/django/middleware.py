"""
Django middleware for MSAL JWT token authentication.

Add to MIDDLEWARE in settings.py:
    MIDDLEWARE = [
        ...
        'hub_auth_client.django.middleware.MSALAuthenticationMiddleware',
    ]
"""

import logging
from typing import Optional
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from ..validator import MSALTokenValidator

logger = logging.getLogger(__name__)


class MSALAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to validate MSAL JWT tokens and attach user info to request.
    
    Configuration in settings.py:
        AZURE_AD_TENANT_ID = "your-tenant-id"
        AZURE_AD_CLIENT_ID = "your-client-id"
        
        # Optional settings
        MSAL_VALIDATE_AUDIENCE = True  # Default: True
        MSAL_VALIDATE_ISSUER = True    # Default: True
        MSAL_TOKEN_LEEWAY = 0          # Leeway in seconds for time-based claims
        MSAL_EXEMPT_PATHS = ['/health/', '/metrics/']  # Paths that don't require auth
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Initialize validator
        tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
        client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
        
        if not tenant_id or not client_id:
            raise ValueError(
                "AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID must be set in Django settings"
            )
        
        self.validator = MSALTokenValidator(
            tenant_id=tenant_id,
            client_id=client_id,
            validate_audience=getattr(settings, 'MSAL_VALIDATE_AUDIENCE', True),
            validate_issuer=getattr(settings, 'MSAL_VALIDATE_ISSUER', True),
            leeway=getattr(settings, 'MSAL_TOKEN_LEEWAY', 0),
        )
        
        # Get exempt paths
        self.exempt_paths = getattr(settings, 'MSAL_EXEMPT_PATHS', [])
    
    def process_request(self, request):
        """Process the request and validate token."""
        # Check if path is exempt
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return None
        
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            # Allow requests without auth header to proceed (handled by DRF permissions)
            request.msal_token = None
            request.msal_user = None
            return None
        
        # Validate token
        is_valid, claims, error = self.validator.validate_token(auth_header)
        
        if not is_valid:
            return JsonResponse(
                {'error': 'Invalid token', 'message': error},
                status=401
            )
        
        # Attach claims and user info to request
        request.msal_token = claims
        request.msal_user = self.validator.extract_user_info(claims)
        
        return None
