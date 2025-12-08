"""
Django integration for hub_auth_client.

Provides middleware, decorators, and utilities for integrating MSAL token
validation into Django REST Framework projects.
"""

from .middleware import MSALAuthenticationMiddleware
from .decorators import require_token, require_scopes, require_roles
from .authentication import MSALAuthentication
from .permissions import HasScopes, HasRoles, HasAnyScope, HasAnyRole, HasAllScopes, HasAllRoles
from .dynamic_permissions import DynamicPermission, DynamicScopePermission, DynamicRolePermission

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
        from .rls_models import RLSPolicy as _RLSPolicy, RLSTableConfig as _RLSTableConfig
        from .rls_middleware import RLSMiddleware as _RLSMiddleware, RLSDebugMiddleware as _RLSDebugMiddleware
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
        from .config_models import AzureADConfiguration as _AzureADConfiguration, AzureADConfigurationHistory as _AzureADConfigurationHistory
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
        from .admin_views import MSALAdminLoginView as _MSALAdminLoginView, MSALAdminCallbackView as _MSALAdminCallbackView
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

