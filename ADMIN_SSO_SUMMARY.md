# Admin SSO Quick Reference

## Overview

MSAL-based Single Sign-On (SSO) for Django admin that automatically creates and manages Django users from Azure AD accounts.

## Quick Setup

### 1. Settings Configuration

```python
# settings.py
INSTALLED_APPS = [
    'hub_auth_client.django',
    # ...
]

AUTHENTICATION_BACKENDS = [
    'hub_auth_client.django.admin_auth.MSALAdminBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AZURE_AD_TENANT_ID = 'your-tenant-id'
AZURE_AD_CLIENT_ID = 'your-client-id'
AZURE_AD_CLIENT_SECRET = 'your-client-secret'

MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin']
MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']
```

### 2. URL Configuration

```python
# urls.py
from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView

urlpatterns = [
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    path('admin/', admin.site.urls),
]
```

### 3. Azure AD Configuration

1. Register application in Azure AD
2. Create client secret
3. Add redirect URI: `https://yourdomain.com/admin/login/msal/callback/`
4. Add token claims: `email`, `name`, `roles`
5. Create app roles: `Admin`, `Staff`, etc.
6. Grant admin consent

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Admin SSO Login Flow                        │
└─────────────────────────────────────────────────────────────────┘

1. User clicks "Sign in with Microsoft"
   └─> MSALAdminLoginView redirects to Microsoft

2. User authenticates with Microsoft credentials
   └─> Microsoft validates and redirects back

3. MSALAdminCallbackView receives authorization code
   └─> Exchanges code for access token and ID token

4. ID token is validated using Azure AD public keys
   └─> MSALAdminBackend extracts user claims

5. Django user is created or updated
   ├─> Username = Azure AD user ID (oid)
   ├─> Email = user's email
   ├─> Name = first/last name
   └─> Permissions = mapped from roles

6. User is logged into Django admin
   └─> Access granted if has staff role
```

## User Provisioning

### Automatic User Creation

When a user logs in for the first time:

```python
# Azure AD token claims:
{
    "oid": "abc123...",           # Unique user ID
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["Staff"]
}

# Creates Django user:
username = "abc123..."
email = "user@example.com"
first_name = "John"
last_name = "Doe"
is_staff = True   # Has 'Staff' role
is_superuser = False
is_active = True
```

### Automatic User Updates

On subsequent logins, user information is updated:

- Email address (if changed in Azure AD)
- First/Last name (if changed in Azure AD)
- Staff status (based on current roles)
- Superuser status (based on current roles)

## Role Mapping

### Default Configuration

```python
# Users with these roles become superusers
MSAL_SUPERUSER_ROLES = ['Admin', 'GlobalAdmin']

# Users with these roles become staff
MSAL_STAFF_ROLES = ['Staff', 'Manager', 'Admin']
```

### Permission Matrix

| Azure AD Role | is_staff | is_superuser | Admin Access | Full Permissions |
|---------------|----------|--------------|--------------|------------------|
| Admin         | ✅ Yes   | ✅ Yes       | ✅ Yes       | ✅ Yes           |
| Staff         | ✅ Yes   | ❌ No        | ✅ Yes       | ❌ No            |
| (no role)     | ❌ No    | ❌ No        | ❌ No        | ❌ No            |

### Custom Role Mapping

```python
# Custom superuser roles
MSAL_SUPERUSER_ROLES = ['SuperAdmin', 'Owner', 'IT-Admin']

# Custom staff roles
MSAL_STAFF_ROLES = ['Staff', 'Editor', 'Moderator', 'SuperAdmin']
```

## Components

### MSALAdminBackend

Django authentication backend that:
- Validates MSAL ID tokens
- Creates Django users from Azure AD
- Maps Azure AD roles to Django permissions
- Updates user info on each login

**Usage:**
```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'hub_auth_client.django.admin_auth.MSALAdminBackend',
]
```

### MSALAdminLoginView

Initiates OAuth2 login flow:
- Generates state parameter for CSRF protection
- Builds authorization URL
- Redirects to Microsoft login

**Usage:**
```python
# urls.py
path('admin/login/msal/', MSALAdminLoginView.as_view())
```

### MSALAdminCallbackView

Handles OAuth2 callback:
- Validates state parameter
- Exchanges code for tokens
- Validates ID token
- Authenticates user
- Grants admin access

**Usage:**
```python
# urls.py
path('admin/login/msal/callback/', MSALAdminCallbackView.as_view())
```

## Configuration Options

### Database Configuration (Recommended)

Store Azure AD credentials in database:

```python
# Configure via Django admin instead of settings
# Admin > Azure AD Configurations > Add Configuration
```

See [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md)

### Settings Configuration

```python
# Required
AZURE_AD_TENANT_ID = 'xxx-xxx-xxx'
AZURE_AD_CLIENT_ID = 'yyy-yyy-yyy'
AZURE_AD_CLIENT_SECRET = 'zzz-zzz-zzz'

# Optional
MSAL_ADMIN_REDIRECT_URI = 'https://yourdomain.com/callback/'
MSAL_SUPERUSER_ROLES = ['Admin']
MSAL_STAFF_ROLES = ['Staff', 'Admin']
MSAL_ADMIN_SCOPES = ['openid', 'profile', 'email', 'User.Read']
```

### Environment Variables

```bash
# .env
AZURE_AD_TENANT_ID=xxx-xxx-xxx
AZURE_AD_CLIENT_ID=yyy-yyy-yyy
AZURE_AD_CLIENT_SECRET=zzz-zzz-zzz
```

```python
# settings.py
import os
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')
```

## Testing

### Run Tests

```bash
pytest tests/test_admin_sso.py -v
```

### Test Coverage

```bash
pytest tests/test_admin_sso.py --cov=hub_auth_client.django.admin_auth --cov=hub_auth_client.django.admin_views
```

### Manual Testing

1. Navigate to `/admin/login/msal/`
2. Click "Sign in with Microsoft"
3. Authenticate with Azure AD
4. Verify redirect to `/admin/`
5. Check Django admin > Users for created user

## Common Issues

### "Invalid state parameter"
- **Cause**: Sessions not configured or CSRF attack
- **Fix**: Enable SessionMiddleware in MIDDLEWARE

### "User does not have permission"
- **Cause**: User lacks required Azure AD roles
- **Fix**: Assign roles in Azure AD or update MSAL_STAFF_ROLES

### "Token validation failed"
- **Cause**: Wrong tenant ID or client ID
- **Fix**: Verify configuration matches Azure AD app

### "Redirect URI mismatch"
- **Cause**: Redirect URI doesn't match Azure AD config
- **Fix**: Update Azure AD app registration or MSAL_ADMIN_REDIRECT_URI

## Security Best Practices

1. **Use HTTPS in production**
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   ```

2. **Store secrets securely**
   - Use environment variables
   - Never commit secrets to version control

3. **Restrict admin roles**
   ```python
   MSAL_STAFF_ROLES = ['Admin']  # Only admins, not all users
   ```

4. **Enable audit logging**
   ```python
   LOGGING = {
       'loggers': {
           'hub_auth_client.django.admin_auth': {'level': 'INFO'},
       }
   }
   ```

5. **Rotate client secrets regularly**
   - Create new secret in Azure AD
   - Update configuration
   - Delete old secret

## Example Files

- **Settings**: `examples/example_admin_sso_settings.py`
- **URLs**: `examples/example_admin_sso_urls.py`
- **Tests**: `tests/test_admin_sso.py`

## Full Documentation

See [ADMIN_SSO_GUIDE.md](ADMIN_SSO_GUIDE.md) for:
- Detailed setup instructions
- Azure AD configuration steps
- Advanced customization
- Troubleshooting guide
- Multi-tenant setup
- Custom authentication logic

## Support

**Issues?**
1. Check [ADMIN_SSO_GUIDE.md](ADMIN_SSO_GUIDE.md) troubleshooting section
2. Enable debug logging: `logger.setLevel(logging.DEBUG)`
3. Review test examples in `tests/test_admin_sso.py`
4. Verify Azure AD app registration configuration
