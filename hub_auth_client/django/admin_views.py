"""
MSAL SSO login view for Django admin.

Provides OAuth2 flow for logging into Django admin with Microsoft credentials.
"""

from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views import View
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from urllib.parse import urlencode
import secrets
import logging

logger = logging.getLogger(__name__)


class MSALAdminLoginView(View):
    """
    Initiates MSAL OAuth2 login flow for Django admin.
    
    Usage in urls.py:
        from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView
        
        urlpatterns = [
            path('admin/login/msal/', MSALAdminLoginView.as_view(), name='msal_admin_login'),
            path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='msal_admin_callback'),
            path('admin/', admin.site.urls),
        ]
    """
    
    def get(self, request):
        """Redirect to Microsoft login page."""
        # Get configuration
        config = self._get_config()
        if not config:
            messages.error(request, "Azure AD is not configured")
            return redirect('/admin/login/')
        
        tenant_id, client_id = config
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session['msal_state'] = state
        
        # Get redirect URI
        redirect_uri = self._get_redirect_uri(request)
        request.session['msal_redirect_uri'] = redirect_uri
        
        # Build authorization URL
        auth_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'response_mode': 'query',
            'scope': 'openid profile email User.Read',
            'state': state,
        }
        
        auth_url = f"{auth_endpoint}?{urlencode(params)}"
        
        return redirect(auth_url)
    
    def _get_config(self):
        """Get Azure AD configuration."""
        try:
            from .config_models import AzureADConfiguration
            config = AzureADConfiguration.get_active_config()
            
            if config:
                return (config.tenant_id, config.client_id)
        except Exception:
            pass
        
        # Fall back to settings
        tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
        client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
        
        if tenant_id and client_id:
            return (tenant_id, client_id)
        
        return None
    
    def _get_redirect_uri(self, request):
        """Get redirect URI for OAuth callback."""
        # Check settings for custom redirect URI
        redirect_uri = getattr(settings, 'MSAL_ADMIN_REDIRECT_URI', None)
        
        if redirect_uri:
            return redirect_uri
        
        # Build redirect URI from request
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        
        return f"{scheme}://{host}/admin/login/msal/callback/"


class MSALAdminCallbackView(View):
    """
    Handles OAuth2 callback from Microsoft.
    
    Exchanges authorization code for access token and logs user in.
    """
    
    def get(self, request):
        """Handle OAuth callback."""
        # Validate state
        state = request.GET.get('state')
        expected_state = request.session.get('msal_state')
        
        if not state or state != expected_state:
            logger.warning("MSAL callback state mismatch")
            messages.error(request, "Invalid state parameter")
            return redirect('/admin/login/')
        
        # Check for error
        error = request.GET.get('error')
        if error:
            error_description = request.GET.get('error_description', error)
            logger.warning(f"MSAL login error: {error_description}")
            messages.error(request, f"Login failed: {error_description}")
            return redirect('/admin/login/')
        
        # Get authorization code
        code = request.GET.get('code')
        if not code:
            messages.error(request, "No authorization code received")
            return redirect('/admin/login/')
        
        # Exchange code for token
        token_data = self._exchange_code_for_token(request, code)
        if not token_data:
            messages.error(request, "Failed to obtain access token")
            return redirect('/admin/login/')
        
        # Authenticate user with token
        id_token = token_data.get('id_token')
        if not id_token:
            messages.error(request, "No ID token received")
            return redirect('/admin/login/')
        
        # Validate token and get claims
        claims = self._validate_id_token(id_token)
        if not claims:
            messages.error(request, "Invalid ID token")
            return redirect('/admin/login/')
        
        # Authenticate user
        from .admin_auth import MSALAdminBackend
        backend = MSALAdminBackend()
        
        user = backend.authenticate(request=request, claims=claims)
        if not user:
            messages.error(request, "Authentication failed")
            return redirect('/admin/login/')
        
        # Check if user has admin access
        if not user.is_staff:
            logger.warning(f"User {user.username} attempted admin login without staff privileges")
            messages.error(request, "You do not have permission to access the admin site")
            return redirect('/admin/login/')
        
        # Log user in
        user.backend = 'hub_auth_client.django.admin_auth.MSALAdminBackend'
        login(request, user)
        
        logger.info(f"User {user.username} logged in via MSAL")
        messages.success(request, f"Welcome, {user.get_full_name() or user.username}!")
        
        # Clean up session
        request.session.pop('msal_state', None)
        request.session.pop('msal_redirect_uri', None)
        
        # Redirect to admin
        next_url = request.GET.get('next', '/admin/')
        return redirect(next_url)
    
    def _exchange_code_for_token(self, request, code):
        """
        Exchange authorization code for access token.
        
        Args:
            request: Django request object
            code: Authorization code
        
        Returns:
            dict: Token data or None if failed
        """
        import requests
        
        # Get configuration
        config = self._get_config()
        if not config:
            return None
        
        tenant_id, client_id, client_secret = config
        
        if not client_secret:
            logger.error("Client secret not configured for admin SSO")
            return None
        
        # Get redirect URI from session
        redirect_uri = request.session.get('msal_redirect_uri')
        if not redirect_uri:
            logger.error("Redirect URI not found in session")
            return None
        
        # Exchange code for token
        token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'scope': 'openid profile email User.Read',
        }
        
        try:
            response = requests.post(token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Error exchanging code for token: {e}")
            return None
    
    def _validate_id_token(self, id_token):
        """
        Validate ID token and return claims.
        
        Args:
            id_token: JWT ID token
        
        Returns:
            dict: Token claims or None if invalid
        """
        try:
            from .config_models import AzureADConfiguration
            config = AzureADConfiguration.get_active_config()
            
            if config:
                validator = config.get_validator()
            else:
                from ..validator import MSALTokenValidator
                
                tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
                client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
                
                if not tenant_id or not client_id:
                    return None
                
                validator = MSALTokenValidator(
                    tenant_id=tenant_id,
                    client_id=client_id
                )
            
            is_valid, claims, error = validator.validate_token(id_token)
            
            if not is_valid:
                logger.warning(f"ID token validation failed: {error}")
                return None
            
            return claims
            
        except Exception as e:
            logger.exception(f"Error validating ID token: {e}")
            return None
    
    def _get_config(self):
        """Get Azure AD configuration including client secret."""
        try:
            from .config_models import AzureADConfiguration
            config = AzureADConfiguration.get_active_config()
            
            if config:
                return (config.tenant_id, config.client_id, config.client_secret)
        except Exception:
            pass
        
        # Fall back to settings
        tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
        client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
        client_secret = getattr(settings, 'AZURE_AD_CLIENT_SECRET', None)
        
        if tenant_id and client_id:
            return (tenant_id, client_id, client_secret)
        
        return None
