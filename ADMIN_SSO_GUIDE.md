# Admin SSO Setup Guide

Complete guide for implementing MSAL-based Single Sign-On (SSO) for Django admin using the hub_auth_client package.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Azure AD Configuration](#azure-ad-configuration)
- [Django Configuration](#django-configuration)
- [URL Configuration](#url-configuration)
- [Role Mapping](#role-mapping)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Overview

The admin SSO feature allows your Django admin users to authenticate using their Microsoft Azure AD (Entra ID) accounts. This provides:

- **Single Sign-On**: Users authenticate once with their Microsoft account
- **Automatic User Provisioning**: Django users are created automatically from Azure AD
- **Role-Based Access Control**: Azure AD roles map to Django staff/superuser permissions
- **Enhanced Security**: Leverages Microsoft's authentication infrastructure
- **No Password Management**: Users authenticate through Microsoft, no local passwords needed

### How It Works

```
User → Django Admin Login → Microsoft Login Page → User Authenticates
     ← Django Admin Access ← User Created/Updated ← Token Validated
```

1. User visits Django admin login
2. Redirected to Microsoft login page
3. User authenticates with Microsoft credentials
4. Microsoft redirects back with authorization code
5. Django exchanges code for access token and ID token
6. ID token is validated and user info extracted
7. Django user is created or updated with Azure AD info
8. User is logged in and granted admin access (if has staff role)

## Quick Start

### 1. Install the Package

```bash
pip install hub-auth-client
```

### 2. Configure Django Settings

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps
    'hub_auth_client.django',
]

AUTHENTICATION_BACKENDS = [
    'hub_auth_client.django.admin_auth.MSALAdminBackend',
    'django.contrib.auth.backends.ModelBackend',  # Keep for fallback
]

# Azure AD Configuration
AZURE_AD_TENANT_ID = 'your-tenant-id'
AZURE_AD_CLIENT_ID = 'your-client-id'
AZURE_AD_CLIENT_SECRET = 'your-client-secret'  # Required for OAuth2 flow

# Optional: Custom role mapping
MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin']
MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']
```

### 3. Configure URLs

```python
# urls.py

from django.contrib import admin
from django.urls import path
from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView

urlpatterns = [
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    path('admin/', admin.site.urls),
]
```

### 4. Update Admin Login Template (Optional)

Add a Microsoft login button to your admin login page:

```html
<!-- templates/admin/login.html -->
{% extends "admin/login.html" %}

{% block content %}
{{ block.super }}
<div style="margin-top: 20px; text-align: center;">
    <a href="{% url 'admin_msal_login' %}" style="
        display: inline-block;
        padding: 10px 20px;
        background-color: #0078d4;
        color: white;
        text-decoration: none;
        border-radius: 4px;
    ">
        Sign in with Microsoft
    </a>
</div>
{% endblock %}
```

## Prerequisites

### Required Settings

- **AZURE_AD_TENANT_ID**: Your Azure AD tenant ID
- **AZURE_AD_CLIENT_ID**: Application (client) ID from Azure AD app registration
- **AZURE_AD_CLIENT_SECRET**: Client secret from Azure AD app registration

### Azure AD App Requirements

Your Azure AD application must have:

- **Redirect URI**: `https://yourdomain.com/admin/login/msal/callback/`
- **Token configuration**: Include `email`, `name`, and optionally `roles` claims
- **API permissions**: `User.Read` (for basic profile information)

## Azure AD Configuration

### Step 1: Register Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: Django Admin SSO
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: Web - `https://yourdomain.com/admin/login/msal/callback/`

### Step 2: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Set description and expiration
4. **Copy the secret value immediately** (won't be shown again)
5. Use this value for `AZURE_AD_CLIENT_SECRET`

### Step 3: Configure Token Claims

1. Go to **Token configuration**
2. Add optional claims:
   - **ID token**: email, name
3. Click **Add groups claim** (if using role-based access)
4. Select **Security groups** or **Directory roles**

### Step 4: Configure App Roles (Optional)

For role-based access control:

1. Go to **App roles**
2. Create roles matching your `MSAL_SUPERUSER_ROLES` and `MSAL_STAFF_ROLES`:
   ```
   Display name: Admin
   Value: Admin
   Description: Administrator role
   Allowed member types: Users/Groups
   ```
3. Assign users to roles in **Enterprise applications** > Your App > **Users and groups**

### Step 5: API Permissions

1. Go to **API permissions**
2. Add permissions:
   - Microsoft Graph > **User.Read** (Delegated)
3. Grant admin consent for your organization

## Django Configuration

### Database Configuration (Recommended)

Instead of hardcoding credentials in settings, use database configuration:

```python
# settings.py - Minimal configuration
INSTALLED_APPS = [
    'hub_auth_client.django',
    # ...
]

AUTHENTICATION_BACKENDS = [
    'hub_auth_client.django.admin_auth.MSALAdminBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

Then configure via Django admin:

1. Run migrations: `python manage.py migrate`
2. Create superuser: `python manage.py createsuperuser`
3. Login to admin and go to **Azure AD Configurations**
4. Click **Add Azure AD Configuration**
5. Fill in Tenant ID, Client ID, Client Secret
6. Mark as **Active**
7. Click **Save**

See [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md) for detailed instructions.

### Settings Configuration

Alternatively, configure directly in settings:

```python
# settings.py

# Azure AD OAuth2 Configuration
AZURE_AD_TENANT_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
AZURE_AD_CLIENT_ID = 'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy'
AZURE_AD_CLIENT_SECRET = 'your-client-secret-value'

# Optional: Custom redirect URI (defaults to auto-detected)
MSAL_ADMIN_REDIRECT_URI = 'https://yourdomain.com/admin/login/msal/callback/'

# Optional: Role mapping (defaults shown)
MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin']
MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']

# Optional: Custom scopes (defaults shown)
MSAL_ADMIN_SCOPES = ['openid', 'profile', 'email', 'User.Read']
```

### Environment Variables

For better security, use environment variables:

```python
# settings.py
import os

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')
```

```bash
# .env or environment
AZURE_AD_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_AD_CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
AZURE_AD_CLIENT_SECRET=your-client-secret-value
```

## URL Configuration

### Basic Setup

```python
# urls.py
from django.contrib import admin
from django.urls import path
from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView

urlpatterns = [
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    path('admin/', admin.site.urls),
]
```

### Custom Paths

You can customize the URL paths:

```python
urlpatterns = [
    path('admin/sso/', MSALAdminLoginView.as_view(), name='admin_sso_login'),
    path('admin/sso/auth/', MSALAdminCallbackView.as_view(), name='admin_sso_callback'),
    path('admin/', admin.site.urls),
]
```

**Important**: Update the redirect URI in Azure AD app registration to match your callback URL.

### Make SSO Default Login

To make SSO the default admin login:

```python
# urls.py
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect default admin login to SSO
    path('admin/login/', RedirectView.as_view(pattern_name='admin_msal_login', permanent=False)),
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    path('admin/', admin.site.urls),
]
```

## Role Mapping

### Understanding Role Mapping

The admin SSO system maps Azure AD roles to Django user permissions:

- **Staff Status** (`is_staff`): Determines if user can access admin site
- **Superuser Status** (`is_superuser`): Determines if user has all permissions

### Configuration

```python
# settings.py

# Users with these Azure AD roles become Django superusers
MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin', 'SuperAdmin']

# Users with these Azure AD roles become Django staff
MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin', 'Editor']
```

### Role Sources

Azure AD roles can come from:

1. **App Roles**: Defined in your Azure AD app registration
2. **Directory Roles**: Built-in Azure AD admin roles
3. **Group Claims**: Azure AD security groups

### Examples

**Example 1: Admin gets full access**

```python
MSAL_SUPERUSER_ROLES = ['Admin']
MSAL_STAFF_ROLES = ['Staff', 'Admin']

# Azure AD user with 'Admin' role:
# - is_staff = True
# - is_superuser = True
```

**Example 2: Staff gets limited access**

```python
MSAL_SUPERUSER_ROLES = ['Admin']
MSAL_STAFF_ROLES = ['Staff', 'Admin']

# Azure AD user with 'Staff' role:
# - is_staff = True
# - is_superuser = False
```

**Example 3: Regular user denied**

```python
MSAL_SUPERUSER_ROLES = ['Admin']
MSAL_STAFF_ROLES = ['Staff', 'Admin']

# Azure AD user with no matching roles:
# - is_staff = False
# - is_superuser = False
# - Cannot access admin (shown error message)
```

### Dynamic Permission Updates

User permissions are updated on **every login**:

- Promoted: User gains 'Admin' role → becomes superuser
- Demoted: User loses 'Admin' role → loses superuser status
- Removed: User loses all roles → loses admin access

## Testing

### Running Tests

```bash
# Run all admin SSO tests
pytest tests/test_admin_sso.py -v

# Run specific test class
pytest tests/test_admin_sso.py::TestMSALAdminBackend -v

# Run with coverage
pytest tests/test_admin_sso.py --cov=hub_auth_client.django.admin_auth --cov=hub_auth_client.django.admin_views
```

### Manual Testing

1. **Test Login Flow**:
   ```
   Navigate to: http://localhost:8000/admin/login/msal/
   Expected: Redirect to Microsoft login
   ```

2. **Test Callback**:
   ```
   After Microsoft login
   Expected: Redirect to /admin/ with user logged in
   ```

3. **Test User Creation**:
   ```python
   # Check Django admin > Users
   # Should see user with username = Azure AD user ID (oid)
   ```

4. **Test Permissions**:
   ```python
   # Login with user with 'Admin' role
   # Check: is_superuser = True, is_staff = True
   
   # Login with user with 'Staff' role
   # Check: is_superuser = False, is_staff = True
   ```

### Test Different Role Scenarios

```bash
# Create test users in Azure AD with different roles
# Login as each user and verify Django permissions match
```

## Troubleshooting

### Cannot Access Callback URL

**Problem**: `MSAL_ADMIN_REDIRECT_URI` doesn't match Azure AD configuration

**Solution**:
1. Check Azure AD app registration > Redirect URIs
2. Ensure exact match including trailing slash
3. Update `MSAL_ADMIN_REDIRECT_URI` setting or Azure AD config

### Invalid State Error

**Problem**: State parameter doesn't match (CSRF protection)

**Causes**:
- Sessions not configured correctly
- Multiple login attempts in different tabs
- Session expired between login and callback

**Solutions**:
```python
# Ensure sessions are configured
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ...
]

# Check session backend
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Or cache, file, etc.

# Increase session timeout if needed
SESSION_COOKIE_AGE = 3600  # 1 hour
```

### User Not Granted Admin Access

**Problem**: User authenticated but denied admin access

**Causes**:
- User doesn't have required Azure AD roles
- Role names don't match `MSAL_STAFF_ROLES`
- Roles not included in token

**Solutions**:

1. **Check user's Azure AD roles**:
   - Go to Azure AD > Enterprise applications > Your app > Users and groups
   - Verify user is assigned appropriate roles

2. **Check role configuration**:
   ```python
   # Verify role names match exactly (case-sensitive)
   MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']
   ```

3. **Verify roles in token**:
   ```python
   # Add debug logging to see token claims
   import logging
   logger = logging.getLogger('hub_auth_client.django.admin_auth')
   logger.setLevel(logging.DEBUG)
   ```

4. **Configure token claims in Azure AD**:
   - App registration > Token configuration
   - Add groups claim or ensure app roles are included

### Token Validation Fails

**Problem**: ID token validation fails

**Causes**:
- Wrong tenant ID or client ID
- Token expired
- Clock skew between servers

**Solutions**:

1. **Verify configuration**:
   ```python
   # Double-check these match Azure AD exactly
   AZURE_AD_TENANT_ID = 'your-tenant-id'
   AZURE_AD_CLIENT_ID = 'your-client-id'
   ```

2. **Check server time**:
   ```bash
   # Ensure server time is accurate
   date
   # Sync if needed
   sudo ntpdate pool.ntp.org  # Linux
   ```

3. **Enable debug logging**:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'hub_auth_client': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }
   ```

### Client Secret Issues

**Problem**: Token exchange fails with authentication error

**Causes**:
- Client secret expired
- Wrong client secret value
- Client secret not configured

**Solutions**:

1. **Generate new secret**:
   - Azure AD > App registration > Certificates & secrets
   - New client secret
   - Copy value immediately
   - Update `AZURE_AD_CLIENT_SECRET`

2. **Verify secret format**:
   ```python
   # Should be a string value, not the secret ID
   AZURE_AD_CLIENT_SECRET = 'abc123...'  # Correct
   # NOT the secret ID: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
   ```

### Database vs Settings Configuration

**Problem**: Using database config but settings override it

**Solution**: Database configuration takes precedence. To use settings-based config:

1. **Deactivate database configs**:
   ```python
   # Admin > Azure AD Configurations
   # Uncheck "Active" for all configurations
   ```

2. **Or delete database configs**:
   ```python
   # Django shell
   from hub_auth_client.django.config_models import AzureADConfiguration
   AzureADConfiguration.objects.all().delete()
   ```

## Security Considerations

### Client Secret Protection

**Never commit secrets to version control**:

```python
# ❌ BAD
AZURE_AD_CLIENT_SECRET = 'secret-value-here'

# ✅ GOOD
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')
```

### HTTPS Required

**Always use HTTPS in production**:

```python
# settings.py
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

Azure AD OAuth2 requires HTTPS for redirect URIs (except localhost).

### State Parameter

The state parameter prevents CSRF attacks. Never disable it or implement custom callback views without proper state validation.

### Token Storage

- Access tokens are **not stored** by default
- ID tokens are validated and discarded
- Only user claims are extracted and stored

### Role-Based Access

Always configure `MSAL_STAFF_ROLES` appropriately:

```python
# ❌ TOO PERMISSIVE
MSAL_STAFF_ROLES = []  # All authenticated users get admin access

# ✅ PROPER RESTRICTION
MSAL_STAFF_ROLES = ['Admin', 'Staff']  # Only users with these roles
```

### Regular Secret Rotation

Rotate client secrets regularly:

1. Create new secret in Azure AD
2. Update `AZURE_AD_CLIENT_SECRET`
3. Deploy changes
4. Delete old secret from Azure AD

### Audit Logging

Enable logging for security monitoring:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'admin_sso.log',
        },
    },
    'loggers': {
        'hub_auth_client.django.admin_auth': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

This logs:
- User creation events
- Permission changes
- Authentication failures
- Token validation errors

## Advanced Configuration

### Custom User Creation

Override user creation logic:

```python
# myapp/admin_auth.py
from hub_auth_client.django.admin_auth import MSALAdminBackend

class CustomMSALAdminBackend(MSALAdminBackend):
    def _create_user(self, user_id, email, name, roles):
        user = super()._create_user(user_id, email, name, roles)
        
        # Custom logic
        user.profile.department = self._extract_department(roles)
        user.profile.save()
        
        return user
    
    def _extract_department(self, roles):
        # Your custom logic
        if 'IT' in roles:
            return 'IT'
        return 'General'
```

```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'myapp.admin_auth.CustomMSALAdminBackend',
]
```

### Multiple Tenants

Support multiple Azure AD tenants:

```python
# settings.py
AZURE_AD_TENANTS = {
    'primary': {
        'TENANT_ID': 'tenant-1-id',
        'CLIENT_ID': 'client-1-id',
        'CLIENT_SECRET': 'secret-1',
    },
    'partner': {
        'TENANT_ID': 'tenant-2-id',
        'CLIENT_ID': 'client-2-id',
        'CLIENT_SECRET': 'secret-2',
    }
}
```

Then create custom views to handle tenant selection.

### Custom Redirect After Login

```python
# myapp/admin_views.py
from hub_auth_client.django.admin_views import MSALAdminCallbackView

class CustomCallbackView(MSALAdminCallbackView):
    def get_success_redirect_url(self):
        # Custom redirect logic
        if self.request.user.is_superuser:
            return '/admin/dashboard/'
        return '/admin/limited/'
```

```python
# urls.py
urlpatterns = [
    path('admin/login/msal/callback/', CustomCallbackView.as_view()),
]
```

## Next Steps

1. ✅ Configure Azure AD app registration
2. ✅ Update Django settings
3. ✅ Configure URLs
4. ✅ Run migrations
5. ✅ Test login flow
6. ✅ Configure role mapping
7. ✅ Enable HTTPS in production
8. ✅ Set up secret rotation schedule
9. ✅ Configure logging/monitoring
10. ✅ Update admin login template (optional)

## Related Documentation

- [Database Configuration Guide](DATABASE_CONFIG_GUIDE.md)
- [Installation Guide](INSTALL_IN_EMPLOYEE_MANAGE.md)
- [Start Here Guide](START_HERE.md)
- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [test_admin_sso.py](tests/test_admin_sso.py) for examples
3. Enable debug logging for detailed error messages
4. Check Azure AD app registration configuration
