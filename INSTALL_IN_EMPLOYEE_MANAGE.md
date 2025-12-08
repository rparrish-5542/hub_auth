# Installing hub-auth-client in employee_manage

This guide shows you exactly how to install and configure hub-auth-client in the employee_manage project.

## Step 1: Build hub-auth-client Package

```powershell
# Navigate to hub_auth
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# Run the build script (easiest method)
.\build_and_install.ps1

# Or manually:
pip install build wheel
python -m build
```

## Step 2: Install in employee_manage

```powershell
# Navigate to employee_manage
cd c:\Users\rparrish\GitHub\micro_service\employee_manage

# Install the package
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth

# Or for development (changes to hub_auth_client apply immediately):
pip install -e c:\Users\rparrish\GitHub\micro_service\hub_auth

# Verify installation
python -c "import hub_auth_client; print(hub_auth_client.__version__)"
```

## Step 3: Update requirements.txt

Add to `employee_manage/requirements.txt`:

```txt
# MSAL JWT Authentication
hub-auth-client @ file:///c:/Users/rparrish/GitHub/micro_service/hub_auth

# Or for editable install:
-e c:\Users\rparrish\GitHub\micro_service\hub_auth
```

## Step 4: Update Django Settings

Edit `employee_manage/employee_manage/settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ... existing settings ...

# ============================================================================
# INSTALLED APPS - Add hub_auth_client.django
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add hub_auth_client Django app
    'hub_auth_client.django',
    
    # ... your other apps ...
    'rest_framework',
]

# ============================================================================
# AZURE AD / MSAL CONFIGURATION (OPTIONAL - Can use database config instead)
# ============================================================================

# Option 1: Environment variables (traditional approach)
# AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
# AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')

# Option 2: Configure via Django admin (RECOMMENDED)
# After running migrations, go to Django admin > Azure AD Configurations
# and create your configuration there. No environment variables needed!

# ============================================================================
# REST FRAMEWORK - UPDATE AUTHENTICATION
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # ... rest of your DRF settings ...
}
```

## Step 5: Run Migrations

```powershell
cd c:\Users\rparrish\GitHub\micro_service\employee_manage

# Run migrations to create hub_auth_client tables
python manage.py migrate

# Create superuser if you don't have one
python manage.py createsuperuser
```

## Step 6: Configure Azure AD Credentials

You have **two options** for configuring Azure AD credentials:

### Option A: Django Admin (RECOMMENDED - Cleaner Deployment)

1. Start the development server:
   ```powershell
   python manage.py runserver
   ```

2. Go to [http://localhost:8000/admin/](http://localhost:8000/admin/)

3. Navigate to **Hub Auth Client** → **Azure AD Configurations**

4. Click **Add Azure AD Configuration**

5. Fill in the form:
   - **Name**: `Production` (or `Development`)
   - **Tenant ID**: Your Azure AD Tenant ID (GUID format)
   - **Client ID**: Your Azure AD Application ID (GUID format)
   - **Client Secret**: (Optional, for service-to-service auth)
   - **Token Version**: `2.0` (default)
   - **Validate Audience**: ✓ (checked)
   - **Validate Issuer**: ✓ (checked)
   - **Exempt Paths**: `["/admin/", "/health/"]`
   - **Is Active**: ✓ (checked)

6. Click **Save**

**Benefits:**
- No `.env` files needed
- Easy to switch between environments
- Configuration history tracking
- Test configurations directly in admin
- Same package works across all projects

### Option B: Environment Variables (Traditional)

Edit `employee_manage/.env`:

```env
# Azure AD Configuration
AZURE_AD_TENANT_ID=your-tenant-id-here
AZURE_AD_CLIENT_ID=your-client-id-here

# ... rest of your environment variables ...
```

Then update `settings.py`:

```python
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
MSAL_VALIDATE_AUDIENCE = True
MSAL_VALIDATE_ISSUER = True
MSAL_TOKEN_LEEWAY = 0
MSAL_EXEMPT_PATHS = ['/admin/', '/health/', '/api/docs/']
```

## Step 7: Update Views with Scope-Based Permissions

### Example 1: Simple Scope Requirement

```python
# employee_manage/app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import HasScopes

class EmployeeListView(APIView):
    """List employees - requires Employee.Read scope."""
    
    permission_classes = [HasScopes(['Employee.Read'])]
    
    def get(self, request):
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)
```

### Example 2: Multiple Scopes (Any)

```python
class EmployeeManageView(APIView):
    """Manage employees - requires Employee.Read OR Employee.Write scope."""
    
    permission_classes = [HasScopes(['Employee.Read', 'Employee.Write'])]
    
    def get(self, request):
        # User has at least one of the scopes
        employees = Employee.objects.all()
        return Response(EmployeeSerializer(employees, many=True).data)
```

### Example 3: Multiple Scopes (All)

```python
from hub_auth_client.django import HasAllScopes

class EmployeeFullAccessView(APIView):
    """Full access - requires BOTH Employee.Read AND Employee.Write scopes."""
    
    permission_classes = [HasAllScopes(['Employee.Read', 'Employee.Write'])]
    
    def post(self, request):
        # User must have both scopes
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
```

### Example 4: Role-Based Access

```python
from hub_auth_client.django import HasRoles

class AdminOnlyView(APIView):
    """Admin only - requires Admin role."""
    
    permission_classes = [HasRoles(['Admin'])]
    
    def get(self, request):
        return Response({'message': 'Admin access granted'})
```

### Example 5: Function-Based Views

```python
from hub_auth_client.django import require_scopes, require_roles

@require_scopes(['Employee.Read'])
def employee_list(request):
    """Function-based view with scope requirement."""
    employees = Employee.objects.all()
    return JsonResponse({
        'employees': list(employees.values())
    })

@require_roles(['Manager', 'Admin'])
def management_dashboard(request):
    """Function-based view with role requirement."""
    return JsonResponse({
        'message': 'Management access granted',
        'user': request.msal_user['name']
    })
```

## Step 7: Configure Azure AD

### Register Scopes in Azure AD

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Select your application
4. Go to **Expose an API**
5. Add scopes:
   - `Employee.Read`
   - `Employee.Write`
   - `Employee.Delete`
   - etc.

### Register App Roles

1. In your app registration, go to **App roles**
2. Create roles:
   - `Admin`
   - `Manager`
   - `User`
   - `HR`
   - etc.
3. Assign users to roles in **Enterprise Applications**

## Step 8: Test the Integration

### Test with Postman

1. Get a token from MSAL authentication
2. Make a request to your endpoint:

```http
GET http://localhost:8000/api/employees/
Authorization: Bearer <your-msal-token>
```

### Test Token Validation

```python
# employee_manage/test_auth.py
from hub_auth_client import MSALTokenValidator

validator = MSALTokenValidator(
    tenant_id="your-tenant-id",
    client_id="your-client-id"
)

token = "your-test-token"
is_valid, claims, error = validator.validate_token(
    token,
    required_scopes=['Employee.Read']
)

if is_valid:
    print("✓ Token is valid!")
    print(f"User: {claims['upn']}")
    print(f"Scopes: {claims.get('scp', '').split()}")
else:
    print(f"✗ Token invalid: {error}")
```

## Step 9: Update URLs (if needed)

If you want to use the example views:

```python
# employee_manage/employee_manage/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/employees/', include('employees.urls')),
    # ... other URLs ...
]
```

## Common Issues and Solutions

### Issue: "Module not found: hub_auth_client"

**Solution:**
```powershell
pip uninstall hub-auth-client
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth
```

### Issue: "AZURE_AD_TENANT_ID must be set"

**Solution:**
1. Verify `.env` file exists in employee_manage directory
2. Ensure it contains `AZURE_AD_TENANT_ID` and `AZURE_AD_CLIENT_ID`
3. Load in settings: `load_dotenv()`

### Issue: "Invalid audience"

**Solution:**
- Ensure `AZURE_AD_CLIENT_ID` matches the `aud` claim in your token
- Check your token at [jwt.io](https://jwt.io)

### Issue: "Missing required scopes"

**Solution:**
1. Verify scopes are configured in Azure AD
2. Request scopes in your frontend authentication
3. Check token has scopes in `scp` or `scopes` claim

## Migration from Old Auth

If employee_manage was using a different auth method:

### 1. Keep Old Auth for Transition

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',  # New
        'your.old.AuthenticationClass',  # Old - keep during transition
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### 2. Gradually Update Views

Update views one at a time to use scope-based permissions:

```python
# Old (token-based only)
permission_classes = [IsAuthenticated]

# New (scope-based RBAC)
permission_classes = [HasScopes(['Employee.Read'])]
```

### 3. Remove Old Auth

Once all views are updated and tested, remove old authentication classes.

## Verification Checklist

- [ ] Package built successfully
- [ ] Package installed in employee_manage
- [ ] `hub_auth_client.django` added to INSTALLED_APPS
- [ ] Migrations run successfully
- [ ] Azure AD credentials configured (via admin OR .env)
- [ ] Django settings updated
- [ ] At least one view updated to use scope-based permissions
- [ ] Token validation tested
- [ ] Scopes configured in Azure AD
- [ ] Users assigned appropriate scopes/roles
- [ ] All tests passing

## Next Steps

1. Test with real MSAL tokens from your frontend
2. Update all views to use scope-based permissions
3. Configure appropriate scopes and roles in Azure AD
4. Document which scopes are required for each endpoint
5. Consider using the same package in other microservices

## Support

- See `c:\Users\rparrish\GitHub\micro_service\hub_auth\README_PACKAGE.md` for full documentation
- See `c:\Users\rparrish\GitHub\micro_service\hub_auth\examples\` for more examples
- Check `c:\Users\rparrish\GitHub\micro_service\hub_auth\INSTALLATION.md` for troubleshooting
