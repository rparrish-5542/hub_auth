# Row-Level Security (RLS) with Hub Auth Client

## Overview

Hub Auth Client now includes **PostgreSQL Row-Level Security (RLS)** integration that lets you enforce data access rules at the database level based on Azure AD scopes and roles.

Instead of filtering queries in your application code, RLS policies run directly in PostgreSQL, automatically restricting which rows users can see, insert, update, or delete based on their MSAL token claims.

## 🎯 What is RLS?

Row-Level Security is a PostgreSQL feature that lets you create security policies that control access to individual rows in database tables based on the current user's characteristics.

### Benefits:

- ✅ **Database-enforced security** - Can't be bypassed by buggy application code
- ✅ **Performance** - PostgreSQL optimizes queries with RLS constraints
- ✅ **Centralized policies** - Define once, applies to all queries
- ✅ **Audit trail** - Database logs all access attempts
- ✅ **Admin-configurable** - Define policies through Django admin without code changes

## 🚀 Quick Start

### 1. Enable RLS in Settings

```python
# settings.py

INSTALLED_APPS = [
    ...
    'hub_auth_client.django',
    ...
]

MIDDLEWARE = [
    ...
    'hub_auth_client.django.MSALAuthenticationMiddleware',
    'hub_auth_client.django.rls_middleware.RLSMiddleware',  # Add this
    ...
]

# Ensure you're using PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
    }
}
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure RLS in Django Admin

#### 3a. Enable RLS on a Table

1. Go to Django Admin → RLS Table Configurations
2. Click "Add RLS Table Configuration"
3. Enter table name (e.g., `employee_employee`)
4. Check "RLS enabled"
5. Configure which session variables to set (user_id, scopes, roles)
6. Save

#### 3b. Create an RLS Policy

1. Go to Django Admin → RLS Policies
2. Click "Add RLS Policy"
3. Fill in:
   - **Name**: `employee_department_access`
   - **Table name**: `employee_employee`
   - **Policy command**: `ALL`
   - **Required scopes**: Select scopes (e.g., `Employee.Read`)
   - **Scope requirement**: `any` or `all`
4. Save
5. Select the policy and choose Action → "Apply selected policies to database"

### 4. Test It!

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import DynamicScopePermission

class EmployeeListView(APIView):
    permission_classes = [DynamicScopePermission]
    
    def get(self, request):
        # This query is automatically filtered by RLS!
        # Users only see employees they have access to
        from employee.models import Employee
        employees = Employee.objects.all()
        
        return Response({
            'count': employees.count(),
            'employees': [e.name for e in employees]
        })
```

## 📊 How It Works

### Architecture

```
1. User makes request with MSAL JWT token
   ↓
2. MSALAuthenticationMiddleware validates token
   ↓
3. RLSMiddleware sets PostgreSQL session variables:
   - app.user_id = user's OID
   - app.user_scopes = "Employee.Read,Employee.Write"
   - app.user_roles = "Manager,Admin"
   ↓
4. Django ORM executes query
   ↓
5. PostgreSQL RLS policy checks session variables
   ↓
6. Only matching rows are returned
```

### Session Variables Set by RLSMiddleware

| Variable | Source | Example Value |
|----------|--------|---------------|
| `app.user_id` | Token `oid` or `email` | `"a1b2c3d4-..."` |
| `app.user_email` | Token `email` | `"user@company.com"` |
| `app.user_name` | Token `name` | `"John Doe"` |
| `app.user_scopes` | Token `scp` claim | `"Employee.Read,Files.Write"` |
| `app.user_roles` | Token `roles` claim | `"Manager,Admin"` |
| `app.tenant_id` | Token `tid` | `"tenant-id-guid"` |
| Custom vars | Configured in admin | `"123"` (dept ID, etc) |

## 🔧 RLS Policy Types

### Permissive Policies (Default)

Grant access if condition matches. Multiple permissive policies are OR'd together.

```sql
CREATE POLICY employee_read_own_department
ON employee_employee
AS PERMISSIVE
FOR SELECT
USING (
    current_setting('app.user_scopes', true) ~ 'Employee.Read'
    AND department_id = current_setting('app.user_department_id')::int
);
```

### Restrictive Policies

Deny access unless condition matches. All restrictive policies must pass (AND logic).

```sql
CREATE POLICY employee_no_hr_access
ON employee_employee
AS RESTRICTIVE
FOR ALL
USING (
    department != 'HR' 
    OR current_setting('app.user_roles', true) ~ 'HR.Admin'
);
```

## 📝 Common RLS Patterns

### Pattern 1: Scope-Based Access

**Scenario**: Users with `Employee.Read` scope can read all employees.

**Admin Configuration**:
- Table: `employee_employee`
- Policy Command: `SELECT`
- Required Scopes: `Employee.Read`
- Scope Requirement: `any`

**Generated SQL**:
```sql
CREATE POLICY employee_read_access
ON employee_employee
FOR SELECT
USING (
    current_setting('app.user_scopes', true) ~* 'Employee.Read'
);
```

### Pattern 2: Role-Based Access

**Scenario**: Only `Manager` and `Admin` roles can modify employees.

**Admin Configuration**:
- Table: `employee_employee`
- Policy Command: `UPDATE`
- Required Roles: `Manager`, `Admin`
- Role Requirement: `any`

**Generated SQL**:
```sql
CREATE POLICY employee_modify_access
ON employee_employee
FOR UPDATE
USING (
    current_setting('app.user_roles', true) ~* '(Manager|Admin)'
);
```

### Pattern 3: Department-Based Access with Custom SQL

**Scenario**: Users can only see employees in their department.

**Admin Configuration**:
- Table: `employee_employee`
- Policy Command: `SELECT`
- Custom USING expression:
  ```sql
  department_id = current_setting('app.user_department_id', true)::int
  ```

**Custom Session Variable** (in RLSTableConfig):
```json
{
  "app.user_department_id": "user.department.id"
}
```

### Pattern 4: Tenant Isolation

**Scenario**: Multi-tenant SaaS - users only see their tenant's data.

**Admin Configuration**:
- Table: `saas_customer`
- Policy Command: `ALL`
- Custom USING expression:
  ```sql
  tenant_id = current_setting('app.tenant_id', true)::uuid
  ```

### Pattern 5: Combined Scope + Department

**Scenario**: Users need `Employee.Read` scope AND must be in same department.

**Admin Configuration**:
- Table: `employee_employee`
- Policy Command: `SELECT`
- Required Scopes: `Employee.Read`
- Scope Requirement: `all`
- Custom USING expression:
  ```sql
  current_setting('app.user_scopes', true) ~* 'Employee.Read'
  AND department_id = current_setting('app.user_department_id', true)::int
  ```

## 🎛️ Management Commands

### Django Admin Actions (Recommended)

**All RLS operations can be performed through the Django admin interface without using the command line!**

#### RLS Policies Admin Actions

1. **Navigate to**: Django Admin → RLS Policies
2. **Select policies** you want to manage
3. **Choose action** from the dropdown:

   - ✅ **Apply selected policies to database** - Creates/updates selected policies in PostgreSQL
   - ❌ **Remove selected policies from database** - Drops selected policies from PostgreSQL
   - 👁️ **Preview SQL for selected policies** - Shows the SQL that will be executed
   - 🔍 **Check status of selected policies** - Verifies if policies exist in the database
   - 📋 **Apply all policies for selected tables** - Applies all active policies for the tables of selected policies

**Example**: To apply a new policy:
1. Go to RLS Policies
2. Check the boxes next to the policies you want to apply
3. Select "Apply selected policies to database" from the Actions dropdown
4. Click "Go"
5. Verify the success message

#### RLS Table Configurations Admin Actions

1. **Navigate to**: Django Admin → RLS Table Configurations
2. **Select tables** you want to manage
3. **Choose action** from the dropdown:

   - ✅ **Enable RLS on selected tables** - Enables RLS feature on tables in PostgreSQL
   - ❌ **Disable RLS on selected tables** - Disables RLS feature on tables
   - 📋 **Apply all policies for selected tables** - Applies all active policies for selected tables
   - 🗑️ **Remove all policies for selected tables** - Removes all policies from selected tables
   - 🔍 **Check RLS status for selected tables** - Shows RLS status and policy count

**Example**: To enable RLS and apply policies:
1. Go to RLS Table Configurations
2. Check the box next to your table (e.g., `employee_employee`)
3. Select "Enable RLS on selected tables"
4. Click "Go"
5. Then select "Apply all policies for selected tables"
6. Click "Go"

#### Typical Admin Workflow

**Step 1: Create RLS Table Config**
- Go to: **RLS Table Configurations** → **Add**
- Enter table name: `employee_employee`
- Check: ✅ **RLS enabled**
- Check session variables:
  - ✅ Use user_id
  - ✅ Use scopes
  - ✅ Use roles
- Click: **Save**

**Step 2: Create RLS Policies**
- Go to: **RLS Policies** → **Add**
- Enter:
  - Name: `employee_read_access`
  - Table: `employee_employee`
  - Command: `SELECT`
  - Required scopes: Select `Employee.Read`
  - Scope requirement: `any`
- Check: ✅ **Is active**
- Click: **Save**

**Step 3: Apply to Database** (Choose one method)

**Method A: Apply Individual Policies**
- Go to: **RLS Policies**
- Select: Check boxes for policies to apply
- Action: **Apply selected policies to database**
- Click: **Go**

**Method B: Apply All Policies for a Table**
- Go to: **RLS Table Configurations**
- Select: Check box for your table
- Action: **Apply all policies for selected tables**
- Click: **Go**

**Step 4: Verify** (Optional)
- Select your table in RLS Table Configurations
- Action: **Check RLS status for selected tables**
- Click: **Go**
- Review the status message showing:
  - RLS enabled/disabled
  - Policy count in database vs Django

### Command Line Management (Alternative)

For automation, scripting, or if you prefer the command line:

#### View RLS Status

```bash
python manage.py manage_rls
```

Output:
```
=== RLS Status ===

Tables with RLS:
  employee_employee: ✓ Enabled
  department_department: ✗ Disabled

RLS Policies: 2 active, 1 inactive
  ✓ employee_read_access on employee_employee (SELECT, PERMISSIVE)
  ✓ employee_modify_access on employee_employee (UPDATE, PERMISSIVE)
  ✗ old_policy on employee_employee (ALL, PERMISSIVE) - INACTIVE
```

#### Preview Policy SQL

```bash
python manage.py manage_rls --preview
python manage.py manage_rls --preview --table employee_employee
```

#### Apply All Policies

```bash
python manage.py manage_rls --apply-all
python manage.py manage_rls --apply-all --table employee_employee
```

#### Apply Specific Policy

```bash
python manage.py manage_rls --policy employee_read_access
```

#### Enable/Disable RLS on Table

```bash
python manage.py manage_rls --enable-table employee_employee
python manage.py manage_rls --disable-table employee_employee
```

#### Remove All Policies

```bash
python manage.py manage_rls --remove-all
python manage.py manage_rls --remove-all --table employee_employee
```

## 🐛 Debugging

### Enable RLS Debug Logging

```python
# settings.py

MIDDLEWARE = [
    ...
    'hub_auth_client.django.rls_middleware.RLSMiddleware',
    'hub_auth_client.django.rls_middleware.RLSDebugMiddleware',  # Add this
    ...
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
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
-- In psql or pg_admin
SELECT 
    current_setting('app.user_id', true) as user_id,
    current_setting('app.user_scopes', true) as scopes,
    current_setting('app.user_roles', true) as roles;
```

### Test RLS Policy Manually

```sql
-- Set session variables manually
SET LOCAL app.user_scopes = 'Employee.Read';
SET LOCAL app.user_department_id = '5';

-- Test query
SELECT * FROM employee_employee;

-- Reset
RESET app.user_scopes;
RESET app.user_department_id;
```

### View Active Policies

```sql
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'employee_employee';
```

## ⚠️ Important Considerations

### 1. **Performance**

- RLS adds a WHERE clause to every query
- Use indexes on columns referenced in RLS policies
- Test performance with realistic data volumes
- Consider materialized views for complex policies

### 2. **Superuser Bypass**

- PostgreSQL superusers bypass RLS by default
- Use `FORCE ROW LEVEL SECURITY` to apply to owners/admins
- Or use non-superuser application database roles

### 3. **Policy Ordering**

- PERMISSIVE policies are OR'd together (any match grants access)
- RESTRICTIVE policies are AND'd together (all must pass)
- Use priority field in admin to control evaluation order

### 4. **Testing**

- Always test RLS policies thoroughly
- Use different user roles and scopes
- Verify both positive and negative cases
- Check INSERT, UPDATE, DELETE in addition to SELECT

### 5. **Migration Strategy**

- Enable RLS on tables one at a time
- Start with PERMISSIVE policies (less restrictive)
- Monitor query performance
- Have rollback plan ready

## 🔒 Security Best Practices

### 1. **Principle of Least Privilege**

Start restrictive, then relax as needed:

```python
# Good: Deny by default, grant specific access
RLSPolicy(
    name='employee_default_deny',
    table_name='employee_employee',
    policy_type='RESTRICTIVE',
    using_expression='false',  # Deny all
)

RLSPolicy(
    name='employee_manager_access',
    table_name='employee_employee',
    policy_type='PERMISSIVE',
    required_roles=['Manager'],
)
```

### 2. **Validate Session Variables**

Always validate session variables exist and are valid:

```sql
-- Bad: Can crash if variable not set
department_id = current_setting('app.user_department_id')::int

-- Good: Use default value
department_id = COALESCE(
    current_setting('app.user_department_id', true)::int,
    -1  -- Invalid dept ID
)
```

### 3. **Audit RLS Changes**

- Log all policy creations/modifications
- Review policies regularly
- Document business rules for each policy

### 4. **Use WITH CHECK for Write Operations**

Ensure users can only create/update rows they can see:

```sql
CREATE POLICY employee_write
ON employee_employee
FOR INSERT
WITH CHECK (
    department_id = current_setting('app.user_department_id', true)::int
);
```

## 📚 Additional Resources

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Django + PostgreSQL RLS Guide](https://www.postgresql.org/docs/current/sql-createpolicy.html)
- [Hub Auth Dynamic Permissions](DYNAMIC_PERMISSIONS.md)

## 🤔 FAQ

### Q: Can I use RLS with SQLite or MySQL?

**A:** No, RLS is a PostgreSQL-specific feature. If you need row-level filtering on other databases, implement it in your Django views/querysets.

### Q: Does RLS work with Django ORM?

**A:** Yes! RLS is transparent to the ORM. Your `Model.objects.all()` queries are automatically filtered.

### Q: Can I disable RLS for specific queries?

**A:** Yes, but requires database superuser privileges:

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET SESSION AUTHORIZATION postgres;")
    cursor.execute("SELECT * FROM employee_employee;")  # Bypasses RLS
```

### Q: What happens if a policy references a non-existent session variable?

**A:** PostgreSQL will use an empty string. Use `current_setting('var', true)` to prevent errors and COALESCE for defaults.

### Q: Can I use RLS policies without hub_auth scopes/roles?

**A:** Yes! Write custom SQL expressions that reference any data:

```sql
owner_id = current_user::regrole
created_by = current_setting('app.user_email', true)
```

### Q: How do I test RLS locally?

**A:** Use the RLSDebugMiddleware and check logs. Also test with different user tokens via your API endpoints.

## 🎓 Example: Complete Employee Management Setup

### 1. Models

```python
# employee/models.py
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    manager_email = models.EmailField()

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
```

### 2. RLS Configuration (Django Admin)

**Table Config** for `employee_employee`:
- RLS Enabled: ✓
- Use scopes: ✓
- Use roles: ✓
- Custom session vars:
  ```json
  {
    "app.user_department_id": "user.department.id"
  }
  ```

**RLS Policies**:

1. **Basic Read Access** (everyone with scope sees all):
   - Name: `employee_basic_read`
   - Table: `employee_employee`
   - Command: `SELECT`
   - Required scopes: `Employee.Read`

2. **Department-Based Access** (see own dept only):
   - Name: `employee_department_read`
   - Table: `employee_employee`
   - Command: `SELECT`
   - Custom SQL:
     ```sql
     current_setting('app.user_scopes', true) ~* 'Employee.Read'
     AND department_id = current_setting('app.user_department_id', true)::int
     ```

3. **Manager Can Modify Own Dept**:
   - Name: `employee_manager_modify`
   - Table: `employee_employee`
   - Command: `UPDATE`
   - Custom SQL:
     ```sql
     current_setting('app.user_roles', true) ~* 'Manager'
     AND department_id = current_setting('app.user_department_id', true)::int
     ```

4. **HR Can See Salary**:
   - Name: `employee_salary_restriction`
   - Table: `employee_employee`
   - Command: `SELECT`
   - Type: `RESTRICTIVE`
   - Custom SQL:
     ```sql
     salary IS NULL 
     OR current_setting('app.user_roles', true) ~* 'HR'
     ```

### 3. Views

```python
# employee/views.py
from rest_framework import viewsets
from hub_auth_client.django import DynamicScopePermission
from .models import Employee
from .serializers import EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee CRUD - automatically filtered by RLS!
    """
    queryset = Employee.objects.all()  # RLS filters this
    serializer_class = EmployeeSerializer
    permission_classes = [DynamicScopePermission]
```

### 4. Apply Policies

```bash
python manage.py manage_rls --apply-all
```

### 5. Test!

Users with different roles/scopes will automatically see different data - no application code changes needed!

---

**Need help?** Check the main [README_PACKAGE.md](README_PACKAGE.md) or [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md) for more information.
