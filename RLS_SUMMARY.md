# RLS Integration Summary

## What Was Added

Hub Auth Client now supports **PostgreSQL Row-Level Security (RLS)**, allowing you to enforce data access rules at the database level based on Azure AD scopes and roles.

## ✨ New Components

### 1. RLS Models (`rls_models.py`)

**RLSPolicy**
- Define RLS policies for database tables
- Configure scope/role requirements
- Auto-generate PostgreSQL policy SQL
- Apply/remove policies via Django admin

**RLSTableConfig**
- Enable/disable RLS per table
- Configure session variables to set
- Custom variable mapping support

### 2. RLS Middleware (`rls_middleware.py`)

**RLSMiddleware**
- Automatically sets PostgreSQL session variables from MSAL token
- Extracts user ID, email, scopes, roles, tenant ID
- Supports custom session variables
- Transparent to application code

**RLSDebugMiddleware**
- Logs session variables for debugging
- Helps troubleshoot RLS policies

### 3. Django Admin Integration (`admin.py`)

**RLSPolicyAdmin**
- Visual policy editor
- SQL preview before applying
- Bulk actions: Apply/Remove policies
- Scope/Role filtering with badges

**RLSTableConfigAdmin**
- Enable/Disable RLS per table
- Configure session variables
- View active policies per table

### 4. Management Command (`manage_rls.py`)

```bash
python manage.py manage_rls --help
python manage.py manage_rls --apply-all
python manage.py manage_rls --preview
python manage.py manage_rls --enable-table employee_employee
```

### 5. Documentation

- [RLS_GUIDE.md](RLS_GUIDE.md) - Complete 400+ line guide
- Examples for common patterns
- Security best practices
- Debugging techniques

## 🎯 Key Benefits

### Database-Enforced Security
- Can't be bypassed by buggy application code
- PostgreSQL validates every query
- Audit trail at database level

### Admin-Configurable
- No code changes needed to adjust policies
- Define policies through Django admin
- Apply/remove with one click

### Performance
- PostgreSQL optimizes RLS constraints
- More efficient than application-level filtering
- Indexes work with RLS policies

### Scope/Role Integration
- Seamlessly integrates with existing MSAL scopes/roles
- Session variables auto-set from JWT token
- Works with dynamic permissions

## 📋 How It Works

```
1. User request with MSAL token
   ↓
2. MSALAuthenticationMiddleware validates token
   ↓
3. RLSMiddleware sets PostgreSQL session vars:
   - app.user_id
   - app.user_scopes = "Employee.Read,Files.Write"
   - app.user_roles = "Manager,Admin"
   ↓
4. Django ORM query executes
   ↓
5. PostgreSQL RLS policy checks session vars
   ↓
6. Only authorized rows returned
```

## 🚀 Quick Example

### Define Policy in Admin

1. Go to Django Admin → RLS Policies
2. Create policy:
   - Name: `employee_read_access`
   - Table: `employee_employee`
   - Command: `SELECT`
   - Required Scopes: `Employee.Read`
3. Save and click "Apply to database"

### Generated SQL

```sql
CREATE POLICY employee_read_access
ON employee_employee
AS PERMISSIVE
FOR SELECT
TO PUBLIC
USING (
    current_setting('app.user_scopes', true) ~* 'Employee.Read'
);
```

### Application Code

```python
# No changes needed! RLS is transparent
from employee.models import Employee

# This query is automatically filtered by RLS
employees = Employee.objects.all()
```

## 🔒 Common Use Cases

### 1. Department-Based Access
Users only see employees in their department

### 2. Tenant Isolation
Multi-tenant SaaS - users only see their tenant's data

### 3. Scope-Based Filtering
Filter rows based on Azure AD scopes

### 4. Role-Based Access
Managers see more data than regular users

### 5. Combined Policies
Scope + Department + Role requirements

## 📊 Admin Interface Features

### RLS Policy Admin
- ✅ SQL preview before applying
- ✅ Scope/Role selection with badges
- ✅ Policy type (PERMISSIVE/RESTRICTIVE)
- ✅ Bulk apply/remove actions
- ✅ Active/Inactive status
- ✅ Custom SQL expressions
- ✅ Priority ordering

### RLS Table Config Admin
- ✅ Enable/Disable RLS per table
- ✅ Force RLS for superusers
- ✅ Session variable configuration
- ✅ Custom variable mapping (JSON)
- ✅ View active policies
- ✅ Bulk enable/disable actions

## 🎓 Session Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `app.user_id` | User's OID or email | `"a1b2c3-..."` |
| `app.user_email` | Email address | `"user@company.com"` |
| `app.user_name` | Display name | `"John Doe"` |
| `app.user_scopes` | Comma-separated scopes | `"Employee.Read,Files.Write"` |
| `app.user_roles` | Comma-separated roles | `"Manager,Admin"` |
| `app.tenant_id` | Azure AD tenant ID | `"tenant-guid"` |
| Custom vars | Configurable in admin | `"123"` (dept ID) |

## 🛠️ Management Commands

### View Status
```bash
python manage.py manage_rls
```

### Preview SQL
```bash
python manage.py manage_rls --preview
python manage.py manage_rls --preview --table employee_employee
```

### Apply Policies
```bash
python manage.py manage_rls --apply-all
python manage.py manage_rls --policy employee_read_access
```

### Enable RLS
```bash
python manage.py manage_rls --enable-table employee_employee
```

## ⚙️ Configuration

### settings.py

```python
INSTALLED_APPS = [
    ...
    'hub_auth_client.django',
]

MIDDLEWARE = [
    ...
    'hub_auth_client.django.MSALAuthenticationMiddleware',
    'hub_auth_client.django.rls_middleware.RLSMiddleware',  # Add this
]

# PostgreSQL required
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
    }
}
```

### Run Migrations

```bash
python manage.py migrate
```

## 🐛 Debugging

### Enable Debug Middleware

```python
MIDDLEWARE = [
    ...
    'hub_auth_client.django.rls_middleware.RLSDebugMiddleware',
]

LOGGING = {
    'loggers': {
        'hub_auth.rls': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Check Session Variables in PostgreSQL

```sql
SELECT 
    current_setting('app.user_id', true) as user_id,
    current_setting('app.user_scopes', true) as scopes,
    current_setting('app.user_roles', true) as roles;
```

### View Active Policies

```sql
SELECT * FROM pg_policies WHERE tablename = 'employee_employee';
```

## ⚠️ Important Notes

### Requirements
- ✅ PostgreSQL database
- ✅ hub-auth-client package installed
- ✅ Migrations run

### Performance
- Use indexes on columns in RLS policies
- Test with realistic data volumes
- Monitor query performance

### Security
- Start restrictive, relax as needed
- Test thoroughly with different users
- Validate session variables
- Use FORCE RLS for superusers if needed

### Migration
- Enable RLS on tables one at a time
- Start with PERMISSIVE policies
- Have rollback plan ready

## 📚 Full Documentation

See [RLS_GUIDE.md](RLS_GUIDE.md) for:
- Complete setup instructions
- Common RLS patterns
- Security best practices
- Troubleshooting guide
- FAQ

## 🎉 Summary

RLS integration adds database-level security enforcement to hub-auth-client, making it even more powerful for multi-tenant applications, department-based access, and complex data visibility requirements.

**Key advantages:**
1. ✅ Configure through Django admin (no code changes)
2. ✅ Database-enforced security (can't be bypassed)
3. ✅ Works with existing scopes/roles from MSAL tokens
4. ✅ Transparent to application code
5. ✅ Better performance than application-level filtering

**Next steps:**
1. Read [RLS_GUIDE.md](RLS_GUIDE.md)
2. Configure RLS in Django admin
3. Test with different user scopes/roles
4. Apply policies to production
