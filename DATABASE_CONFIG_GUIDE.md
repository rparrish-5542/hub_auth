# Database Configuration Guide

This guide explains how to use database-driven configuration instead of environment variables.

## Why Use Database Configuration?

**Benefits:**
- ✅ **Cleaner Deployment**: No `.env` files to manage
- ✅ **Multiple Environments**: Easily switch between dev/staging/prod
- ✅ **Audit Trail**: Track all configuration changes with history
- ✅ **Same Package Everywhere**: No code changes between projects
- ✅ **Admin-Friendly**: Non-developers can update credentials
- ✅ **Test Configurations**: Test settings before activating

## Quick Start

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps ...
    
    'hub_auth_client.django',  # Add this
    
    # ... your apps ...
]
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure via Django Admin

1. Go to Django admin: `http://localhost:8000/admin/`
2. Navigate to **Hub Auth Client** → **Azure AD Configurations**
3. Click **Add Azure AD Configuration**
4. Fill in your Azure AD credentials
5. Check **Is Active**
6. Click **Save**

Done! No environment variables needed.

## Configuration Fields

### Basic Settings

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| **Name** | Yes | Configuration name | `Production` or `Development` |
| **Tenant ID** | Yes | Azure AD Tenant ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| **Client ID** | Yes | Azure AD Application ID | `f9e8d7c6-b5a4-3210-fedc-ba9876543210` |
| **Client Secret** | No | For service-to-service auth | (leave blank for user auth) |
| **Is Active** | Yes | Only one can be active | ✓ (checked) |

### Token Validation Settings

| Field | Default | Description |
|-------|---------|-------------|
| **Token Version** | `2.0` | Azure AD token version (`1.0` or `2.0`) |
| **Validate Audience** | ✓ | Verify token `aud` claim matches client ID |
| **Validate Issuer** | ✓ | Verify token `iss` claim is from Azure AD |
| **Token Leeway** | `0` | Seconds of leeway for expiration (0-300) |
| **Allowed Audiences** | `[client_id]` | JSON array of allowed `aud` values |

### Exempt Paths

URLs that don't require authentication:

```json
["/admin/", "/health/", "/api/docs/"]
```

## Django Admin Features

### Configuration Management

**List View:**
- See all configurations at a glance
- Active config highlighted in green
- Short tenant/client IDs for privacy
- Validation badges (AUD, ISS, Leeway)

**Admin Actions:**
1. **Activate Configuration**: Make a config active (deactivates others)
2. **Test Configuration**: Verify credentials connect to Azure AD

### Configuration History

Every change is tracked:
- Who made the change
- When it was made
- What action was taken (created, updated, activated, deactivated)
- Tenant and client IDs for reference

View history at: **Azure AD Configurations** → click a config → **History** tab

## How It Works

### Authentication Flow

1. Request comes in with JWT token
2. `MSALAuthentication` checks for active database config
3. If found, uses those credentials
4. If not found, falls back to `settings.py` variables
5. Token is validated against Azure AD
6. User is authenticated

### Fallback to Environment Variables

If no active database config exists, it falls back to:

```python
# settings.py
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
MSAL_VALIDATE_AUDIENCE = True
MSAL_VALIDATE_ISSUER = True
MSAL_TOKEN_LEEWAY = 0
MSAL_EXEMPT_PATHS = ['/admin/', '/health/']
```

This ensures backward compatibility with existing projects.

## Common Scenarios

### Multiple Environments

Create configurations for each environment:

```
Development  (Inactive)  - dev.azure.com tenant
Staging      (Inactive)  - staging.azure.com tenant
Production   (Active)    - prod.azure.com tenant
```

To switch environments, just activate a different config in admin.

### Rotating Credentials

When Azure AD credentials change:

1. Create a new configuration with new credentials
2. Test it using **Test Configuration** action
3. Activate it using **Activate Configuration** action
4. Old config is automatically deactivated
5. History shows who made the change and when

### Multiple Tenants

For multi-tenant apps:

```
Tenant A - Customer Corp  (Active)
Tenant B - Partner Inc    (Inactive)
Tenant C - Client LLC     (Inactive)
```

Switch tenants by activating the appropriate config.

## Migration from Environment Variables

### Step 1: Current Setup (Environment Variables)

```python
# settings.py
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
```

```env
# .env
AZURE_AD_TENANT_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
AZURE_AD_CLIENT_ID=f9e8d7c6-b5a4-3210-fedc-ba9876543210
```

### Step 2: Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps ...
    'hub_auth_client.django',
]
```

### Step 3: Run Migrations

```bash
python manage.py migrate
```

### Step 4: Create Database Config

1. Go to Django admin
2. Create Azure AD Configuration with your credentials
3. Activate it

### Step 5: Remove Environment Variables (Optional)

Once database config is active:

1. Remove `.env` variables
2. Remove `AZURE_AD_*` from `settings.py`
3. Keep `hub_auth_client.django` in INSTALLED_APPS

The authentication will automatically use database config.

## Testing Configurations

### Test Before Activating

1. Create a new configuration
2. Leave **Is Active** unchecked
3. Save it
4. Select it in admin
5. Actions → **Test Configuration**
6. If successful, activate it

### What "Test Configuration" Does

- Creates MSALTokenValidator with config
- Attempts to fetch Azure AD signing keys
- Verifies connectivity to Azure AD
- Reports any errors

## Security Considerations

### Database Security

Azure AD credentials are stored in your database. Ensure:

- ✅ Database backups are encrypted
- ✅ Only authorized users can access Django admin
- ✅ Database access is restricted
- ✅ Consider encrypting client secrets (future feature)

### Who Can Modify Configurations?

Only Django admin users with these permissions:

- `hub_auth_client.add_azureadconfiguration`
- `hub_auth_client.change_azureadconfiguration`
- `hub_auth_client.delete_azureadconfiguration`

Superusers have all permissions by default.

### Audit Trail

Every change is logged in `AzureADConfigurationHistory`:

- Configuration created
- Configuration updated
- Configuration activated
- Configuration deactivated
- Configuration deleted

You can see who made changes and when.

## Troubleshooting

### "No active configuration found"

**Cause**: No configuration is marked as active.

**Solution**: Go to admin and activate a configuration.

### "Multiple active configurations found"

**Cause**: Database constraint failed (shouldn't happen).

**Solution**: 
1. Go to admin
2. Deactivate all configs
3. Activate only one

### "Invalid tenant_id format"

**Cause**: Tenant ID is not a valid GUID.

**Solution**: Ensure format is: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### "Token validation fails"

**Possible causes:**
- Client ID doesn't match token `aud` claim
- Tenant ID doesn't match token `iss` claim
- Token expired and leeway is 0
- Wrong token version configured

**Solution**: Use **Test Configuration** action to verify settings.

## API Reference

### Get Active Configuration

```python
from hub_auth_client.django import AzureADConfiguration

config = AzureADConfiguration.get_active_config()
if config:
    print(f"Using config: {config.name}")
    print(f"Tenant: {config.tenant_id}")
```

### Get Validator from Config

```python
from hub_auth_client.django import AzureADConfiguration

config = AzureADConfiguration.get_active_config()
if config:
    validator = config.get_validator()
    is_valid, claims, error = validator.validate_token(token)
```

### Check if Config Available

```python
from hub_auth_client.django import CONFIG_AVAILABLE

if CONFIG_AVAILABLE:
    # Database config models are available
    from hub_auth_client.django import AzureADConfiguration
```

## Best Practices

### 1. Always Test First

Before activating a new configuration:
1. Create it as inactive
2. Test it using admin action
3. Only activate if test passes

### 2. Use Descriptive Names

Good names:
- `Production - Azure AD`
- `Development - Local Testing`
- `Staging - Pre-Production`

Bad names:
- `Config 1`
- `Test`
- `New`

### 3. Document Changes

Use the **Description** field:

```
Updated client secret after rotation on 2024-12-08.
New secret expires 2025-12-08.
```

### 4. Regular Audits

Periodically review:
- Active configuration is correct
- Inactive configurations can be deleted
- History shows no unauthorized changes

### 5. Backup Database

Since credentials are in database:
- Regular automated backups
- Test restore process
- Encrypt backup files

## Example: Complete Setup

```bash
# 1. Add to settings
# Edit settings.py and add 'hub_auth_client.django' to INSTALLED_APPS

# 2. Run migrations
python manage.py migrate

# 3. Start server
python manage.py runserver

# 4. Go to admin
# http://localhost:8000/admin/

# 5. Create configuration
# Hub Auth Client > Azure AD Configurations > Add
# Name: Production
# Tenant ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# Client ID: f9e8d7c6-b5a4-3210-fedc-ba9876543210
# Is Active: ✓

# 6. Test it
# Select the configuration
# Actions > Test Configuration

# 7. Done!
# Authentication now uses database config
```

## Support

- Full documentation: See `README.md`
- Installation guide: See `INSTALL_IN_EMPLOYEE_MANAGE.md`
- RLS guide: See `RLS_GUIDE.md`
