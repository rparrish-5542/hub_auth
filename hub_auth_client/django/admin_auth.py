"""
MSAL-based SSO authentication backend for Django admin.

Allows users to log into Django admin using their Microsoft Entra ID (Azure AD) credentials
instead of Django username/password.
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class MSALAdminBackend(BaseBackend):
    """
    Authentication backend that creates/authenticates Django users from MSAL tokens.
    
    This backend:
    1. Validates MSAL JWT tokens
    2. Creates Django users automatically from token claims
    3. Updates user information on each login
    4. Grants superuser/staff permissions based on Azure AD roles
    
    Usage in settings.py:
        AUTHENTICATION_BACKENDS = [
            'hub_auth_client.django.admin_auth.MSALAdminBackend',
            'django.contrib.auth.backends.ModelBackend',  # Fallback
        ]
        
        # Optional: Map Azure AD roles to Django permissions
        MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin']
        MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']
    """
    
    def authenticate(self, request, token=None, claims=None):
        """
        Authenticate user from MSAL token claims.
        
        Args:
            request: Django request object
            token: MSAL JWT token (optional, will be extracted from request if not provided)
            claims: Pre-validated token claims (optional)
        
        Returns:
            User instance if authentication succeeds, None otherwise
        """
        if claims is None:
            if token is None and request is not None:
                # Try to extract token from request
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                if not auth_header.startswith('Bearer '):
                    return None
                token = auth_header
            
            if not token:
                return None
            
            # Validate token
            claims = self._validate_token(token)
            if not claims:
                return None
        
        # Extract user information from claims
        user_id = claims.get('oid')  # Azure AD Object ID
        email = claims.get('email') or claims.get('preferred_username') or claims.get('upn')
        name = claims.get('name', '')
        roles = claims.get('roles', [])
        
        if not user_id or not email:
            logger.warning("Token missing required claims (oid or email)")
            return None
        
        # Get or create user
        user = self._get_or_create_user(
            user_id=user_id,
            email=email,
            name=name,
            roles=roles
        )
        
        return user
    
    def _validate_token(self, token):
        """
        Validate MSAL token and return claims.
        
        Args:
            token: MSAL JWT token string
        
        Returns:
            dict: Token claims if valid, None otherwise
        """
        try:
            # Try database config first
            from .config_models import AzureADConfiguration
            config = AzureADConfiguration.get_active_config()
            
            if config:
                validator = config.get_validator()
            else:
                # Fall back to creating validator from settings
                from ..validator import MSALTokenValidator
                
                tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
                client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
                
                if not tenant_id or not client_id:
                    logger.error("No Azure AD configuration found")
                    return None
                
                validator = MSALTokenValidator(
                    tenant_id=tenant_id,
                    client_id=client_id
                )
            
            is_valid, claims, error = validator.validate_token(token)
            
            if not is_valid:
                logger.warning(f"Token validation failed: {error}")
                return None
            
            return claims
            
        except Exception as e:
            logger.exception(f"Error validating token: {e}")
            return None
    
    def _get_or_create_user(self, user_id, email, name, roles):
        """
        Get or create Django user from Azure AD information.
        
        Args:
            user_id: Azure AD Object ID
            email: User email
            name: User display name
            roles: List of Azure AD roles
        
        Returns:
            User instance
        """
        # Try to find existing user by username (Azure AD Object ID)
        try:
            user = User.objects.get(username=user_id)
            # Update user information
            user = self._update_user(user, email, name, roles)
        except User.DoesNotExist:
            # Create new user
            user = self._create_user(user_id, email, name, roles)
        
        return user
    
    def _create_user(self, user_id, email, name, roles):
        """
        Create new Django user from Azure AD information.
        
        Args:
            user_id: Azure AD Object ID
            email: User email
            name: User display name
            roles: List of Azure AD roles
        
        Returns:
            User instance
        """
        # Split name into first and last
        name_parts = name.split(' ', 1) if name else ['', '']
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Determine permissions based on roles
        is_superuser = self._has_superuser_role(roles)
        is_staff = self._has_staff_role(roles) or is_superuser
        
        user = User.objects.create_user(
            username=user_id,
            email=email,
            first_name=first_name[:30],  # Django limit
            last_name=last_name[:150],   # Django limit
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True,
        )
        
        logger.info(f"Created user {user_id} ({email}) with staff={is_staff}, superuser={is_superuser}")
        
        return user
    
    def _update_user(self, user, email, name, roles):
        """
        Update existing Django user with latest Azure AD information.
        
        Args:
            user: User instance
            email: User email
            name: User display name
            roles: List of Azure AD roles
        
        Returns:
            Updated User instance
        """
        updated = False
        
        # Update email if changed
        if user.email != email:
            user.email = email
            updated = True
        
        # Update name if changed
        if name:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0][:30]
            last_name = name_parts[1][:150] if len(name_parts) > 1 else ''
            
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
        
        # Update permissions based on current roles
        is_superuser = self._has_superuser_role(roles)
        is_staff = self._has_staff_role(roles) or is_superuser
        
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            updated = True
            logger.info(f"Updated superuser status for {user.username}: {is_superuser}")
        
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            updated = True
            logger.info(f"Updated staff status for {user.username}: {is_staff}")
        
        # Ensure user is active
        if not user.is_active:
            user.is_active = True
            updated = True
        
        if updated:
            user.save()
        
        return user
    
    def _has_superuser_role(self, roles):
        """
        Check if user has any role that grants superuser permissions.
        
        Args:
            roles: List of Azure AD role names
        
        Returns:
            bool: True if user should be superuser
        """
        superuser_roles = getattr(settings, 'MSAL_SUPERUSER_ROLES', ['Admin', 'GlobalAdmin'])
        return any(role in superuser_roles for role in roles)
    
    def _has_staff_role(self, roles):
        """
        Check if user has any role that grants staff permissions.
        
        Args:
            roles: List of Azure AD role names
        
        Returns:
            bool: True if user should be staff
        """
        staff_roles = getattr(settings, 'MSAL_STAFF_ROLES', ['Staff', 'Manager', 'Admin'])
        return any(role in staff_roles for role in roles)
    
    def get_user(self, user_id):
        """
        Get user by primary key.
        
        Args:
            user_id: User primary key
        
        Returns:
            User instance or None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
