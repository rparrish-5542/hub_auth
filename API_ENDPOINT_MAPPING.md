# API Endpoint Mapping Admin Feature

## Overview
Version 1.0.18 of hub-auth-client now includes a dynamic API Endpoint Mapping admin interface that automatically discovers ViewSets from your Django application and displays their URL patterns, actions, and associated serializers in a beautiful table format.

## What It Does

The `APIEndpointMappingAdmin` automatically:

1. **Scans installed apps** for DRF ViewSets in `api_views.py` or `views.py` modules
2. **Discovers URL patterns** from router registrations
3. **Detects serializer classes** used for different actions (list, retrieve, create, update, custom actions)
4. **Displays everything in a read-only admin table** with color-coded formatting

## Features

### Automatic Discovery
- Finds all ViewSet classes across your Django apps
- Identifies standard CRUD endpoints (list, retrieve, create, update, delete)
- Detects custom `@action` decorated methods
- Extracts serializer information from:
  - `serializer_class` attribute
  - `get_serializer_class()` method logic
  - Custom action decorators

### Visual Display
- **Color-coded ViewSets**: Different colors for different ViewSet classes
- **HTTP method highlighting**: GET (blue), POST (green), PUT/PATCH (orange), DELETE (red)
- **Serializer formatting**: Code-style display with special highlighting for custom actions (✅)
- **App labels**: Shows which app each endpoint belongs to
- **Professional styling**: Clean, modern table with hover effects

### Read-Only Interface
- No add/edit/delete permissions (this is documentation, not configuration)
- Clean changelist view without filters or actions
- Fast loading with in-memory data (no database queries)

## How to Use

### 1. Install/Upgrade the Package

```bash
pip install --upgrade hub-auth-client==1.0.18
```

### 2. Run Migrations

```bash
python manage.py migrate hub_auth_client
```

### 3. Collect Static Files

```bash
python manage.py collectstatic
```

### 4. Access the Admin

Navigate to:
```
https://your-domain.com/admin/hub_auth_client/apiendpointmapping/
```

## Example Output

The admin will display a table like this:

| ViewSet | URL Pattern | Action | Expected Serializer | App |
|---------|------------|--------|---------------------|-----|
| **EmployeeViewSet** | `GET /api/employees/` | List all items | `EmployeeListSerializer` | employees |
| **EmployeeViewSet** | `GET /api/employees/{pk}/` | Retrieve single item | `EmployeeDetailSerializer` | employees |
| **EmployeeViewSet** | `GET /api/employees/active/` | Custom action - active | `EmployeeListSerializer ✅` | employees |
| **EmployeeViewSet** | `GET /api/employees/names/` | Custom action - names | `EmployeeNameSerializer ✅` | employees |
| **EmployeePositionViewSet** | `GET /api/positions/` | List all items | `EmployeePositionSerializer` | employees |
| **SupervisorViewSet** | `GET /api/supervisors/` | List all items | `SupervisorSerializer` | employees |

## How It Works

### ViewSet Discovery Algorithm

1. **Scans INSTALLED_APPS** for non-Django, non-DRF packages
2. **Imports modules** tries `{app}.api_views` first, then `{app}.views`
3. **Finds ViewSet classes** using `inspect.issubclass()` checks
4. **Extracts URL patterns** by inspecting router registrations
5. **Parses serializer logic** from source code and decorators

### Serializer Detection

The admin intelligently detects serializers by:

```python
# 1. Direct serializer_class attribute
class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer  # ✓ Detected

# 2. get_serializer_class() method parsing
def get_serializer_class(self):
    if self.action == 'list':
        return EmployeeListSerializer  # ✓ Detected via regex
    return EmployeeDetailSerializer

# 3. Custom action decorators
@action(detail=False, methods=['get'])
def names(self, request):
    # Will show as "Custom action - names" with ✅
    serializer = EmployeeNameSerializer(...)  # ✓ Detected from method context
```

### URL Pattern Detection

The admin finds base URLs by:

1. **Importing the app's urls.py module**
2. **Checking for a `router` object**
3. **Iterating router.registry** to find matching ViewSet class
4. **Building full URL patterns** with `/api/` prefix

Fallback logic:
- If router not found, uses ViewSet name to guess URL (e.g., `EmployeeViewSet` → `/api/employees`)
- Special handling for common patterns (positions, supervisors, etc.)

## Customization

### Changing ViewSet Colors

Edit `hub_auth_client/django/admin.py`:

```python
def viewset_display(self, obj):
    viewset_colors = {
        'YourViewSet': '#ff5722',  # Add your custom color
        'EmployeeViewSet': '#2e7d32',
        # ... more colors
    }
    color = viewset_colors.get(obj.viewset, '#5e35b1')  # Default purple
```

### Customizing CSS

The feature includes `endpoint_mappings.css` in:
```
hub_auth_client/django/static/admin/css/endpoint_mappings.css
```

You can override it in your own static files or modify the package CSS.

### Filtering Apps

If you want to exclude certain apps from discovery, modify `_discover_viewsets()`:

```python
for app_config in settings.INSTALLED_APPS:
    if app_config.startswith('django.') or app_config.startswith('rest_framework'):
        continue
    if app_config in ['myapp_to_exclude']:  # Add this
        continue
```

## Technical Details

### Virtual Model
`APIEndpointMapping` is a **virtual model** (not backed by a database table):

```python
class APIEndpointMapping(models.Model):
    class Meta:
        managed = False  # No migrations, no table
```

This allows it to appear in the admin without database overhead.

### Custom ChangeList
The admin uses a custom `ChangeList` class that overrides `get_results()`:

```python
class EndpointChangeList(ChangeList):
    def get_results(self, request):
        # Create mock objects from discovered data
        self.result_list = [EndpointRow(data) for data in discovered_endpoints]
```

This provides admin UI without QuerySets.

## Troubleshooting

### No Endpoints Showing
- Check that your ViewSets inherit from `viewsets.ViewSetMixin` or its subclasses
- Ensure ViewSets are in `api_views.py` or `views.py` files
- Verify router registration in app's `urls.py`

### Wrong Serializers Displayed
- The detection uses regex parsing of `get_serializer_class()` source code
- Complex conditional logic may not be fully detected
- Fallback shows `(auto)` when serializer can't be determined

### Missing Custom Actions
- Ensure actions use `@action` decorator from `rest_framework.decorators`
- Check that the method has `mapping` attribute

### Styling Issues
- Run `python manage.py collectstatic` after upgrading
- Clear browser cache
- Check that `endpoint_mappings.css` is served correctly

## Changelog

### Version 1.0.18 (Current)
- ✨ **New Feature**: Dynamic API Endpoint Mapping admin interface
- 🎨 Color-coded display for ViewSets and HTTP methods
- 🔍 Automatic serializer detection from source code
- 📊 Beautiful table layout with hover effects
- 🏷️ App labels to show endpoint origin
- 🎯 Read-only interface for documentation purposes

## Future Enhancements

Potential improvements for future versions:
- [ ] Filter by app in changelist
- [ ] Search by URL pattern or ViewSet name
- [ ] Export to CSV/JSON
- [ ] Permission detection (which scopes/roles required)
- [ ] Request/Response schema display
- [ ] Test endpoint directly from admin
- [ ] Integration with OpenAPI/Swagger docs

## Related Documentation

- [Django REST Framework ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/)
- [DRF Routers](https://www.django-rest-framework.org/api-guide/routers/)
- [hub-auth-client README](../README_PACKAGE.md)

## Support

If you encounter issues or have feature requests:
1. Check this documentation first
2. Review the source code in `hub_auth_client/django/admin.py`
3. Open an issue on GitHub with:
   - Your Django version
   - DRF version
   - hub-auth-client version
   - Example ViewSet code
   - Error messages or unexpected behavior
