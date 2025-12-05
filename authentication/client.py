# hub_auth/authentication/client.py
"""
Reusable client library for services to validate tokens with hub_auth.

Usage in other Django projects:
    from hub_auth_client import HubAuthClient
    
    client = HubAuthClient(
        hub_auth_url='http://localhost:8000',
        api_key='your-service-api-key'
    )
    
    is_valid, user_data = client.validate_token(token)
"""
import logging
import requests
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class HubAuthClient:
    """Client for validating tokens with hub_auth service."""
    
    def __init__(self, hub_auth_url: str, api_key: str, service_name: str = 'unknown'):
        """
        Initialize hub_auth client.
        
        Args:
            hub_auth_url: Base URL of hub_auth service (e.g., 'http://localhost:8000')
            api_key: API key for your service
            service_name: Name of your service for logging
        """
        self.hub_auth_url = hub_auth_url.rstrip('/')
        self.api_key = api_key
        self.service_name = service_name
        self.validate_endpoint = f"{self.hub_auth_url}/api/auth/validate/"
        self.validate_simple_endpoint = f"{self.hub_auth_url}/api/auth/validate-simple/"
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token string (with or without 'Bearer ' prefix)
        
        Returns:
            Tuple of (is_valid, user_data, error_message)
        """
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            response = requests.post(
                self.validate_endpoint,
                json={
                    'token': token,
                    'service_name': self.service_name
                },
                headers={
                    'X-API-Key': self.api_key,
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            
            data = response.json()
            
            if response.status_code == 200:
                return True, data.get('user'), None
            else:
                error_msg = data.get('error_message') or data.get('error') or 'Token validation failed'
                return False, None, error_msg
                
        except requests.exceptions.Timeout:
            logger.error("Hub auth validation timeout")
            return False, None, "Hub auth service timeout"
        except requests.exceptions.ConnectionError:
            logger.error("Hub auth connection error")
            return False, None, "Hub auth service unavailable"
        except Exception as e:
            logger.error(f"Hub auth validation error: {str(e)}", exc_info=True)
            return False, None, f"Validation error: {str(e)}"
    
    def validate_token_simple(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Simple token validation using GET endpoint.
        
        Args:
            token: JWT token string
        
        Returns:
            Tuple of (is_valid, minimal_user_data)
        """
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            response = requests.get(
                self.validate_simple_endpoint,
                headers={
                    'Authorization': f'Bearer {token}',
                    'X-API-Key': self.api_key
                },
                timeout=5
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('is_valid'):
                return True, data.get('user')
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"Hub auth simple validation error: {str(e)}", exc_info=True)
            return False, None


class DjangoHubAuthBackend:
    """
    Django authentication backend that uses hub_auth for token validation.
    
    Add to your Django settings.py:
    
    AUTHENTICATION_BACKENDS = [
        'path.to.DjangoHubAuthBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    
    HUB_AUTH_URL = 'http://localhost:8000'
    HUB_AUTH_API_KEY = 'your-api-key'
    HUB_AUTH_SERVICE_NAME = 'your-service-name'
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate using hub_auth token validation.
        
        Args:
            request: Django request object
            token: JWT token from MSAL
        
        Returns:
            User object if valid, None otherwise
        """
        if not token:
            # Try to extract from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                return None
        
        # Get hub_auth configuration from Django settings
        from django.conf import settings
        
        hub_auth_url = getattr(settings, 'HUB_AUTH_URL', None)
        api_key = getattr(settings, 'HUB_AUTH_API_KEY', None)
        service_name = getattr(settings, 'HUB_AUTH_SERVICE_NAME', 'django-service')
        
        if not hub_auth_url or not api_key:
            logger.error("HUB_AUTH_URL and HUB_AUTH_API_KEY must be configured in settings")
            return None
        
        # Validate token with hub_auth
        client = HubAuthClient(hub_auth_url, api_key, service_name)
        is_valid, user_data, error_msg = client.validate_token(token)
        
        if not is_valid or not user_data:
            logger.warning(f"Token validation failed: {error_msg}")
            return None
        
        # Get or create local user based on hub_auth response
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try to find user by azure_ad_object_id or username
        azure_oid = user_data.get('azure_ad_object_id')
        username = user_data.get('username')
        email = user_data.get('email')
        
        user = None
        
        # Try to find by Azure OID first (if your User model has this field)
        if azure_oid and hasattr(User, 'azure_ad_object_id'):
            try:
                user = User.objects.get(azure_ad_object_id=azure_oid)
            except User.DoesNotExist:
                pass
        
        # Try by username
        if not user and username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        
        # Try by email
        if not user and email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        # Create user if not found
        if not user:
            user = User.objects.create(
                username=username or azure_oid,
                email=email or '',
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                is_active=user_data.get('is_active', True)
            )
            
            # Set additional fields if they exist on your User model
            if hasattr(user, 'azure_ad_object_id') and azure_oid:
                user.azure_ad_object_id = azure_oid
            if hasattr(user, 'display_name'):
                user.display_name = user_data.get('display_name')
            if hasattr(user, 'user_principal_name'):
                user.user_principal_name = user_data.get('user_principal_name')
            
            user.save()
            logger.info(f"Created new user from hub_auth: {username}")
        
        return user
    
    def get_user(self, user_id):
        """Get user by ID."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
