# Hub Auth Client

A Python package for validating MSAL JWT tokens with Microsoft Entra ID (Azure AD) and implementing scope-based RBAC (Role-Based Access Control).

## Features

- **JWT Token Validation**: Validates MSAL tokens using Azure AD public key verification
- **Scope-Based RBAC**: Validate tokens have required scopes (delegated permissions)
- **Role-Based RBAC**: Validate tokens have required app roles
- **Django Integration**: Middleware, authentication backends, and permission classes for Django/DRF
- **Admin SSO**: MSAL-based Single Sign-On for Django admin with automatic user provisioning 🆕
- **Database Configuration**: Store Azure AD credentials in database instead of settings 🆕
- **Flexible Validation**: Require any or all scopes/roles
- **Production Ready**: Caching, error handling, and comprehensive logging
- **Type Hints**: Full type hint support for better IDE integration

## Installation

### Install via pip

```bash
pip install hub-auth-client
```

### Install with Django support

```bash
pip install hub-auth-client[django]
```

### Install from local directory

If you want to install from the source:

```bash
cd /path/to/hub_auth
pip install -e .
```

Or build and install:

```bash
python -m build
pip install dist/hub_auth_client-1.0.0-py3-none-any.whl
```

## Quick Start

### Standalone Usage (No Django)

```python
from hub_auth_client import MSALTokenValidator

# Initialize validator
validator = MSALTokenValidator(
    tenant_id="your-tenant-id",
    client_id="your-client-id"
)

# Validate token
token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
is_valid, claims, error = validator.validate_token(token)

if is_valid:
    print(f"User: {claims['upn']}")
    print(f"Scopes: {claims.get('scp', '').split()}")
else:
    print(f"Validation failed: {error}")
```

### Validate with Required Scopes

```python
# Require at least one scope
is_valid, claims, error = validator.validate_token(
    token,
    required_scopes=["User.Read", "Files.ReadWrite"],
    require_all_scopes=False  # User needs ANY of these scopes
)

# Require all scopes
is_valid, claims, error = validator.validate_token(
    token,
    required_scopes=["User.Read", "Files.ReadWrite"],
    require_all_scopes=True  # User needs ALL scopes
)
```

### Validate with Required Roles

```python
is_valid, claims, error = validator.validate_token(
    token,
    required_roles=["Admin", "Manager"],
    require_all_roles=False  # User needs ANY of these roles
)
```

### Extract User Information

```python
is_valid, claims, error = validator.validate_token(token)

if is_valid:
    user_info = validator.extract_user_info(claims)
    print(f"User: {user_info['name']}")
    print(f"Email: {user_info['email']}")
    print(f"Scopes: {user_info['scopes']}")
    print(f"Roles: {user_info['roles']}")
```

## Django Integration

### 1. Install in Django Project

```bash
cd /path/to/your/django_project
pip install /path/to/hub_auth
```

Or if published to PyPI:

```bash
pip install hub-auth-client[django]
```

### 2. Configure Django Settings

Add to your `settings.py`:

```python
# Azure AD Configuration
AZURE_AD_TENANT_ID = "your-tenant-id"
AZURE_AD_CLIENT_ID = "your-client-id"

# Optional MSAL settings
MSAL_VALIDATE_AUDIENCE = True  # Default: True
MSAL_VALIDATE_ISSUER = True    # Default: True
MSAL_TOKEN_LEEWAY = 0          # Leeway in seconds for time-based claims
MSAL_EXEMPT_PATHS = ['/health/', '/admin/']  # Paths that don't require auth
```

### 3. Use DRF Authentication Backend

Add to `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 4. Use in Views with Permission Classes

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import HasScopes, HasRoles, HasAllScopes

class UserProfileView(APIView):
    permission_classes = [HasScopes(['User.Read'])]
    
    def get(self, request):
        # User has User.Read scope
        user_info = {
            'username': request.user.username,
            'email': request.user.email,
            'scopes': request.user.scopes,
        }
        return Response(user_info)

class AdminView(APIView):
    permission_classes = [HasRoles(['Admin'])]
    
    def get(self, request):
        # User has Admin role
        return Response({'message': 'Admin access granted'})

class FileManagementView(APIView):
    # User needs BOTH scopes
    permission_classes = [HasAllScopes(['Files.Read', 'Files.Write'])]
    
    def post(self, request):
        return Response({'message': 'File created'})
```

### 5. Use with Decorators (Function-Based Views)

```python
from hub_auth_client.django import require_token, require_scopes, require_roles

@require_token
def my_view(request):
    """Token is validated, user info available in request.msal_user"""
    user_id = request.msal_user['object_id']
    return JsonResponse({'user_id': user_id})

@require_scopes(['User.Read', 'Files.ReadWrite'])
def read_files(request):
    """User has at least one of the required scopes"""
    return JsonResponse({'files': [...]})

@require_scopes(['Files.Read', 'Files.Write'], require_all=True)
def manage_files(request):
    """User has ALL required scopes"""
    return JsonResponse({'message': 'Access granted'})

@require_roles(['Admin', 'Manager'])
def admin_view(request):
    """User has at least one of the required roles"""
    return JsonResponse({'message': 'Admin access'})
```

### 6. Use Middleware (Optional)

Add to `MIDDLEWARE` in `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Add MSAL middleware
    'hub_auth_client.django.middleware.MSALAuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

The middleware attaches `request.msal_token` and `request.msal_user` to all requests.

## Configuration

### Environment Variables

Create a `.env` file:

```env
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here
```

Load in Django settings:

```python
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
```

### Getting Azure AD Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Create or select your application
4. Note the **Application (client) ID** - this is your `AZURE_AD_CLIENT_ID`
5. Note the **Directory (tenant) ID** - this is your `AZURE_AD_TENANT_ID`

### Configuring Scopes

In your Azure AD app registration:

1. Go to **API permissions**
2. Add delegated permissions (scopes) like `User.Read`, `Files.ReadWrite`, etc.
3. Grant admin consent if required

### Configuring Roles

In your Azure AD app registration:

1. Go to **App roles**
2. Create app roles like `Admin`, `Manager`, `User`, etc.
3. Assign users/groups to roles in **Enterprise Applications**

## API Reference

### MSALTokenValidator

Main class for token validation.

#### Constructor

```python
MSALTokenValidator(
    tenant_id: str,
    client_id: str,
    validate_audience: bool = True,
    validate_issuer: bool = True,
    leeway: int = 0,
    cache_jwks: bool = True,
    max_cached_keys: int = 16,
)
```

#### Methods

##### `validate_token(token, required_scopes=None, required_roles=None, require_all_scopes=False, require_all_roles=False)`

Validate a JWT token.

**Parameters:**
- `token` (str): JWT token string
- `required_scopes` (List[str], optional): Required scopes
- `required_roles` (List[str], optional): Required roles
- `require_all_scopes` (bool): If True, all scopes required
- `require_all_roles` (bool): If True, all roles required

**Returns:** Tuple of `(is_valid, claims, error_message)`

##### `extract_user_info(decoded_token)`

Extract user information from decoded token.

**Returns:** Dictionary with user info (object_id, email, name, scopes, roles, etc.)

##### `has_scope(decoded_token, scope)`

Check if token has a specific scope.

##### `has_role(decoded_token, role)`

Check if token has a specific role.

##### `has_any_scope(decoded_token, scopes)`

Check if token has any of the specified scopes.

##### `has_all_scopes(decoded_token, scopes)`

Check if token has all of the specified scopes.

## Usage in Other Projects

### Installing in employee_manage

```bash
cd /path/to/micro_service/employee_manage
pip install /path/to/hub_auth
```

Or add to `requirements.txt`:

```
# From local path
/path/to/hub_auth

# Or from Git
git+https://github.com/your-org/hub-auth-client.git@main

# Or from PyPI (if published)
hub-auth-client>=1.0.0
```

### Example Integration

```python
# In employee_manage/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
    ],
}

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')

# In views.py
from rest_framework.views import APIView
from hub_auth_client.django import HasScopes

class EmployeeListView(APIView):
    permission_classes = [HasScopes(['Employee.Read'])]
    
    def get(self, request):
        # User is authenticated and has Employee.Read scope
        employees = Employee.objects.all()
        return Response(EmployeeSerializer(employees, many=True).data)
```

## Testing

Run tests:

```bash
pytest
```

With coverage:

```bash
pytest --cov=hub_auth_client --cov-report=html
```

## Development

### Install in editable mode

```bash
pip install -e .
```

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Format code

```bash
black hub_auth_client
```

### Lint

```bash
flake8 hub_auth_client
```

## Common Issues

### "Token has expired"

Tokens typically expire after 1 hour. Get a new token from your authentication flow.

### "Invalid audience"

Ensure `AZURE_AD_CLIENT_ID` matches the `aud` claim in your token.

### "Token from wrong tenant"

Ensure `AZURE_AD_TENANT_ID` matches the `tid` claim in your token.

### "Missing required scopes"

Ensure:
1. Scopes are configured in Azure AD app registration
2. User has consented to the scopes
3. Token includes the scopes in `scp` or `scopes` claim

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please submit pull requests or open issues.

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: your-email@example.com
