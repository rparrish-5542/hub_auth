# Hub-Auth-Client Management Commands

These Django management commands help you discover and secure your API endpoints.

## Commands Overview

### 1. `list_endpoints` - Discover All API Endpoints

Lists all available views, URLs, serializers, and their current security configuration.

**Basic Usage:**
```bash
python manage.py list_endpoints
```

**Output Example:**
```
Found 45 endpoints:

URL Pattern                                          Methods              View                           Permissions                   
-------------------------------------------------------------------------------------------------------------------------
^admin/                                              GET,POST             AdminSite                      IsAdminUser                   
^api/employees/$                                     GET,POST             EmployeeListView               NONE                          
  → List and create employees
^api/employees/(?P<pk>[^/.]+)/$                      GET,PUT,DELETE       EmployeeDetailView             IsAuthenticated               
  → Retrieve, update, delete employee

⚠ Warning: 12 endpoints have no permission classes!
Consider securing them with scopes/roles using EndpointPermission.
```

**Advanced Options:**

```bash
# Show only unsecured endpoints
python manage.py list_endpoints --unsecured-only

# Filter by app
python manage.py list_endpoints --app=employees

# Show serializer information
python manage.py list_endpoints --show-serializers

# JSON output
python manage.py list_endpoints --format=json

# CSV output for Excel
python manage.py list_endpoints --format=csv > endpoints.csv
```

**With Serializers:**
```bash
python manage.py list_endpoints --show-serializers
```
Shows which serializer is used by each view and its fields.

---

### 2. `fetch_azure_scopes` - Sync Scopes from Azure AD

Fetches all available scopes from your Azure AD App Registration and optionally imports them into Django.

**Basic Usage:**
```bash
# View scopes
python manage.py fetch_azure_scopes

# Import scopes into database
python manage.py fetch_azure_scopes --import
```

**Output Example:**
```
Authenticating with Azure AD...
Fetching application details from Microsoft Graph...

Found 15 scopes in Azure AD:

Scope Name                               Category        Type            Enabled   
--------------------------------------------------------------------------------------
Employee.Read                            delegated       oauth2          ✓         
  → Read employee information
Employee.Write                           delegated       oauth2          ✓         
  → Create and update employees
Employee.Delete                          application     app_role        ✓         
  → Delete employees (admin only)

Summary:
  delegated: 8
  application: 5
  required: 2
```

**Configuration Options:**

**Option 1: Database Configuration (Recommended)**
```python
# Configure via Django admin or shell
from hub_auth_client.django.config_models import AzureADConfiguration

AzureADConfiguration.objects.create(
    name="Production",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    is_active=True
)
```

**Option 2: Django Settings**
```python
# settings.py
AZURE_AD_TENANT_ID = "your-tenant-id"
AZURE_AD_CLIENT_ID = "your-client-id"
AZURE_AD_CLIENT_SECRET = "your-client-secret"
```

**Option 3: Command Line**
```bash
python manage.py fetch_azure_scopes \
    --tenant-id="your-tenant-id" \
    --client-id="your-client-id" \
    --client-secret="your-client-secret"
```

**Import to Database:**
```bash
python manage.py fetch_azure_scopes --import
```
This creates/updates `ScopeDefinition` objects for each scope found in Azure AD.

**JSON Output:**
```bash
python manage.py fetch_azure_scopes --format=json > azure_scopes.json
```

---

## Workflow: Securing Your API

### Step 1: Discover Endpoints
```bash
# Find all unsecured endpoints
python manage.py list_endpoints --unsecured-only
```

### Step 2: Fetch Azure Scopes
```bash
# Import scopes from Azure AD
python manage.py fetch_azure_scopes --import
```

### Step 3: Create Endpoint Permissions

**Via Django Admin:**
1. Go to `/admin/hub_auth_client/endpointpermission/`
2. Click "Add Endpoint Permission"
3. Configure:
   - **Name**: "Employee List Access"
   - **URL Pattern**: `^api/employees/$`
   - **HTTP Methods**: GET, POST
   - **Required Scopes**: Select "Employee.Read", "Employee.Write"
   - **Scope Requirement**: ANY (user needs at least one)

**Via Django Shell:**
```python
from hub_auth_client.django.models import EndpointPermission, ScopeDefinition

# Get scopes
read_scope = ScopeDefinition.objects.get(name="Employee.Read")
write_scope = ScopeDefinition.objects.get(name="Employee.Write")

# Create permission
permission = EndpointPermission.objects.create(
    name="Employee List Access",
    url_pattern=r"^api/employees/$",
    http_methods="GET,POST",
    scope_requirement="any",
    is_active=True
)
permission.required_scopes.add(read_scope, write_scope)
```

### Step 4: Verify
```bash
# Check that endpoint is now secured
python manage.py list_endpoints --app=employees
```

---

## Use Cases

### Use Case 1: API Audit
```bash
# Export all endpoints to CSV for security review
python manage.py list_endpoints --format=csv > api_audit.csv

# Share with security team
# They can review which endpoints need protection
```

### Use Case 2: Sync Production Scopes
```bash
# Fetch scopes from production Azure AD
python manage.py fetch_azure_scopes \
    --tenant-id="prod-tenant-id" \
    --client-id="prod-client-id" \
    --client-secret="prod-secret" \
    --import

# Creates ScopeDefinition objects matching production
```

### Use Case 3: Find Unsecured Admin Endpoints
```bash
# Find admin endpoints without protection
python manage.py list_endpoints --unsecured-only | grep admin
```

### Use Case 4: Verify API Documentation
```bash
# Export endpoints with serializers for API documentation
python manage.py list_endpoints --show-serializers --format=json > api_docs.json
```

---

## Advanced Examples

### Compare Local Scopes with Azure AD
```bash
# Local scopes
python manage.py shell -c "
from hub_auth_client.django.models import ScopeDefinition
print('Local scopes:', list(ScopeDefinition.objects.values_list('name', flat=True)))
"

# Azure scopes
python manage.py fetch_azure_scopes --format=json | jq '.[].name'
```

### Bulk Create Endpoint Permissions
```python
# management/commands/secure_all_endpoints.py
from django.core.management.base import BaseCommand
from hub_auth_client.django.models import EndpointPermission, ScopeDefinition
import subprocess
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get all endpoints
        result = subprocess.run(
            ['python', 'manage.py', 'list_endpoints', '--format=json'],
            capture_output=True,
            text=True
        )
        endpoints = json.loads(result.stdout)
        
        # Get default scope
        read_scope = ScopeDefinition.objects.get(name="Employee.Read")
        
        # Create permissions for unsecured endpoints
        for endpoint in endpoints:
            if not endpoint['permission_classes']:
                EndpointPermission.objects.get_or_create(
                    url_pattern=endpoint['url_pattern'],
                    defaults={
                        'name': f"Auto: {endpoint['view_name']}",
                        'http_methods': ','.join(endpoint['methods']),
                        'is_active': True
                    }
                )
```

---

## Troubleshooting

### Error: "Azure AD configuration not found"
**Solution:** Configure Azure AD credentials using one of the three methods above.

### Error: "Application not found for Client ID"
**Solution:** Verify your client ID is correct. Check Azure Portal > App registrations.

### Error: "No scopes found in Azure AD"
**Solution:** 
1. Go to Azure Portal > App registrations > Your app
2. Navigate to "Expose an API"
3. Add scopes under "Scopes defined by this API"

### Empty endpoint list
**Solution:** 
- Ensure your Django app is properly configured
- Check that URL patterns are included in root `urls.py`
- Try: `python manage.py show_urls` to verify URLs are registered

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Security Audit

on: [push]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Check for unsecured endpoints
        run: |
          UNSECURED=$(python manage.py list_endpoints --unsecured-only --format=json | jq length)
          if [ "$UNSECURED" -gt "0" ]; then
            echo "::error::Found $UNSECURED unsecured endpoints"
            exit 1
          fi
```

---

## Next Steps

After discovering endpoints and scopes:

1. **Review Unsecured Endpoints**
   ```bash
   python manage.py list_endpoints --unsecured-only
   ```

2. **Import Azure Scopes**
   ```bash
   python manage.py fetch_azure_scopes --import
   ```

3. **Configure Endpoint Permissions** in Django admin

4. **Test Authentication** with MSAL tokens

5. **Monitor** scope usage via Django admin

---

## Support

For issues or questions:
- **GitHub**: https://github.com/rparrish-5542/hub_auth
- **PyPI**: https://pypi.org/project/hub-auth-client/
