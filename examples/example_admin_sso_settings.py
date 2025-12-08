"""
Example Django settings for admin SSO configuration.

Copy relevant settings to your project's settings.py file.
"""

# ============================================================================
# BASIC CONFIGURATION
# Minimal settings required for admin SSO
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add hub_auth_client
    'hub_auth_client.django',
    
    # Your other apps
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Required for SSO
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Required
    'django.contrib.messages.middleware.MessageMiddleware',  # Required for error messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication backends - MSAL backend for SSO
AUTHENTICATION_BACKENDS = [
    'hub_auth_client.django.admin_auth.MSALAdminBackend',  # SSO authentication
    'django.contrib.auth.backends.ModelBackend',  # Fallback for local users
]

# Azure AD Configuration
AZURE_AD_TENANT_ID = 'your-tenant-id-here'
AZURE_AD_CLIENT_ID = 'your-client-id-here'
AZURE_AD_CLIENT_SECRET = 'your-client-secret-here'  # Required for OAuth2 flow


# ============================================================================
# ENVIRONMENT VARIABLES (RECOMMENDED)
# Use environment variables for sensitive data
# ============================================================================

import os

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')


# ============================================================================
# ROLE MAPPING CONFIGURATION
# Customize how Azure AD roles map to Django permissions
# ============================================================================

# Users with these Azure AD roles will become Django superusers
# Superusers have all permissions and can access everything
MSAL_SUPERUSER_ROLES = [
    'Admin',
    'GlobalAdmin',
    'SuperAdmin',
]

# Users with these Azure AD roles will become Django staff
# Staff users can access admin site but have limited permissions
MSAL_STAFF_ROLES = [
    'Staff',
    'Manager',
    'Admin',  # Admins are also staff
    'Editor',
    'Moderator',
]

# Note: Users with no matching roles will be denied admin access


# ============================================================================
# CUSTOM REDIRECT URI (OPTIONAL)
# Specify custom callback URL
# ============================================================================

# By default, redirect URI is auto-detected from request
# Set this if you need a specific redirect URI (e.g., behind proxy)
MSAL_ADMIN_REDIRECT_URI = 'https://yourdomain.com/admin/login/msal/callback/'

# For development
if DEBUG:
    MSAL_ADMIN_REDIRECT_URI = 'http://localhost:8000/admin/login/msal/callback/'


# ============================================================================
# CUSTOM SCOPES (OPTIONAL)
# Customize OAuth2 scopes requested
# ============================================================================

# Default scopes provide basic profile information
MSAL_ADMIN_SCOPES = [
    'openid',      # Required for ID token
    'profile',     # User's profile information
    'email',       # User's email address
    'User.Read',   # Microsoft Graph - read user profile
]

# Extended scopes for additional data
MSAL_ADMIN_SCOPES_EXTENDED = [
    'openid',
    'profile',
    'email',
    'User.Read',
    'User.ReadBasic.All',  # Read other users' basic info
    'Directory.Read.All',  # Read directory data (requires admin consent)
]


# ============================================================================
# DATABASE CONFIGURATION (ALTERNATIVE)
# Use database to store Azure AD configuration instead of settings
# ============================================================================

# Option 1: Database only (recommended for multi-tenant or dynamic config)
# Don't set AZURE_AD_* settings in settings.py
# Configure via Django admin > Azure AD Configurations

# Option 2: Database with settings fallback
# Set settings as fallback, use database for overrides
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')  # Fallback
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')  # Fallback
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')  # Fallback
# Database config takes precedence if active config exists


# ============================================================================
# SESSION CONFIGURATION
# Configure sessions for SSO state management
# ============================================================================

# Session engine (choose one)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Database (recommended)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Cache (faster)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Hybrid

# Session timeout
SESSION_COOKIE_AGE = 3600  # 1 hour (in seconds)
SESSION_SAVE_EVERY_REQUEST = False  # Set True to extend session on every request

# Session security
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection


# ============================================================================
# PRODUCTION SECURITY SETTINGS
# Required security settings for production deployment
# ============================================================================

if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Other security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'


# ============================================================================
# LOGGING CONFIGURATION
# Enable logging for troubleshooting and security monitoring
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/admin_sso.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # Admin SSO authentication
        'hub_auth_client.django.admin_auth': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # Change to DEBUG for troubleshooting
            'propagate': False,
        },
        # Admin SSO views
        'hub_auth_client.django.admin_views': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Token validation
        'hub_auth_client.core': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Only log warnings/errors
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)


# ============================================================================
# DEVELOPMENT SETTINGS
# Settings for local development
# ============================================================================

if DEBUG:
    # Allow local development without HTTPS
    MSAL_ADMIN_REDIRECT_URI = 'http://localhost:8000/admin/login/msal/callback/'
    
    # More verbose logging
    LOGGING['loggers']['hub_auth_client.django.admin_auth']['level'] = 'DEBUG'
    LOGGING['loggers']['hub_auth_client.django.admin_views']['level'] = 'DEBUG'
    
    # Allow all hosts for testing
    ALLOWED_HOSTS = ['*']


# ============================================================================
# MULTI-TENANT CONFIGURATION (ADVANCED)
# Support multiple Azure AD tenants
# ============================================================================

# Example multi-tenant setup
AZURE_AD_MULTI_TENANT = {
    'primary': {
        'TENANT_ID': 'primary-tenant-id',
        'CLIENT_ID': 'primary-client-id',
        'CLIENT_SECRET': 'primary-secret',
        'SUPERUSER_ROLES': ['Admin'],
        'STAFF_ROLES': ['Staff', 'Admin'],
    },
    'partner': {
        'TENANT_ID': 'partner-tenant-id',
        'CLIENT_ID': 'partner-client-id',
        'CLIENT_SECRET': 'partner-secret',
        'SUPERUSER_ROLES': ['PartnerAdmin'],
        'STAFF_ROLES': ['PartnerStaff', 'PartnerAdmin'],
    },
}

# You would need to create custom views to handle tenant selection
# This is an advanced use case - contact support for implementation help


# ============================================================================
# CUSTOM AUTHENTICATION BACKEND (ADVANCED)
# Extend the default SSO backend
# ============================================================================

# Example in myapp/auth_backends.py:
"""
from hub_auth_client.django.admin_auth import MSALAdminBackend

class CustomMSALAdminBackend(MSALAdminBackend):
    def _create_user(self, user_id, email, name, roles):
        # Call parent to create user
        user = super()._create_user(user_id, email, name, roles)
        
        # Custom logic - e.g., create user profile
        from myapp.models import UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'department': self._extract_department(roles),
                'azure_ad_id': user_id,
            }
        )
        
        return user
    
    def _extract_department(self, roles):
        # Custom department mapping
        if 'IT-Admin' in roles:
            return 'IT'
        elif 'HR-Staff' in roles:
            return 'HR'
        return 'General'
"""

# Then use custom backend in settings:
# AUTHENTICATION_BACKENDS = [
#     'myapp.auth_backends.CustomMSALAdminBackend',
#     'django.contrib.auth.backends.ModelBackend',
# ]


# ============================================================================
# QUICK START CHECKLIST
# ============================================================================

"""
Quick Start Configuration Checklist:

1. ✅ Add 'hub_auth_client.django' to INSTALLED_APPS
2. ✅ Add MSALAdminBackend to AUTHENTICATION_BACKENDS
3. ✅ Set AZURE_AD_TENANT_ID (from Azure AD)
4. ✅ Set AZURE_AD_CLIENT_ID (from Azure AD app registration)
5. ✅ Set AZURE_AD_CLIENT_SECRET (from Azure AD app registration)
6. ✅ Configure MSAL_SUPERUSER_ROLES and MSAL_STAFF_ROLES
7. ✅ Set up session middleware (SessionMiddleware)
8. ✅ Set up messages middleware (MessageMiddleware)
9. ✅ Configure URLs (see example_admin_sso_urls.py)
10. ✅ Run migrations: python manage.py migrate
11. ✅ Configure redirect URI in Azure AD app registration
12. ✅ Test SSO login flow

For production:
13. ✅ Enable HTTPS (SECURE_SSL_REDIRECT = True)
14. ✅ Use environment variables for secrets
15. ✅ Set up logging
16. ✅ Configure proper ALLOWED_HOSTS
17. ✅ Test role-based access control

See ADMIN_SSO_GUIDE.md for detailed setup instructions.
"""
