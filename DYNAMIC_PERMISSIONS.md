# Database-Driven Permission Management

## Overview

Instead of hardcoding scopes and roles in your views, you can now configure them through the Django admin interface. This makes the package flexible for multiple projects without code changes.

## Features

- ✅ **Define Scopes** - Create and manage scope definitions
- ✅ **Define Roles** - Create and manage role definitions
- ✅ **Configure Endpoints** - Map URL patterns to required scopes/roles
- ✅ **Flexible Requirements** - Require ANY or ALL scopes/roles
- ✅ **URL Pattern Matching** - Use regex to match endpoints
- ✅ **HTTP Method Filtering** - Different permissions per HTTP method
- ✅ **Priority-Based Matching** - Control which rules apply first
- ✅ **Caching** - Performance optimized with caching
- ✅ **Admin Interface** - Easy management through Django admin

## Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'hub_auth_client.django',  # Add this
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

## Usage

### Option 1: Dynamic Permissions (Recommended)

Use `DynamicPermission` in your views - it reads requirements from the database:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from hub_auth_client.django import DynamicPermission

class EmployeeListView(APIView):
    permission_classes = [DynamicPermission]  # Reads from database
    
    def get(self, request):
        employees = Employee.objects.all()
        return Response(EmployeeSerializer(employees, many=True).data)
```

### Option 2: Scope-Only Dynamic Permissions

```python
from hub_auth_client.django import DynamicScopePermission

class UserProfileView(APIView):
    permission_classes = [DynamicScopePermission]  # Only checks scopes
    
    def get(self, request):
        return Response({'user': request.user.username})
```

### Option 3: Role-Only Dynamic Permissions

```python
from hub_auth_client.django import DynamicRolePermission

class AdminView(APIView):
    permission_classes = [DynamicRolePermission]  # Only checks roles
    
    def get(self, request):
        return Response({'message': 'Admin access'})
```

## Admin Configuration

### 1. Access Django Admin

Navigate to: `http://localhost:8000/admin/`

### 2. Define Scopes

**Admin → Scope Definitions → Add Scope Definition**

Examples:
- **Name**: `Employee.Read`
- **Category**: `Employee`
- **Description**: `Read employee information`
- **Is Active**: ✓

Add more scopes:
- `Employee.Write`, `Employee.Delete`
- `User.Read`, `User.Write`
- `Files.Read`, `Files.Write`

### 3. Define Roles

**Admin → Role Definitions → Add Role Definition**

Examples:
- **Name**: `Admin`
- **Description**: `Administrator role with full access`
- **Is Active**: ✓

Add more roles:
- `Manager`, `User`, `HR`, `ReadOnly`

### 4. Configure Endpoint Permissions

**Admin → Endpoint Permissions → Add Endpoint Permission**

#### Example 1: Employee List (Read Access)

- **Name**: `Employee List`
- **URL Pattern**: `^/api/employees/$`
- **HTTP Methods**: `GET`
- **Required Scopes**: `Employee.Read`
- **Scope Requirement**: `Any`
- **Is Active**: ✓
- **Priority**: `10`

#### Example 2: Employee Create (Write Access)

- **Name**: `Employee Create`
- **URL Pattern**: `^/api/employees/$`
- **HTTP Methods**: `POST`
- **Required Scopes**: `Employee.Write`
- **Scope Requirement**: `Any`
- **Is Active**: ✓
- **Priority**: `10`

#### Example 3: Employee Update (Both Read & Write)

- **Name**: `Employee Update`
- **URL Pattern**: `^/api/employees/[0-9]+/$`
- **HTTP Methods**: `PUT,PATCH`
- **Required Scopes**: `Employee.Read`, `Employee.Write`
- **Scope Requirement**: `All` ← User needs BOTH scopes
- **Is Active**: ✓
- **Priority**: `10`

#### Example 4: Admin Only Endpoint

- **Name**: `Admin Dashboard`
- **URL Pattern**: `^/api/admin/.*`
- **HTTP Methods**: `*` ← All methods
- **Required Roles**: `Admin`
- **Role Requirement**: `Any`
- **Is Active**: ✓
- **Priority**: `20` ← Higher priority

#### Example 5: Complex Requirements

- **Name**: `HR Management`
- **URL Pattern**: `^/api/hr/.*`
- **HTTP Methods**: `*`
- **Required Scopes**: `Employee.Read`, `Employee.Write`
- **Scope Requirement**: `All`
- **Required Roles**: `HR`, `Manager`, `Admin`
- **Role Requirement**: `Any` ← User needs ANY of these roles
- **Is Active**: ✓
- **Priority**: `15`

## URL Pattern Examples

| Pattern | Matches |
|---------|---------|
| `^/api/employees/$` | Exact: `/api/employees/` |
| `^/api/employees/[0-9]+/$` | `/api/employees/123/` |
| `^/api/employees/.*` | `/api/employees/` and all sub-paths |
| `^/api/users/[^/]+/$` | `/api/users/john/` |
| `.*/export/$` | Any path ending with `/export/` |

## HTTP Methods

- **Single**: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- **Multiple**: `GET,POST` (comma-separated)
- **All Methods**: `*`

## Priority System

Higher priority rules are checked first:
- **Priority 100**: Critical security rules
- **Priority 50**: Standard endpoint rules
- **Priority 10**: Default rules
- **Priority 0**: Fallback rules

If multiple rules match a request, the highest priority one is used.

## Scope/Role Requirements

### Any (Default)
User needs **at least one** of the specified scopes/roles:
- Scopes: `Employee.Read` OR `Employee.Write`
- Roles: `Admin` OR `Manager`

### All
User needs **all** of the specified scopes/roles:
- Scopes: `Employee.Read` AND `Employee.Write`
- Roles: `Admin` AND `Manager`

## Caching

Endpoint permissions are cached for 5 minutes to improve performance.

To clear cache manually:
```python
from django.core.cache import cache
cache.clear()
```

## Migration from Hardcoded Permissions

### Before (Hardcoded)

```python
from hub_auth_client.django import HasScopes

class EmployeeListView(APIView):
    permission_classes = [HasScopes(['Employee.Read'])]  # Hardcoded
    
    def get(self, request):
        return Response([...])
```

### After (Database-Driven)

```python
from hub_auth_client.django import DynamicPermission

class EmployeeListView(APIView):
    permission_classes = [DynamicPermission]  # Reads from database
    
    def get(self, request):
        return Response([...])
```

Then configure in admin:
1. Create scope: `Employee.Read`
2. Create endpoint permission:
   - URL: `^/api/employees/$`
   - Method: `GET`
   - Scope: `Employee.Read`

## Benefits

### For Multiple Projects

Each project can configure its own scopes and endpoints without changing code:

**Project A (employee_manage)**:
- Scopes: `Employee.Read`, `Employee.Write`
- Endpoints: `/api/employees/`, `/api/departments/`

**Project B (document_service)**:
- Scopes: `Document.Read`, `Document.Write`, `Document.Share`
- Endpoints: `/api/documents/`, `/api/folders/`

Same package, different configurations!

### For Different Environments

Configure different permissions per environment:
- **Development**: Relaxed permissions
- **Staging**: Testing permissions
- **Production**: Strict permissions

### For Dynamic Changes

Change permissions without deploying code:
1. Go to admin
2. Update endpoint permission
3. Changes apply immediately (after cache expires)

## Best Practices

### 1. Use Categories

Group scopes by category for better organization:
```
Category: Employee
- Employee.Read
- Employee.Write
- Employee.Delete

Category: User
- User.Read
- User.Write
```

### 2. Be Specific with URL Patterns

More specific patterns should have higher priority:
```
Priority 20: ^/api/employees/[0-9]+/$     (specific)
Priority 10: ^/api/employees/.*           (general)
```

### 3. Document Endpoints

Use the description field to document what the endpoint does:
```
Name: Employee Detail Update
Description: Allows updating employee information including salary and department
```

### 4. Test Patterns

Test your regex patterns at [regex101.com](https://regex101.com/)

### 5. Use Inactive for Testing

Instead of deleting, mark as inactive to preserve configuration:
- ✓ Can re-enable later
- ✓ Keep history
- ✓ See what was configured

## Troubleshooting

### Permission always denied

**Check**:
1. Is the endpoint permission active?
2. Does the URL pattern match your request path?
3. Does the HTTP method match?
4. Does the user have the required scopes/roles?

**Debug**:
```python
# In your view
print(f"Path: {request.path}")
print(f"Method: {request.method}")
print(f"User scopes: {request.user.scopes}")
print(f"User roles: {request.user.roles}")
```

### No permission check happening

**Check**:
1. Is `DynamicPermission` in `permission_classes`?
2. Are migrations applied?
3. Is `hub_auth_client.django` in `INSTALLED_APPS`?

### Cache not updating

Clear cache after changes:
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

Or wait 5 minutes for cache to expire.

## Example: Complete Setup for employee_manage

### 1. Create Scopes in Admin

- `Employee.Read` - Read employee information
- `Employee.Write` - Create and update employees
- `Employee.Delete` - Delete employees
- `Department.Read` - Read department information
- `Department.Write` - Manage departments

### 2. Create Roles in Admin

- `Admin` - Full system access
- `HR` - Human resources access
- `Manager` - Department manager access
- `User` - Regular user access

### 3. Configure Endpoints

| Endpoint | URL Pattern | Method | Scopes | Roles |
|----------|-------------|--------|--------|-------|
| Employee List | `^/api/employees/$` | GET | Employee.Read | - |
| Employee Create | `^/api/employees/$` | POST | Employee.Write | HR, Admin |
| Employee Detail | `^/api/employees/[0-9]+/$` | GET | Employee.Read | - |
| Employee Update | `^/api/employees/[0-9]+/$` | PUT,PATCH | Employee.Read + Employee.Write (ALL) | HR, Admin |
| Employee Delete | `^/api/employees/[0-9]+/$` | DELETE | Employee.Delete | Admin |

### 4. Update Views

```python
from hub_auth_client.django import DynamicPermission

class EmployeeViewSet(ModelViewSet):
    permission_classes = [DynamicPermission]
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    
    # Permissions are now managed in admin!
```

## Advanced: Custom Permission Logic

If you need custom logic beyond database configuration, combine permissions:

```python
from hub_auth_client.django import DynamicPermission
from rest_framework.permissions import BasePermission

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.has_role('Admin')

class EmployeeDetailView(APIView):
    permission_classes = [DynamicPermission, IsOwnerOrAdmin]
    
    # Must pass BOTH permission checks
```

## Summary

Database-driven permissions give you:
- ✅ **Flexibility** - Configure per project without code changes
- ✅ **Manageability** - Update through admin interface
- ✅ **Scalability** - Easy to add new endpoints
- ✅ **Maintainability** - No code deployments for permission changes
- ✅ **Auditability** - Track changes in database
- ✅ **Testing** - Easy to test different configurations

**Perfect for managing multiple internal projects with different permission requirements!**
