# Hub Auth Client - Installation Guide

This guide provides step-by-step instructions for installing and using the `hub-auth-client` package in your Django projects.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Quick Start](#quick-start)
4. [Integrating with Existing Projects](#integrating-with-existing-projects)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- Django 4.2 or higher (for Django integration)
- Azure AD tenant with application registration
- Active Azure AD account

## Installation Methods

### Method 1: Install from Local Directory (Development)

If you're developing or testing locally:

```bash
# Navigate to your project
cd /path/to/your/project

# Install from local hub_auth directory
pip install /path/to/hub_auth

# Or install in editable mode for development
pip install -e /path/to/hub_auth
```

### Method 2: Install from Git Repository

```bash
pip install git+https://github.com/your-org/hub-auth-client.git@main
```

### Method 3: Install from PyPI (if published)

```bash
pip install hub-auth-client
```

### Method 4: Install with Django Support

```bash
pip install hub-auth-client[django]
```

## Quick Start

### 1. Build the Package (First Time Only)

```bash
# Navigate to hub_auth directory
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# Install build tools
pip install build wheel

# Build the package
python -m build

# This creates:
# - dist/hub_auth_client-1.0.0-py3-none-any.whl
# - dist/hub_auth_client-1.0.0.tar.gz
```

### 2. Install in Your Project

```bash
# Install the built wheel
pip install dist/hub_auth_client-1.0.0-py3-none-any.whl

# Or install directly from source
pip install .
```

### 3. Verify Installation

```python
python -c "import hub_auth_client; print(hub_auth_client.__version__)"
# Should print: 1.0.0
```

## Integrating with Existing Projects

### For employee_manage Project

```bash
# Navigate to employee_manage
cd c:\Users\rparrish\GitHub\micro_service\employee_manage

# Install hub-auth-client
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth

# Or add to requirements.txt
echo "hub-auth-client @ file:///c:/Users/rparrish/GitHub/micro_service/hub_auth" >> requirements.txt
pip install -r requirements.txt
```

### Update employee_manage Settings

Edit `employee_manage/settings.py`:

```python
# Add Azure AD configuration
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')

# Update REST_FRAMEWORK settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Update employee_manage Views

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import HasScopes

class EmployeeListView(APIView):
    permission_classes = [HasScopes(['Employee.Read'])]
    
    def get(self, request):
        # User is authenticated with Employee.Read scope
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)
```

## Configuration

### Azure AD Setup

1. **Register Application in Azure AD**
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to **Azure Active Directory** → **App registrations**
   - Click **New registration**
   - Note the **Application (client) ID** and **Directory (tenant) ID**

2. **Configure API Permissions (Scopes)**
   - Go to **API permissions**
   - Add Microsoft Graph permissions: `User.Read`, `Files.ReadWrite`, etc.
   - Grant admin consent if required

3. **Configure App Roles**
   - Go to **App roles**
   - Create roles: `Admin`, `Manager`, `User`, etc.
   - Assign users to roles in **Enterprise Applications**

### Environment Variables

Create `.env` file in your project:

```env
# Azure AD
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here

# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=your_database
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Load in Django settings:

```python
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
```

## Testing

### Run Package Tests

```bash
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# Install test dependencies
pip install -r tests/requirements-test.txt

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=hub_auth_client --cov-report=html

# View coverage report
start htmlcov/index.html
```

### Test in Your Project

```python
# Test token validation
from hub_auth_client import MSALTokenValidator

validator = MSALTokenValidator(
    tenant_id="your-tenant-id",
    client_id="your-client-id"
)

token = "your-test-token"
is_valid, claims, error = validator.validate_token(token)

if is_valid:
    print("Token is valid!")
    print(f"User: {claims['upn']}")
else:
    print(f"Token invalid: {error}")
```

## Troubleshooting

### "Module not found: hub_auth_client"

**Solution:**
```bash
# Reinstall the package
pip uninstall hub-auth-client
pip install /path/to/hub_auth

# Or use editable install
pip install -e /path/to/hub_auth
```

### "AZURE_AD_TENANT_ID must be set"

**Solution:**
- Ensure `.env` file exists and contains `AZURE_AD_TENANT_ID`
- Load environment variables in settings: `load_dotenv()`
- Verify environment variables are loaded: `print(os.getenv('AZURE_AD_TENANT_ID'))`

### "Invalid audience" Error

**Solution:**
- Verify `AZURE_AD_CLIENT_ID` matches the `aud` claim in your token
- Check token audience: Decode token at [jwt.io](https://jwt.io)
- Ensure you're using the correct client ID from Azure AD app registration

### "Token has expired"

**Solution:**
- Tokens typically expire after 1 hour
- Get a new token from your authentication flow
- Consider implementing token refresh logic

### "Missing required scopes"

**Solution:**
1. Configure scopes in Azure AD app registration
2. Ensure user has consented to scopes
3. Request scopes in your authentication flow
4. Verify token contains scopes: Decode at [jwt.io](https://jwt.io)

### Package Build Errors

**Solution:**
```bash
# Upgrade build tools
pip install --upgrade build wheel setuptools

# Clean previous builds
rm -rf build dist *.egg-info

# Rebuild
python -m build
```

## Updating the Package

When you make changes to hub_auth_client:

```bash
# Rebuild the package
cd c:\Users\rparrish\GitHub\micro_service\hub_auth
python -m build

# Reinstall in your project
cd /path/to/your/project
pip install --upgrade --force-reinstall c:\Users\rparrish\GitHub\micro_service\hub_auth
```

Or with editable install (changes apply immediately):

```bash
pip install -e c:\Users\rparrish\GitHub\micro_service\hub_auth
```

## Publishing to PyPI (Optional)

If you want to publish to PyPI:

```bash
# Install twine
pip install twine

# Build package
python -m build

# Upload to TestPyPI (testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
python -m twine upload dist/*
```

Then install from PyPI:

```bash
pip install hub-auth-client
```

## Support

For issues and questions:
- Check the [README_PACKAGE.md](README_PACKAGE.md) for detailed documentation
- Review examples in `examples/` directory
- Open an issue on GitHub
- Contact: your-email@example.com
