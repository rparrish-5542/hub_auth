"""
Django integration for hub_auth_client.

Provides middleware, decorators, and utilities for integrating MSAL token
validation into Django REST Framework projects.
"""

from .authentication import MSALAuthentication
from .decorators import require_roles, require_scopes, require_token
from .dynamic_permissions import DynamicPermission, DynamicRolePermission, DynamicScopePermission
from .middleware import MSALAuthenticationMiddleware
from .permissions import HasAllRoles, HasAllScopes, HasAnyRole, HasAnyScope, HasRoles, HasScopes

# RLS components (optional, require PostgreSQL)
# Use lazy imports to avoid circular import issues
RLS_AVAILABLE = False
RLSPolicy = None
RLSTableConfig = None
RLSMiddleware = None
RLSDebugMiddleware = None

def _init_rls():
    """Lazy initialization of RLS components."""
    global RLS_AVAILABLE, RLSPolicy, RLSTableConfig, RLSMiddleware, RLSDebugMiddleware
    if RLS_AVAILABLE is not False:  # Already initialized
        return
    try:
        from .rls_middleware import RLSDebugMiddleware as _RLSDebugMiddleware
        from .rls_middleware import RLSMiddleware as _RLSMiddleware
        from .rls_models import RLSPolicy as _RLSPolicy
        from .rls_models import RLSTableConfig as _RLSTableConfig
        RLSPolicy = _RLSPolicy
        RLSTableConfig = _RLSTableConfig
        RLSMiddleware = _RLSMiddleware
        RLSDebugMiddleware = _RLSDebugMiddleware
        RLS_AVAILABLE = True
    except ImportError:
        RLS_AVAILABLE = False

# Config models (optional, for database-driven configuration)
#Use lazy imports to avoid circular import issues
CONFIG_AVAILABLE = False
AzureADConfiguration = None
AzureADConfigurationHistory = None

def _init_config():
    """Lazy initialization of config components."""
    global CONFIG_AVAILABLE, AzureADConfiguration, AzureADConfigurationHistory
    if CONFIG_AVAILABLE is not False:  # Already initialized
        return
    try:
        from .config_models import AzureADConfiguration as _AzureADConfiguration
        from .config_models import AzureADConfigurationHistory as _AzureADConfigurationHistory
        AzureADConfiguration = _AzureADConfiguration
        AzureADConfigurationHistory = _AzureADConfigurationHistory
        CONFIG_AVAILABLE = True
    except ImportError:
        CONFIG_AVAILABLE = False

# Admin SSO (optional, for MSAL-based admin authentication)
# Use lazy imports to avoid circular import issues
ADMIN_SSO_AVAILABLE = False
MSALAdminBackend = None
MSALAdminLoginView = None
MSALAdminCallbackView = None

def _init_admin_sso():
    """Lazy initialization of admin SSO components."""
    global ADMIN_SSO_AVAILABLE, MSALAdminBackend, MSALAdminLoginView, MSALAdminCallbackView
    if ADMIN_SSO_AVAILABLE is not False:  # Already initialized
        return
    try:
        from .admin_auth import MSALAdminBackend as _MSALAdminBackend
        from .admin_views import MSALAdminCallbackView as _MSALAdminCallbackView
        from .admin_views import MSALAdminLoginView as _MSALAdminLoginView
        MSALAdminBackend = _MSALAdminBackend
        MSALAdminLoginView = _MSALAdminLoginView
        MSALAdminCallbackView = _MSALAdminCallbackView
        ADMIN_SSO_AVAILABLE = True
    except ImportError:
        ADMIN_SSO_AVAILABLE = False

__all__ = [
    "MSALAuthenticationMiddleware",
    "MSALAuthentication",
    "require_token",
    "require_scopes",
    "require_roles",
    "HasScopes",
    "HasRoles",
    "HasAnyScope",
    "HasAnyRole",
    "HasAllScopes",
    "HasAllRoles",
    # Dynamic permissions (database-driven)
    "DynamicPermission",
    "DynamicScopePermission",
    "DynamicRolePermission",
    # RLS (Row-Level Security) - PostgreSQL only
    "RLSPolicy",
    "RLSTableConfig",
    "RLSMiddleware",
    "RLSDebugMiddleware",
    "RLS_AVAILABLE",
    # Configuration models (database-driven config)
    "AzureADConfiguration",
    "AzureADConfigurationHistory",
    "CONFIG_AVAILABLE",
    # Admin SSO (MSAL-based admin authentication)
    "MSALAdminBackend",
    "MSALAdminLoginView",
    "MSALAdminCallbackView",
    "ADMIN_SSO_AVAILABLE",
]

