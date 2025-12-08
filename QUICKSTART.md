# Quick Start - Installing hub-auth-client

## Build and Install

```powershell
# 1. Navigate to hub_auth directory
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# 2. Install build tools (if not already installed)
pip install build wheel

# 3. Build the package
python -m build

# 4. Install the package
pip install dist/hub_auth_client-1.0.0-py3-none-any.whl
```

## Install in Other Projects

### For employee_manage:

```powershell
cd c:\Users\rparrish\GitHub\micro_service\employee_manage
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth
```

### For other projects:

```powershell
cd /path/to/your/project
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth
```

## Configuration

Add to your Django `settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Azure AD Configuration
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

Create `.env` file:

```env
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here
```

## Usage Example

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import HasScopes

class MyView(APIView):
    permission_classes = [HasScopes(['User.Read'])]
    
    def get(self, request):
        return Response({
            'user': request.user.username,
            'scopes': request.user.scopes,
        })
```

## Documentation

- **[README_PACKAGE.md](README_PACKAGE.md)** - Full package documentation
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation guide
- **[examples/](examples/)** - Example configurations and usage

## Testing

```powershell
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run tests
pytest tests/
```
