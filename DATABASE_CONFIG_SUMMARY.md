# Database Configuration - Quick Summary

## What Is This?

Store your Azure AD credentials (Tenant ID, Client ID) in your Django database instead of environment variables.

## Why?

✅ **No `.env` files to manage**  
✅ **Same package across all environments**  
✅ **Switch configurations via Django admin**  
✅ **Track who changed what and when**  
✅ **Test configurations before activating**

## How?

### 1. Add to settings.py

```python
INSTALLED_APPS = [
    # ... other apps ...
    'hub_auth_client.django',
]
```

### 2. Run migrations

```bash
python manage.py migrate
```

### 3. Configure via admin

1. Go to `http://localhost:8000/admin/`
2. Navigate to **Azure AD Configurations**
3. Click **Add Azure AD Configuration**
4. Fill in your credentials
5. Check **Is Active**
6. Save

Done! No environment variables needed.

## What You Configure

| Field | Description | Example |
|-------|-------------|---------|
| Name | Config name | `Production` |
| Tenant ID | Azure AD Tenant ID | `a1b2c3d4-...` |
| Client ID | Application ID | `f9e8d7c6-...` |
| Is Active | Make it active | ✓ |

## Features

### Django Admin

- **List view**: See all configurations
- **Test action**: Verify credentials work
- **Activate action**: Switch active config
- **History**: See who changed what

### Automatic Fallback

If no database config exists, falls back to:

```python
# settings.py
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
```

This ensures backward compatibility.

### Multiple Environments

```
Development  (Inactive)
Staging      (Inactive)  
Production   (Active)    ← Currently using this
```

Switch by activating a different config.

## Example

**Before (environment variables):**

```env
# .env
AZURE_AD_TENANT_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
AZURE_AD_CLIENT_ID=f9e8d7c6-b5a4-3210-fedc-ba9876543210
```

```python
# settings.py
AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
```

**After (database config):**

```python
# settings.py
INSTALLED_APPS = [
    'hub_auth_client.django',  # Just add this
]
```

Then configure via Django admin. No `.env` needed!

## Full Guide

See [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md) for complete documentation.

## Installation Guide

See [INSTALL_IN_EMPLOYEE_MANAGE.md](INSTALL_IN_EMPLOYEE_MANAGE.md) for step-by-step instructions.
