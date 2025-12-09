"""
Django admin configuration for scope and permission management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import connection
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse
from .models import ScopeDefinition, RoleDefinition, EndpointPermission, APIEndpointMapping
from .admin_mixins import (
    URLPatternMixin,
    ScopeCountMixin,
    RoleCountMixin,
    ActiveBadgeMixin,
)

# Import RLS models if available
try:
    from .rls_models import RLSPolicy, RLSTableConfig
    RLS_AVAILABLE = True
except ImportError:
    RLS_AVAILABLE = False

# Import config models if available
try:
    from .config_models import AzureADConfiguration, AzureADConfigurationHistory
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@admin.register(ScopeDefinition)
class ScopeDefinitionAdmin(admin.ModelAdmin):
    """Admin for managing scope definitions."""
    
    change_list_template = "admin/hub_auth_client/scopedefinition/change_list.html"
    
    list_display = ['name', 'category', 'is_active', 'is_active_badge', 'endpoint_count', 'updated_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'category']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['sync_from_azure_ad']
    
    fieldsets = [
        ('Scope Information', {
            'fields': ['name', 'category', 'description']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_urls(self):
        """Add custom URL for sync button."""
        urls = super().get_urls()
        custom_urls = [
            path('sync-azure-scopes/', self.admin_site.admin_view(self.sync_azure_scopes_view), name='sync_azure_scopes'),
        ]
        return custom_urls + urls
    
    def sync_azure_scopes_view(self, request):
        """Custom view to sync scopes from Azure AD."""
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        
        try:
            # Call the fetch_azure_scopes management command
            call_command('fetch_azure_scopes', '--import', stdout=output)
            
            result = output.getvalue()
            
            # Check if any scopes were actually found
            if 'No scopes found' in result or 'Found 0 scopes' in result:
                self.message_user(
                    request,
                    f"No scopes found in Azure AD App Registration. Check the output below for details.\n\n{result}",
                    level=messages.WARNING
                )
            elif 'Created:' in result or 'Updated:' in result:
                # Success message only if scopes were imported
                self.message_user(
                    request,
                    f"Successfully synced scopes from Azure AD.\n\n{result}",
                    level=messages.SUCCESS
                )
            else:
                # Default case
                self.message_user(
                    request,
                    f"Sync completed. {result}",
                    level=messages.INFO
                )
        except Exception as e:
            self.message_user(
                request,
                f"Error syncing scopes: {str(e)}",
                level=messages.ERROR
            )
        
        # Redirect back to the changelist
        return redirect('admin:hub_auth_client_scopedefinition_changelist')
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'
    
    def endpoint_count(self, obj):
        """Count endpoints using this scope."""
        count = obj.endpoints.filter(is_active=True).count()
        return format_html(f'<span>{count} endpoints</span>')
    endpoint_count.short_description = 'Used By'
    
    def sync_from_azure_ad(self, request, queryset):
        """Sync scopes from Azure AD App Registration."""
        from django.core.management import call_command
        from io import StringIO
        import sys
        
        # Capture output
        output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output
        
        try:
            # Call the management command
            call_command('fetch_azure_scopes', '--import', stdout=output)
            sys.stdout = old_stdout
            
            # Get the output
            result = output.getvalue()
            
            # Show success message
            self.message_user(
                request,
                f"Azure AD sync completed. Check output for details."
            )
            
            # Show detailed output if available
            if result:
                lines = result.strip().split('\n')
                for line in lines[-10:]:  # Show last 10 lines
                    if line.strip():
                        self.message_user(request, line)
                        
        except Exception as e:
            sys.stdout = old_stdout
            self.message_user(
                request,
                f"Error syncing from Azure AD: {str(e)}",
                level='error'
            )
    
    sync_from_azure_ad.short_description = "Sync scopes from Azure AD"


@admin.register(RoleDefinition)
class RoleDefinitionAdmin(admin.ModelAdmin):
    """Admin for managing role definitions."""
    
    list_display = ['name', 'is_active', 'is_active_badge', 'endpoint_count', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Role Information', {
            'fields': ['name', 'description']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'
    
    def endpoint_count(self, obj):
        """Count endpoints using this role."""
        count = obj.endpoints.filter(is_active=True).count()
        return format_html(f'<span>{count} endpoints</span>')
    endpoint_count.short_description = 'Used By'


class EndpointPermissionScopeInline(admin.TabularInline):
    """Inline for managing endpoint scopes."""
    model = EndpointPermission.required_scopes.through
    extra = 1
    verbose_name = "Required Scope"
    verbose_name_plural = "Required Scopes"


class EndpointPermissionRoleInline(admin.TabularInline):
    """Inline for managing endpoint roles."""
    model = EndpointPermission.required_roles.through
    extra = 1
    verbose_name = "Required Role"
    verbose_name_plural = "Required Roles"


@admin.register(EndpointPermission)
class EndpointPermissionAdmin(URLPatternMixin, ScopeCountMixin, RoleCountMixin, ActiveBadgeMixin, admin.ModelAdmin):
    """Admin for managing endpoint permissions."""
    
    change_list_template = "admin/hub_auth_client/endpointpermission/change_list.html"
    
    list_display = [
        'name',
        'url_pattern_display',
        'http_methods',
        'scope_count',
        'role_count',
        'is_active',
        'is_active_badge',
        'priority'
    ]
    list_filter = ['is_active', 'scope_requirement', 'role_requirement', 'created_at']
    search_fields = ['name', 'url_pattern', 'description']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['discover_endpoints', 'show_endpoint_details']
    
    filter_horizontal = ['required_scopes', 'required_roles']
    
    fieldsets = [
        ('Endpoint Information', {
            'fields': ['name', 'description', 'url_pattern', 'http_methods']
        }),
        ('Scope Requirements', {
            'fields': ['required_scopes', 'scope_requirement']
        }),
        ('Role Requirements', {
            'fields': ['required_roles', 'role_requirement']
        }),
        ('Settings', {
            'fields': ['is_active', 'priority']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_urls(self):
        """Add custom URLs for discover and create actions."""
        urls = super().get_urls()
        custom_urls = [
            path('discover-unsecured/', self.admin_site.admin_view(self.discover_unsecured_view), name='discover_unsecured_endpoints'),
            path('create-permissions/', self.admin_site.admin_view(self.create_endpoint_permissions_view), name='create_endpoint_permissions'),
        ]
        return custom_urls + urls
    
    def discover_unsecured_view(self, request):
        """Custom view to discover unsecured endpoints with filters."""
        from django.core.management import call_command
        from django.shortcuts import render
        from io import StringIO
        import json
        from .admin_helpers import humanize_url_pattern
        
        # Get filter parameters - default to showing ALL endpoints
        unsecured_only = request.GET.get('unsecured_only', '0') == '1'  # Default: show all
        ignore_admin = request.GET.get('ignore_admin', '1') == '1'       # Default: ignore admin
        ignore_static = request.GET.get('ignore_static', '1') == '1'     # Default: ignore static
        
        output = StringIO()
        
        try:
            # Build command arguments
            cmd_args = ['--format=json']
            if unsecured_only:
                cmd_args.append('--unsecured-only')
            
            # Call the list_endpoints management command
            call_command('list_endpoints', *cmd_args, stdout=output)
            
            result = output.getvalue()
            endpoints = json.loads(result) if result.strip() else []
            
            # Apply filters
            filtered_endpoints = []
            for endpoint in endpoints:
                url_pattern = endpoint.get('url_pattern', '')
                view_name = endpoint.get('view_name', '')
                
                # Filter out admin views if requested
                if ignore_admin:
                    if '/admin/' in url_pattern or 'admin' in view_name.lower():
                        continue
                
                # Filter out static/media URLs if requested
                if ignore_static:
                    if any(pattern in url_pattern for pattern in ['/static/', '/media/', '__debug__']):
                        continue
                
                # Add humanized URL pattern
                endpoint['url_pattern_readable'] = humanize_url_pattern(url_pattern)
                
                filtered_endpoints.append(endpoint)
            
            # Render custom template
            context = {
                'endpoints': filtered_endpoints,
                'unsecured_only': unsecured_only,
                'ignore_admin': ignore_admin,
                'ignore_static': ignore_static,
                'title': 'Discover Unsecured Endpoints',
                'site_title': self.admin_site.site_title,
                'site_header': self.admin_site.site_header,
            }
            
            return render(request, 'admin/hub_auth_client/endpointpermission/discover_endpoints.html', context)
            
        except Exception as e:
            self.message_user(
                request,
                f"Error discovering endpoints: {str(e)}",
                level=messages.ERROR
            )
            return redirect('admin:hub_auth_client_endpointpermission_changelist')
    
    def create_endpoint_permissions_view(self, request):
        """Bulk create endpoint permissions from selected endpoints."""
        if request.method != 'POST':
            return redirect('admin:discover_unsecured_endpoints')
        
        selected_endpoints = request.POST.getlist('endpoints')
        
        if not selected_endpoints:
            self.message_user(
                request,
                "No endpoints selected.",
                level=messages.WARNING
            )
            return redirect('admin:discover_unsecured_endpoints')
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        for endpoint_data in selected_endpoints:
            try:
                # Parse endpoint data: url_pattern|http_methods|view_name|serializer_class
                parts = endpoint_data.split('|')
                url_pattern = parts[0] if len(parts) > 0 else ''
                http_methods = parts[1] if len(parts) > 1 else 'GET'
                view_name = parts[2] if len(parts) > 2 else ''
                serializer_class = parts[3] if len(parts) > 3 else ''
                
                # Check if permission already exists
                if EndpointPermission.objects.filter(url_pattern=url_pattern).exists():
                    skipped_count += 1
                    continue
                
                # Create unique name from URL pattern and view name
                # Extract action or endpoint identifier from URL
                url_parts = [p for p in url_pattern.replace('^', '').replace('$', '').split('/') if p and not p.startswith('?P<')]
                
                if view_name:
                    # Use view class name + URL-based identifier
                    view_class = view_name.split('.')[-1]
                    if len(url_parts) > 1:
                        # e.g., "EmployeeViewSet-active" or "EmployeeViewSet-names"
                        action = url_parts[-1].replace('.(?P<format>[a-z0-9]+)/?', '')
                        name = f"{view_class}-{action}"
                    else:
                        # e.g., "EmployeeViewSet-list"
                        name = f"{view_class}-list"
                else:
                    # Fallback to URL pattern-based name
                    name = url_pattern.replace('/', '_').replace('^', '').replace('$', '').strip('_')
                
                if not name or len(name) < 3:
                    name = f"endpoint_{created_count + 1}"
                
                # Ensure uniqueness by checking if name exists
                base_name = name
                counter = 1
                while EndpointPermission.objects.filter(name=name).exists():
                    name = f"{base_name}_{counter}"
                    counter += 1
                
                # Create endpoint permission
                EndpointPermission.objects.create(
                    name=name,
                    url_pattern=url_pattern,
                    http_methods=http_methods,
                    description=f"Auto-created from {view_name}" if view_name else "Auto-created endpoint",
                    is_active=False,  # Start as inactive until configured
                    priority=100
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"{url_pattern}: {str(e)}")
        
        # Show results
        if created_count > 0:
            self.message_user(
                request,
                f"Successfully created {created_count} endpoint permission(s).",
                level=messages.SUCCESS
            )
        
        if skipped_count > 0:
            self.message_user(
                request,
                f"Skipped {skipped_count} endpoint(s) - already exist.",
                level=messages.INFO
            )
        
        if errors:
            self.message_user(
                request,
                f"Errors: {'; '.join(errors[:5])}",
                level=messages.ERROR
            )
        
        # Redirect back to the changelist
        return redirect('admin:hub_auth_client_endpointpermission_changelist')
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'
    
    def scope_count(self, obj):
        """Count required scopes."""
        count = obj.required_scopes.filter(is_active=True).count()
        requirement = obj.scope_requirement.upper()
        if count > 0:
            return format_html(f'<span>{count} ({requirement})</span>')
        return '-'
    scope_count.short_description = 'Scopes'
    
    def role_count(self, obj):
        """Count required roles."""
        count = obj.required_roles.filter(is_active=True).count()
        requirement = obj.role_requirement.upper()
        if count > 0:
            return format_html(f'<span>{count} ({requirement})</span>')
        return '-'
    role_count.short_description = 'Roles'
    
    def discover_endpoints(self, request, queryset):
        """Discover all endpoints in the application."""
        from django.core.management import call_command
        from io import StringIO
        import sys
        import json
        
        # Capture output
        output = StringIO()
        
        try:
            # Call the management command with JSON output
            call_command('list_endpoints', '--format=json', '--unsecured-only', stdout=output)
            
            # Parse JSON output
            result = output.getvalue()
            endpoints = json.loads(result)
            
            if endpoints:
                # Show summary
                self.message_user(
                    request,
                    f"Found {len(endpoints)} unsecured endpoints. Details below:"
                )
                
                # Show first 10 unsecured endpoints
                for endpoint in endpoints[:10]:
                    msg = f"🔓 {endpoint['url_pattern']} ({', '.join(endpoint['methods'])}) - {endpoint['view_name']}"
                    self.message_user(request, msg, level='warning')
                
                if len(endpoints) > 10:
                    self.message_user(
                        request,
                        f"... and {len(endpoints) - 10} more. Run 'python manage.py list_endpoints' for full list.",
                        level='warning'
                    )
            else:
                self.message_user(
                    request,
                    "✅ All endpoints are secured!"
                )
                
        except Exception as e:
            self.message_user(
                request,
                f"Error discovering endpoints: {str(e)}",
                level='error'
            )
    
    discover_endpoints.short_description = "Discover unsecured endpoints"
    
    def show_endpoint_details(self, request, queryset):
        """Show detailed information about selected endpoint permissions."""
        from django.core.management import call_command
        from io import StringIO
        import sys
        import json
        
        # Get all endpoints
        output = StringIO()
        
        try:
            call_command('list_endpoints', '--format=json', '--show-serializers', stdout=output)
            result = output.getvalue()
            all_endpoints = json.loads(result)
            
            # Match selected permissions with discovered endpoints
            for permission in queryset:
                matching = [
                    e for e in all_endpoints 
                    if e['url_pattern'] == permission.url_pattern
                ]
                
                if matching:
                    endpoint = matching[0]
                    msg = (
                        f"<strong>{permission.name}</strong><br>"
                        f"URL: {endpoint['url_pattern']}<br>"
                        f"View: {endpoint['view_name']}<br>"
                        f"Methods: {', '.join(endpoint['methods'])}<br>"
                        f"Permission Classes: {', '.join(endpoint['permission_classes']) or 'None'}<br>"
                    )
                    if endpoint.get('serializer'):
                        msg += f"Serializer: {endpoint['serializer']}<br>"
                    
                    self.message_user(request, format_html(msg))
                else:
                    self.message_user(
                        request,
                        f"⚠ No matching endpoint found for: {permission.url_pattern}",
                        level='warning'
                    )
                    
        except Exception as e:
            self.message_user(
                request,
                f"Error fetching endpoint details: {str(e)}",
                level='error'
            )
    
    show_endpoint_details.short_description = "Show endpoint details"
    
    class Media:
        css = {
            'all': ['admin/css/widgets.css']
        }


# Optional: Create a custom admin site for better organization
class PermissionAdminSite(admin.AdminSite):
    """Custom admin site for permission management."""
    site_header = "Hub Auth - Permission Management"
    site_title = "Permission Admin"
    index_title = "Manage Scopes, Roles, and Endpoint Permissions"


# RLS Admin Classes
if RLS_AVAILABLE:
    
    @admin.register(RLSPolicy)
    class RLSPolicyAdmin(admin.ModelAdmin):
        """Admin for managing RLS policies."""
        
        list_display = [
            'name',
            'table_name',
            'policy_command',
            'policy_type',
            'scope_count',
            'role_count',
            'is_active',
            'is_active_badge',
        ]
        list_filter = [
            'is_active',
            'policy_command',
            'policy_type',
            'table_name',
            'created_at'
        ]
        search_fields = ['name', 'table_name', 'description']
        list_editable = ['is_active']
        readonly_fields = ['created_at', 'updated_at', 'preview_sql']
        
        filter_horizontal = ['required_scopes', 'required_roles']
        
        fieldsets = [
            ('Policy Information', {
                'fields': ['name', 'table_name', 'description']
            }),
            ('Policy Configuration', {
                'fields': [
                    'policy_command',
                    'policy_type',
                    'applies_to_roles'
                ]
            }),
            ('Scope Requirements', {
                'fields': ['required_scopes', 'scope_requirement'],
                'description': 'Scopes required to access rows (via session variables)'
            }),
            ('Role Requirements', {
                'fields': ['required_roles', 'role_requirement'],
                'description': 'Roles required to access rows (via session variables)'
            }),
            ('Custom SQL Expressions', {
                'fields': ['using_expression', 'with_check_expression'],
                'classes': ['collapse'],
                'description': (
                    'Advanced: Override scope/role-based expressions with custom SQL. '
                    'Leave blank to auto-generate from scopes/roles.'
                )
            }),
            ('Generated SQL Preview', {
                'fields': ['preview_sql'],
                'classes': ['collapse'],
            }),
            ('Status', {
                'fields': ['is_active']
            }),
            ('Metadata', {
                'fields': ['created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]
        
        def is_active_badge(self, obj):
            """Display active status as badge."""
            if obj.is_active:
                return format_html('<span style="color: green;">✓ Active</span>')
            return format_html('<span style="color: red;">✗ Inactive</span>')
        is_active_badge.short_description = 'Status'
        
        def scope_count(self, obj):
            """Count required scopes."""
            count = obj.required_scopes.filter(is_active=True).count()
            if count > 0:
                requirement = obj.scope_requirement.upper()
                return format_html(f'<span>{count} ({requirement})</span>')
            return '-'
        scope_count.short_description = 'Scopes'
        
        def role_count(self, obj):
            """Count required roles."""
            count = obj.required_roles.filter(is_active=True).count()
            if count > 0:
                requirement = obj.role_requirement.upper()
                return format_html(f'<span>{count} ({requirement})</span>')
            return '-'
        role_count.short_description = 'Roles'
        
        def preview_sql(self, obj):
            """Preview the generated SQL for this policy."""
            if obj.pk:
                sql = obj.generate_create_policy_sql()
                return format_html(
                    '<pre style="background: #f5f5f5; padding: 10px; '
                    'border-radius: 4px; overflow-x: auto;">{}</pre>',
                    sql
                )
            return "Save policy to preview SQL"
        preview_sql.short_description = 'SQL Preview'
        
        actions = [
            'apply_policies_to_database',
            'remove_policies_from_database',
            'preview_policy_sql',
            'check_policy_status',
            'apply_all_table_policies',
        ]
        
        def apply_policies_to_database(self, request, queryset):
            """Apply selected RLS policies to the database."""
            # Check if PostgreSQL
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            applied_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for policy in queryset:
                    if not policy.is_active:
                        continue
                    
                    try:
                        # Drop existing policy if it exists
                        cursor.execute(policy.generate_drop_policy_sql())
                        
                        # Create new policy
                        cursor.execute(policy.generate_create_policy_sql())
                        
                        # Enable RLS on table if not already
                        cursor.execute(policy.generate_enable_rls_sql())
                        
                        applied_count += 1
                    
                    except Exception as e:
                        errors.append(f"{policy.name}: {str(e)}")
            
            if applied_count > 0:
                self.message_user(
                    request,
                    f"Successfully applied {applied_count} RLS policies to database."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        apply_policies_to_database.short_description = "Apply selected policies to database"
        
        def remove_policies_from_database(self, request, queryset):
            """Remove selected RLS policies from the database."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            removed_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for policy in queryset:
                    try:
                        cursor.execute(policy.generate_drop_policy_sql())
                        removed_count += 1
                    except Exception as e:
                        errors.append(f"{policy.name}: {str(e)}")
            
            if removed_count > 0:
                self.message_user(
                    request,
                    f"Successfully removed {removed_count} RLS policies from database."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        remove_policies_from_database.short_description = "Remove selected policies from database"
        
        def preview_policy_sql(self, request, queryset):
            """Preview the SQL for selected policies."""
            if not queryset.exists():
                self.message_user(request, "No policies selected.", level='warning')
                return
            
            preview_html = '<div style="font-family: monospace;">'
            for policy in queryset:
                preview_html += f'<h3>{policy.name} ({policy.table_name})</h3>'
                preview_html += '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
                preview_html += policy.generate_create_policy_sql()
                preview_html += '</pre><hr>'
            preview_html += '</div>'
            
            self.message_user(
                request,
                format_html(
                    'SQL Preview for {} policies:<br>{}',
                    queryset.count(),
                    preview_html
                )
            )
        
        preview_policy_sql.short_description = "Preview SQL for selected policies"
        
        def check_policy_status(self, request, queryset):
            """Check if selected policies exist in the database."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            status_messages = []
            
            with connection.cursor() as cursor:
                for policy in queryset:
                    # Check if policy exists in database
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_policies
                            WHERE tablename = %s AND policyname = %s
                        )
                    """, [policy.table_name, policy.name])
                    
                    exists = cursor.fetchone()[0]
                    
                    # Check if RLS is enabled on table
                    cursor.execute("""
                        SELECT relrowsecurity, relforcerowsecurity
                        FROM pg_class
                        WHERE relname = %s
                    """, [policy.table_name])
                    
                    result = cursor.fetchone()
                    if result:
                        rls_enabled, force_rls = result
                        status = "✓ Applied" if exists else "✗ Not Applied"
                        rls_status = "✓ Enabled" if rls_enabled else "✗ Disabled"
                        force_status = " (FORCE)" if force_rls else ""
                        
                        status_messages.append(
                            f"{policy.name}: {status} | RLS: {rls_status}{force_status}"
                        )
                    else:
                        status_messages.append(
                            f"{policy.name}: ⚠ Table '{policy.table_name}' not found"
                        )
            
            self.message_user(
                request,
                format_html('<br>'.join(status_messages))
            )
        
        check_policy_status.short_description = "Check status of selected policies"
        
        def apply_all_table_policies(self, request, queryset):
            """Apply all active policies for tables of selected policies."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            # Get unique table names from selected policies
            table_names = set(queryset.values_list('table_name', flat=True))
            
            applied_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for table_name in table_names:
                    # Get all active policies for this table
                    table_policies = RLSPolicy.objects.filter(
                        table_name=table_name,
                        is_active=True
                    )
                    
                    for policy in table_policies:
                        try:
                            # Drop existing policy if it exists
                            cursor.execute(policy.generate_drop_policy_sql())
                            
                            # Create new policy
                            cursor.execute(policy.generate_create_policy_sql())
                            
                            # Enable RLS on table if not already
                            cursor.execute(policy.generate_enable_rls_sql())
                            
                            applied_count += 1
                        
                        except Exception as e:
                            errors.append(f"{policy.name}: {str(e)}")
            
            if applied_count > 0:
                self.message_user(
                    request,
                    f"Successfully applied {applied_count} RLS policies across {len(table_names)} tables."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        apply_all_table_policies.short_description = "Apply all policies for selected tables"
    
    
    @admin.register(RLSTableConfig)
    class RLSTableConfigAdmin(admin.ModelAdmin):
        """Admin for managing RLS table configurations."""
        
        change_list_template = "admin/hub_auth_client/rlstableconfig/change_list.html"
        
        list_display = [
            'table_name',
            'rls_enabled',
            'rls_status_badge',
            'force_rls',
            'policy_count',
            'session_vars_summary',
        ]
        list_filter = ['rls_enabled', 'force_rls', 'created_at']
        search_fields = ['table_name', 'description']
        list_editable = ['rls_enabled', 'force_rls']
        readonly_fields = ['created_at', 'updated_at', 'current_policies']
        
        fieldsets = [
            ('Table Information', {
                'fields': ['table_name', 'description']
            }),
            ('RLS Configuration', {
                'fields': ['rls_enabled', 'force_rls']
            }),
            ('Session Variables', {
                'fields': [
                    'use_user_id',
                    'use_scopes',
                    'use_roles',
                    'custom_session_vars'
                ],
                'description': (
                    'Configure which session variables to set for RLS policies. '
                    'Custom vars format: {"app.var_name": "user.attribute"}'
                )
            }),
            ('Current Policies', {
                'fields': ['current_policies'],
                'classes': ['collapse'],
            }),
            ('Metadata', {
                'fields': ['created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]
        
        def rls_status_badge(self, obj):
            """Display RLS status as badge."""
            if obj.rls_enabled:
                force_text = " (FORCE)" if obj.force_rls else ""
                return format_html(
                    '<span style="color: green;">✓ Enabled{}</span>',
                    force_text
                )
            return format_html('<span style="color: red;">✗ Disabled</span>')
        rls_status_badge.short_description = 'RLS Status'
        
        def policy_count(self, obj):
            """Count policies for this table."""
            if RLS_AVAILABLE:
                count = RLSPolicy.objects.filter(
                    table_name=obj.table_name,
                    is_active=True
                ).count()
                return format_html(f'<span>{count} policies</span>')
            return '-'
        policy_count.short_description = 'Policies'
        
        def session_vars_summary(self, obj):
            """Summary of session variables configuration."""
            vars_enabled = []
            if obj.use_user_id:
                vars_enabled.append('user_id')
            if obj.use_scopes:
                vars_enabled.append('scopes')
            if obj.use_roles:
                vars_enabled.append('roles')
            if obj.custom_session_vars:
                vars_enabled.append(f"{len(obj.custom_session_vars)} custom")
            
            return ', '.join(vars_enabled) if vars_enabled else 'None'
        session_vars_summary.short_description = 'Session Variables'
        
        def current_policies(self, obj):
            """Show current policies for this table."""
            if obj.pk and RLS_AVAILABLE:
                policies = RLSPolicy.objects.filter(table_name=obj.table_name)
                if policies.exists():
                    policy_list = '<ul>'
                    for policy in policies:
                        status = '✓' if policy.is_active else '✗'
                        policy_list += f'<li>{status} {policy.name} ({policy.policy_command})</li>'
                    policy_list += '</ul>'
                    return format_html(policy_list)
                return "No policies defined for this table"
            return "Save table config to see policies"
        current_policies.short_description = 'Configured Policies'
        
        def get_urls(self):
            """Add custom URLs for discover and create actions."""
            urls = super().get_urls()
            custom_urls = [
                path('discover-tables/', self.admin_site.admin_view(self.discover_tables_view), name='discover_rls_tables'),
                path('create-table-configs/', self.admin_site.admin_view(self.create_table_configs_view), name='create_table_configs'),
            ]
            return custom_urls + urls
        
        def discover_tables_view(self, request):
            """Custom view to discover database tables with RLS status."""
            from django.shortcuts import render
            
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level=messages.ERROR
                )
                return redirect('admin:hub_auth_client_rlstableconfig_changelist')
            
            tables = []
            try:
                with connection.cursor() as cursor:
                    # Query to get all user tables with RLS status
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            COALESCE(relrowsecurity, false) as rls_enabled,
                            COALESCE(relforcerowsecurity, false) as force_rls,
                            obj_description(pg_class.oid, 'pg_class') as table_comment
                        FROM pg_tables
                        LEFT JOIN pg_class ON pg_class.relname = pg_tables.tablename
                            AND pg_class.relnamespace = (
                                SELECT oid FROM pg_namespace WHERE nspname = pg_tables.schemaname
                            )
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        AND schemaname !~ '^pg_toast'
                        ORDER BY schemaname, tablename
                    """)
                    
                    for schema, table_name, rls_enabled, force_rls, table_comment in cursor.fetchall():
                        full_table_name = f"{schema}.{table_name}" if schema != 'public' else table_name
                        
                        # Check if already configured
                        is_configured = RLSTableConfig.objects.filter(table_name=full_table_name).exists()
                        
                        tables.append({
                            'schema': schema,
                            'table_name': table_name,
                            'full_table_name': full_table_name,
                            'rls_enabled': rls_enabled,
                            'force_rls': force_rls,
                            'table_comment': table_comment or '',
                            'is_configured': is_configured,
                        })
            
            except Exception as e:
                self.message_user(
                    request,
                    f"Error discovering tables: {str(e)}",
                    level=messages.ERROR
                )
                return redirect('admin:hub_auth_client_rlstableconfig_changelist')
            
            # Render custom template
            context = {
                'tables': tables,
                'title': 'Discover Database Tables',
                'site_title': self.admin_site.site_title,
                'site_header': self.admin_site.site_header,
            }
            
            return render(request, 'admin/hub_auth_client/rlstableconfig/discover_tables.html', context)
        
        def create_table_configs_view(self, request):
            """Bulk create RLS table configurations from selected tables."""
            if request.method != 'POST':
                return redirect('admin:discover_rls_tables')
            
            selected_tables = request.POST.getlist('tables')
            
            if not selected_tables:
                self.message_user(
                    request,
                    "No tables selected.",
                    level=messages.WARNING
                )
                return redirect('admin:discover_rls_tables')
            
            created_count = 0
            skipped_count = 0
            errors = []
            
            for table_data in selected_tables:
                try:
                    # Parse table data: full_table_name|rls_enabled|force_rls
                    parts = table_data.split('|')
                    full_table_name = parts[0] if len(parts) > 0 else ''
                    rls_enabled = parts[1] == 'True' if len(parts) > 1 else False
                    force_rls = parts[2] == 'True' if len(parts) > 2 else False
                    
                    # Check if config already exists
                    if RLSTableConfig.objects.filter(table_name=full_table_name).exists():
                        skipped_count += 1
                        continue
                    
                    # Determine schema
                    schema = 'public'
                    if '.' in full_table_name:
                        schema = full_table_name.split('.')[0]
                    
                    # Create table config
                    RLSTableConfig.objects.create(
                        table_name=full_table_name,
                        description=f"Auto-discovered from {schema} schema",
                        rls_enabled=rls_enabled,
                        force_rls=force_rls,
                        use_user_id=True,  # Default to enabling user_id
                        use_scopes=False,
                        use_roles=False,
                        custom_session_vars={}
                    )
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"{full_table_name}: {str(e)}")
            
            # Show results
            if created_count > 0:
                self.message_user(
                    request,
                    f"Successfully created {created_count} table configuration(s).",
                    level=messages.SUCCESS
                )
            
            if skipped_count > 0:
                self.message_user(
                    request,
                    f"Skipped {skipped_count} table(s) - already configured.",
                    level=messages.INFO
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors[:5])}",
                    level=messages.ERROR
                )
            
            return redirect('admin:hub_auth_client_rlstableconfig_changelist')
        
        actions = [
            'discover_tables_from_database',
            'enable_rls_on_tables',
            'disable_rls_on_tables',
            'apply_all_policies_for_tables',
            'remove_all_policies_for_tables',
            'check_table_status',
        ]
        
        def discover_tables_from_database(self, request, queryset=None):
            """Discover all user tables from the PostgreSQL database and create RLSTableConfig entries."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            discovered_count = 0
            existing_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                # Query to get all user tables (excluding system tables)
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        relrowsecurity,
                        relforcerowsecurity
                    FROM pg_tables
                    LEFT JOIN pg_class ON pg_class.relname = pg_tables.tablename
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    AND schemaname !~ '^pg_toast'
                    ORDER BY schemaname, tablename
                """)
                
                tables = cursor.fetchall()
                
                for schema, table_name, rls_enabled, force_rls in tables:
                    full_table_name = f"{schema}.{table_name}" if schema != 'public' else table_name
                    
                    # Check if config already exists
                    if RLSTableConfig.objects.filter(table_name=full_table_name).exists():
                        existing_count += 1
                        continue
                    
                    try:
                        # Create new table config
                        RLSTableConfig.objects.create(
                            table_name=full_table_name,
                            description=f"Auto-discovered table from {schema} schema",
                            rls_enabled=rls_enabled or False,
                            force_rls=force_rls or False,
                            use_user_id=True,  # Default to enabling user_id session var
                            use_scopes=False,
                            use_roles=False,
                            custom_session_vars={}
                        )
                        discovered_count += 1
                    except Exception as e:
                        errors.append(f"{full_table_name}: {str(e)}")
            
            # Show results
            if discovered_count > 0:
                self.message_user(
                    request,
                    f"Successfully discovered and added {discovered_count} new table(s)."
                )
            
            if existing_count > 0:
                self.message_user(
                    request,
                    f"Skipped {existing_count} table(s) - already configured.",
                    level='info'
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors[:5])}",
                    level='error'
                )
            
            if discovered_count == 0 and existing_count == 0:
                self.message_user(
                    request,
                    "No tables found in the database.",
                    level='warning'
                )
        
        discover_tables_from_database.short_description = "Discover tables from database"
        
        def enable_rls_on_tables(self, request, queryset):
            """Enable RLS on selected tables."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            enabled_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for config in queryset:
                    try:
                        cursor.execute(config.generate_enable_rls_sql())
                        config.rls_enabled = True
                        config.save()
                        enabled_count += 1
                    except Exception as e:
                        errors.append(f"{config.table_name}: {str(e)}")
            
            if enabled_count > 0:
                self.message_user(
                    request,
                    f"Successfully enabled RLS on {enabled_count} tables."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        enable_rls_on_tables.short_description = "Enable RLS on selected tables"
        
        def disable_rls_on_tables(self, request, queryset):
            """Disable RLS on selected tables."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            disabled_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for config in queryset:
                    try:
                        cursor.execute(config.generate_disable_rls_sql())
                        config.rls_enabled = False
                        config.save()
                        disabled_count += 1
                    except Exception as e:
                        errors.append(f"{config.table_name}: {str(e)}")
            
            if disabled_count > 0:
                self.message_user(
                    request,
                    f"Successfully disabled RLS on {disabled_count} tables."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        disable_rls_on_tables.short_description = "Disable RLS on selected tables"
        
        def apply_all_policies_for_tables(self, request, queryset):
            """Apply all active policies for selected tables."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            applied_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for config in queryset:
                    # Get all active policies for this table
                    policies = RLSPolicy.objects.filter(
                        table_name=config.table_name,
                        is_active=True
                    )
                    
                    for policy in policies:
                        try:
                            # Drop existing policy if it exists
                            cursor.execute(policy.generate_drop_policy_sql())
                            
                            # Create new policy
                            cursor.execute(policy.generate_create_policy_sql())
                            
                            applied_count += 1
                        except Exception as e:
                            errors.append(f"{policy.name}: {str(e)}")
                    
                    # Ensure RLS is enabled on the table
                    try:
                        cursor.execute(config.generate_enable_rls_sql())
                        config.rls_enabled = True
                        config.save()
                    except Exception as e:
                        errors.append(f"Enable RLS on {config.table_name}: {str(e)}")
            
            if applied_count > 0:
                self.message_user(
                    request,
                    f"Successfully applied {applied_count} policies for {queryset.count()} tables."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        apply_all_policies_for_tables.short_description = "Apply all policies for selected tables"
        
        def remove_all_policies_for_tables(self, request, queryset):
            """Remove all policies for selected tables."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            removed_count = 0
            errors = []
            
            with connection.cursor() as cursor:
                for config in queryset:
                    # Get all policies for this table
                    policies = RLSPolicy.objects.filter(table_name=config.table_name)
                    
                    for policy in policies:
                        try:
                            cursor.execute(policy.generate_drop_policy_sql())
                            removed_count += 1
                        except Exception as e:
                            errors.append(f"{policy.name}: {str(e)}")
            
            if removed_count > 0:
                self.message_user(
                    request,
                    f"Successfully removed {removed_count} policies from {queryset.count()} tables."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        remove_all_policies_for_tables.short_description = "Remove all policies for selected tables"
        
        def check_table_status(self, request, queryset):
            """Check RLS status for selected tables."""
            db_engine = connection.settings_dict.get('ENGINE', '')
            if 'postgresql' not in db_engine and 'postgis' not in db_engine:
                self.message_user(
                    request,
                    "RLS is only supported on PostgreSQL databases.",
                    level='error'
                )
                return
            
            status_messages = []
            
            with connection.cursor() as cursor:
                for config in queryset:
                    # Check if table exists and RLS status
                    cursor.execute("""
                        SELECT relrowsecurity, relforcerowsecurity
                        FROM pg_class
                        WHERE relname = %s
                    """, [config.table_name])
                    
                    result = cursor.fetchone()
                    if result:
                        rls_enabled, force_rls = result
                        
                        # Count policies in database
                        cursor.execute("""
                            SELECT COUNT(*) FROM pg_policies
                            WHERE tablename = %s
                        """, [config.table_name])
                        
                        db_policy_count = cursor.fetchone()[0]
                        
                        # Count policies in Django
                        django_policy_count = RLSPolicy.objects.filter(
                            table_name=config.table_name,
                            is_active=True
                        ).count()
                        
                        rls_status = "✓ Enabled" if rls_enabled else "✗ Disabled"
                        force_status = " (FORCE)" if force_rls else ""
                        
                        status_messages.append(
                            f"<strong>{config.table_name}</strong>: "
                            f"RLS {rls_status}{force_status} | "
                            f"Policies: {db_policy_count} in DB, {django_policy_count} in Django"
                        )
                    else:
                        status_messages.append(
                            f"<strong>{config.table_name}</strong>: ⚠ Table not found in database"
                        )
            
            self.message_user(
                request,
                format_html('<br>'.join(status_messages))
            )
        
        check_table_status.short_description = "Check RLS status for selected tables"


# ============================================================================
# AZURE AD CONFIGURATION ADMIN
# ============================================================================

if CONFIG_AVAILABLE:
    
    @admin.register(AzureADConfiguration)
    class AzureADConfigurationAdmin(admin.ModelAdmin):
        """Admin for managing Azure AD configurations."""
        
        list_display = [
            'name_badge',
            'tenant_id_masked',
            'client_id_masked',
            'token_version',
            'validate_settings',
            'is_active_badge',
            'updated_at'
        ]
        list_filter = ['is_active', 'token_version', 'created_at']
        search_fields = ['name', 'tenant_id', 'client_id', 'description']
        readonly_fields = [
            'created_at', 
            'updated_at', 
            'created_by',
            'tenant_id_reveal',
            'client_id_reveal', 
            'client_secret_reveal'
        ]
        
        # Base fieldsets for add form (shows regular input fields)
        add_fieldsets = [
            ('Configuration Name', {
                'fields': ['name', 'description', 'is_active']
            }),
            ('Azure AD Credentials', {
                'fields': [
                    'tenant_id',
                    'client_id',
                    'client_secret'
                ],
                'description': 'Find these values in Azure Portal > App registrations.'
            }),
            ('Token Validation Settings', {
                'fields': [
                    'token_version',
                    'validate_audience',
                    'validate_issuer',
                    'token_leeway'
                ],
                'classes': ['collapse']
            }),
            ('Exempt Paths', {
                'fields': ['exempt_paths'],
                'description': 'URL patterns to exempt from authentication (e.g., ["/admin/", "/health/"])',
                'classes': ['collapse']
            }),
        ]
        
        # Change fieldsets for edit form (shows reveal fields instead of inputs)
        change_fieldsets = [
            ('Configuration Name', {
                'fields': ['name', 'description', 'is_active']
            }),
            ('Azure AD Credentials', {
                'fields': [
                    'tenant_id_reveal',
                    'client_id_reveal',
                    'client_secret_reveal',
                    'client_secret'
                ],
                'description': 'Find these values in Azure Portal > App registrations. Click the eye icon to reveal masked values. Update the Client Secret field below to change it.'
            }),
            ('Token Validation Settings', {
                'fields': [
                    'token_version',
                    'validate_audience',
                    'validate_issuer',
                    'token_leeway'
                ],
                'classes': ['collapse']
            }),
            ('Exempt Paths', {
                'fields': ['exempt_paths'],
                'description': 'URL patterns to exempt from authentication (e.g., ["/admin/", "/health/"])',
                'classes': ['collapse']
            }),
            ('Metadata', {
                'fields': ['created_by', 'created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]
        
        actions = ['activate_configuration', 'test_configuration']
        
        def get_fieldsets(self, request, obj=None):
            """Return different fieldsets for add vs change forms."""
            if obj is None:
                # Add form - show regular input fields
                return self.add_fieldsets
            else:
                # Change form - show reveal fields with masked values
                return self.change_fieldsets
        
        def name_badge(self, obj):
            """Display name with active badge."""
            if obj.is_active:
                return format_html(
                    '<strong>{}</strong> <span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">ACTIVE</span>',
                    obj.name
                )
            return format_html('<span>{}</span>', obj.name)
        name_badge.short_description = 'Name'
        
        def tenant_id_masked(self, obj):
            """Display masked tenant ID."""
            if obj.tenant_id:
                return format_html(
                    '<span class="masked-field">••••••••-••••-••••-••••-{}</span>',
                    obj.tenant_id[-12:]
                )
            return '-'
        tenant_id_masked.short_description = 'Tenant ID'
        
        def client_id_masked(self, obj):
            """Display masked client ID."""
            if obj.client_id:
                return format_html(
                    '<span class="masked-field">••••••••-••••-••••-••••-{}</span>',
                    obj.client_id[-12:]
                )
            return '-'
        client_id_masked.short_description = 'Client ID'
        
        def tenant_id_reveal(self, obj):
            """Display tenant ID with reveal button."""
            if obj and obj.pk and obj.tenant_id:
                return format_html(
                    '<div class="sensitive-field-wrapper">' 
                    '<span class="sensitive-field masked" data-value="{}" id="tenant_id_{}">' 
                    '••••••••-••••-••••-••••-{}</span>' 
                    '<button type="button" class="reveal-btn" data-field-id="tenant_id_{}" '
                    'title="Click to reveal">' 
                    '<span class="eye-icon">👁</span>' 
                    '</button>' 
                    '</div>',
                    obj.tenant_id,
                    obj.pk,
                    obj.tenant_id[-12:],
                    obj.pk
                )
            return format_html(
                '<span style="color: #999;">Will be set after saving</span>'
            )
        tenant_id_reveal.short_description = 'Tenant ID'
        
        def client_id_reveal(self, obj):
            """Display client ID with reveal button."""
            if obj and obj.pk and obj.client_id:
                return format_html(
                    '<div class="sensitive-field-wrapper">' 
                    '<span class="sensitive-field masked" data-value="{}" id="client_id_{}">' 
                    '••••••••-••••-••••-••••-{}</span>' 
                    '<button type="button" class="reveal-btn" data-field-id="client_id_{}" '
                    'title="Click to reveal">' 
                    '<span class="eye-icon">👁</span>' 
                    '</button>' 
                    '</div>',
                    obj.client_id,
                    obj.pk,
                    obj.client_id[-12:],
                    obj.pk
                )
            return format_html(
                '<span style="color: #999;">Will be set after saving</span>'
            )
        client_id_reveal.short_description = 'Client ID'
        
        def client_secret_reveal(self, obj):
            """Display client secret with reveal button."""
            if obj and obj.pk and obj.client_secret:
                masked_length = min(len(obj.client_secret), 40)
                return format_html(
                    '<div class="sensitive-field-wrapper">' 
                    '<span class="sensitive-field masked" data-value="{}" id="client_secret_{}">' 
                    '{}</span>' 
                    '<button type="button" class="reveal-btn" data-field-id="client_secret_{}" '
                    'title="Click to reveal">' 
                    '<span class="eye-icon">👁</span>' 
                    '</button>' 
                    '</div>',
                    obj.client_secret,
                    obj.pk,
                    '•' * masked_length,
                    obj.pk
                )
            return format_html(
                '<span style="color: #999;">Will be set after saving</span>'
            )
        client_secret_reveal.short_description = 'Client Secret'
        
        def validate_settings(self, obj):
            """Display validation settings as badges."""
            badges = []
            if obj.validate_audience:
                badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">AUD</span>')
            if obj.validate_issuer:
                badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ISS</span>')
            if obj.token_leeway > 0:
                badges.append(f'<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Leeway: {obj.token_leeway}s</span>')
            
            return format_html(' '.join(badges)) if badges else '-'
        validate_settings.short_description = 'Validation'
        
        def is_active_badge(self, obj):
            """Display active status as badge."""
            if obj.is_active:
                return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
            return format_html('<span style="color: #6c757d;">○ Inactive</span>')
        is_active_badge.short_description = 'Status'
        
        def activate_configuration(self, request, queryset):
            """Activate selected configuration (deactivates others)."""
            if queryset.count() != 1:
                self.message_user(
                    request,
                    "Please select exactly one configuration to activate.",
                    level='error'
                )
                return
            
            config = queryset.first()
            
            # Deactivate all others
            AzureADConfiguration.objects.exclude(pk=config.pk).update(is_active=False)
            
            # Activate selected
            config.is_active = True
            config.save()
            
            # Log history
            AzureADConfigurationHistory.objects.create(
                configuration=config,
                configuration_name=config.name,
                action='activated',
                tenant_id=config.tenant_id,
                client_id=config.client_id,
                changed_by=request.user.username if request.user.is_authenticated else 'unknown',
                details=f"Activated via admin action"
            )
            
            self.message_user(
                request,
                f"Configuration '{config.name}' is now active."
            )
        
        activate_configuration.short_description = "Activate selected configuration"
        
        def test_configuration(self, request, queryset):
            """Test selected configuration by attempting to create validator."""
            errors = []
            success_count = 0
            
            for config in queryset:
                try:
                    from hub_auth_client import MSALTokenValidator
                    
                    validator = MSALTokenValidator(**config.get_validator_config())
                    
                    # Try to get signing keys to verify connectivity
                    if hasattr(validator, '_get_signing_keys'):
                        keys = validator._get_signing_keys()
                        if keys:
                            success_count += 1
                        else:
                            errors.append(f"{config.name}: No signing keys found")
                    else:
                        success_count += 1
                        
                except Exception as e:
                    errors.append(f"{config.name}: {str(e)}")
            
            if success_count > 0:
                self.message_user(
                    request,
                    f"Successfully tested {success_count} configuration(s)."
                )
            
            if errors:
                self.message_user(
                    request,
                    f"Errors: {'; '.join(errors)}",
                    level='error'
                )
        
        test_configuration.short_description = "Test selected configurations"
        
        def save_model(self, request, obj, form, change):
            """Track who created/updated the configuration."""
            if not change:  # Creating new
                obj.created_by = request.user.username if request.user.is_authenticated else 'unknown'
                action = 'created'
            else:
                action = 'updated'
            
            # Check if is_active is being changed
            if change and 'is_active' in form.changed_data:
                action = 'activated' if obj.is_active else 'deactivated'
            
            super().save_model(request, obj, form, change)
            
            # Log history
            AzureADConfigurationHistory.objects.create(
                configuration=obj,
                configuration_name=obj.name,
                action=action,
                tenant_id=obj.tenant_id,
                client_id=obj.client_id,
                changed_by=request.user.username if request.user.is_authenticated else 'unknown',
                details=f"Modified via admin interface"
            )
        
        class Media:
            css = {
                'all': ('admin/css/azure_ad_config.css',)
            }
            js = ('admin/js/azure_ad_config.js',)
    
    
    @admin.register(AzureADConfigurationHistory)
    class AzureADConfigurationHistoryAdmin(admin.ModelAdmin):
        """Admin for viewing Azure AD configuration history."""
        
        list_display = [
            'configuration_name',
            'action_badge',
            'tenant_id_masked',
            'client_id_masked',
            'changed_by',
            'changed_at'
        ]
        list_filter = ['action', 'changed_at']
        search_fields = ['configuration_name', 'tenant_id', 'client_id', 'changed_by']
        readonly_fields = [
            'configuration',
            'configuration_name',
            'action',
            'tenant_id',
            'client_id',
            'changed_by',
            'changed_at',
            'details'
        ]
        
        def has_add_permission(self, request):
            """Prevent manual creation of history records."""
            return False
        
        def has_change_permission(self, request, obj=None):
            """Prevent editing history records."""
            return False
        
        def has_delete_permission(self, request, obj=None):
            """Allow deletion to clean up old history."""
            return True
        
        def action_badge(self, obj):
            """Display action as colored badge."""
            colors = {
                'created': '#28a745',
                'updated': '#17a2b8',
                'activated': '#28a745',
                'deactivated': '#6c757d',
                'deleted': '#dc3545',
            }
            color = colors.get(obj.action, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                color,
                obj.get_action_display()
            )
        action_badge.short_description = 'Action'
        
        def tenant_id_masked(self, obj):
            """Display masked tenant ID."""
            if obj.tenant_id:
                return format_html(
                    '<span class="masked-field">••••••••-••••-••••-••••-{}</span>',
                    obj.tenant_id[-12:]
                )
            return '-'
        tenant_id_masked.short_description = 'Tenant ID'
        
        def client_id_masked(self, obj):
            """Display masked client ID."""
            if obj.client_id:
                return format_html(
                    '<span class="masked-field">••••••••-••••-••••-••••-{}</span>',
                    obj.client_id[-12:]
                )
            return '-'
        client_id_masked.short_description = 'Client ID'


@admin.register(APIEndpointMapping)
class APIEndpointMappingAdmin(admin.ModelAdmin):
    """
    Admin interface to dynamically display API endpoint to serializer mappings.
    
    This admin automatically discovers ViewSets from the installed app and
    displays their URL patterns, actions, and associated serializers.
    Enhanced with features from EndpointPermissionAdmin for creating permissions.
    """
    
    change_list_template = "admin/hub_auth_client/endpointpermission/change_list.html"
    
    def has_add_permission(self, request):
        """Disable add permission since this is read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete permission since this is read-only."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission since this is read-only."""
        return False
    
    def get_urls(self):
        """Add custom URLs for discover and create actions."""
        urls = super().get_urls()
        custom_urls = [
            path('discover-unsecured/', self.admin_site.admin_view(self.discover_unsecured_view), name='discover_unsecured_endpoints'),
            path('create-permissions/', self.admin_site.admin_view(self.create_endpoint_permissions_view), name='create_endpoint_permissions'),
        ]
        return custom_urls + urls
    
    def _discover_viewsets(self):
        """
        Dynamically discover all ViewSets from installed apps.
        
        Returns a list of endpoint mapping dictionaries.
        """
        from django.conf import settings
        from django.urls import get_resolver
        from rest_framework import viewsets
        import inspect
        import importlib
        
        endpoints = []
        order = 1
        
        # Get all installed apps
        for app_config in settings.INSTALLED_APPS:
            if app_config.startswith('django.') or app_config.startswith('rest_framework'):
                continue
                
            try:
                # Try to import api_views module
                try:
                    views_module = importlib.import_module(f"{app_config}.api_views")
                except ImportError:
                    try:
                        views_module = importlib.import_module(f"{app_config}.views")
                    except ImportError:
                        continue
                
                # Find all ViewSet classes in the module
                for name, obj in inspect.getmembers(views_module, inspect.isclass):
                    if not issubclass(obj, viewsets.ViewSetMixin) or obj == viewsets.ViewSetMixin:
                        continue
                    
                    if obj.__module__ != views_module.__name__:
                        continue
                    
                    # Get the base URL from the router registration
                    base_url = self._get_base_url_for_viewset(obj, app_config)
                    if not base_url:
                        continue
                    
                    # Get serializer information
                    serializer_info = self._get_serializer_info(obj)
                    
                    # Standard CRUD endpoints
                    if hasattr(obj, 'queryset') or hasattr(obj, 'get_queryset'):
                        # LIST
                        endpoints.append({
                            'viewset': name,
                            'url': f'GET {base_url}/',
                            'action': 'List all items',
                            'serializer': serializer_info.get('list', serializer_info.get('default', '(auto)')),
                            'http_method': 'GET',
                            'order': order,
                            'app': app_config.split('.')[-1]
                        })
                        order += 1
                        
                        # RETRIEVE
                        endpoints.append({
                            'viewset': name,
                            'url': f'GET {base_url}/{{pk}}/',
                            'action': 'Retrieve single item',
                            'serializer': serializer_info.get('retrieve', serializer_info.get('default', '(auto)')),
                            'http_method': 'GET',
                            'order': order,
                            'app': app_config.split('.')[-1]
                        })
                        order += 1
                        
                        # CREATE (if not ReadOnly)
                        if not issubclass(obj, viewsets.ReadOnlyModelViewSet):
                            endpoints.append({
                                'viewset': name,
                                'url': f'POST {base_url}/',
                                'action': 'Create item',
                                'serializer': serializer_info.get('create', serializer_info.get('default', '(auto)')),
                                'http_method': 'POST',
                                'order': order,
                                'app': app_config.split('.')[-1]
                            })
                            order += 1
                            
                            # UPDATE
                            endpoints.append({
                                'viewset': name,
                                'url': f'PUT/PATCH {base_url}/{{pk}}/',
                                'action': 'Update item',
                                'serializer': serializer_info.get('update', serializer_info.get('default', '(auto)')),
                                'http_method': 'PUT/PATCH',
                                'order': order,
                                'app': app_config.split('.')[-1]
                            })
                            order += 1
                            
                            # DELETE
                            endpoints.append({
                                'viewset': name,
                                'url': f'DELETE {base_url}/{{pk}}/',
                                'action': 'Delete item',
                                'serializer': '(none)',
                                'http_method': 'DELETE',
                                'order': order,
                                'app': app_config.split('.')[-1]
                            })
                            order += 1
                    
                    # Custom actions
                    for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                        if hasattr(method, 'mapping'):  # This is a @action decorated method
                            action_detail = getattr(method, 'detail', False)
                            action_methods = list(getattr(method, 'mapping', {}).keys())
                            action_url_path = getattr(method, 'url_path', method_name)
                            
                            if action_detail:
                                url = f"{base_url}/{{pk}}/{action_url_path}/"
                            else:
                                url = f"{base_url}/{action_url_path}/"
                            
                            method_str = '/'.join([m.upper() for m in action_methods])
                            
                            endpoints.append({
                                'viewset': name,
                                'url': f'{method_str} {url}',
                                'action': f'Custom action - {method_name}',
                                'serializer': serializer_info.get(method_name, serializer_info.get('default', '(auto)')) + ' ✅',
                                'http_method': method_str,
                                'order': order,
                                'app': app_config.split('.')[-1]
                            })
                            order += 1
                
            except Exception as e:
                # Skip apps that can't be imported
                continue
        
        return endpoints
    
    def _get_base_url_for_viewset(self, viewset_class, app_name):
        """Try to determine the base URL for a ViewSet by inspecting URLs."""
        from django.conf import settings
        import importlib
        
        try:
            # Try to import the app's urls module
            urls_module = importlib.import_module(f"{app_name}.urls")
            
            # Look for router registrations
            if hasattr(urls_module, 'router'):
                router = urls_module.router
                for prefix, viewset, basename in router.registry:
                    if viewset == viewset_class:
                        return f'/api/{prefix}'
            
            # Fallback: use the viewset name to guess
            viewset_name = viewset_class.__name__.replace('ViewSet', '').lower()
            if 'employee' in viewset_name.lower():
                if 'position' in viewset_name.lower():
                    return '/api/positions'
                elif 'supervisor' in viewset_name.lower():
                    return '/api/supervisors'
                else:
                    return '/api/employees'
            
            return f'/api/{viewset_name}s'
            
        except:
            return None
    
    def _get_serializer_info(self, viewset_class):
        """Extract serializer information from a ViewSet class."""
        import inspect
        
        serializers = {}
        
        # Check for serializer_class attribute
        if hasattr(viewset_class, 'serializer_class'):
            serializers['default'] = viewset_class.serializer_class.__name__
        
        # Check for get_serializer_class method
        if hasattr(viewset_class, 'get_serializer_class'):
            try:
                # Try to parse the get_serializer_class method
                source = inspect.getsource(viewset_class.get_serializer_class)
                
                # Look for action-specific serializers
                if "'list'" in source or '"list"' in source:
                    # Try to extract serializer name from source
                    import re
                    list_match = re.search(r"'list'.*?return\s+(\w+)", source, re.DOTALL)
                    if list_match:
                        serializers['list'] = list_match.group(1)
                
                if "'retrieve'" in source or '"retrieve"' in source:
                    retrieve_match = re.search(r"'retrieve'.*?return\s+(\w+)", source, re.DOTALL)
                    if retrieve_match:
                        serializers['retrieve'] = retrieve_match.group(1)
                
                if "'names'" in source or '"names"' in source:
                    names_match = re.search(r"'names'.*?return\s+(\w+)", source, re.DOTALL)
                    if names_match:
                        serializers['names'] = names_match.group(1)
                        
            except:
                pass
        
        # Check custom action methods for serializer_class
        for method_name, method in inspect.getmembers(viewset_class, inspect.isfunction):
            if hasattr(method, 'mapping'):  # @action decorator
                if hasattr(method, 'kwargs') and 'serializer_class' in method.kwargs:
                    serializers[method_name] = method.kwargs['serializer_class'].__name__
        
        return serializers
    
    def discover_unsecured_view(self, request):
        """Custom view to discover unsecured endpoints with filters."""
        from django.core.management import call_command
        from django.shortcuts import render
        from io import StringIO
        import json
        from .admin_helpers import humanize_url_pattern
        
        # Get filter parameters - default to showing ALL endpoints
        unsecured_only = request.GET.get('unsecured_only', '0') == '1'  # Default: show all
        ignore_admin = request.GET.get('ignore_admin', '1') == '1'       # Default: ignore admin
        ignore_static = request.GET.get('ignore_static', '1') == '1'     # Default: ignore static
        
        output = StringIO()
        
        try:
            # Build command arguments
            cmd_args = ['--format=json']
            if unsecured_only:
                cmd_args.append('--unsecured-only')
            
            # Call the list_endpoints management command
            call_command('list_endpoints', *cmd_args, stdout=output)
            
            result = output.getvalue()
            endpoints = json.loads(result) if result.strip() else []
            
            # Apply filters
            filtered_endpoints = []
            for endpoint in endpoints:
                url_pattern = endpoint.get('url_pattern', '')
                view_name = endpoint.get('view_name', '')
                
                # Filter out admin views if requested
                if ignore_admin:
                    if '/admin/' in url_pattern or 'admin' in view_name.lower():
                        continue
                
                # Filter out static/media URLs if requested
                if ignore_static:
                    if any(pattern in url_pattern for pattern in ['/static/', '/media/', '__debug__']):
                        continue
                
                # Add humanized URL pattern
                endpoint['url_pattern_readable'] = humanize_url_pattern(url_pattern)
                
                filtered_endpoints.append(endpoint)
            
            # Render custom template
            context = {
                'endpoints': filtered_endpoints,
                'unsecured_only': unsecured_only,
                'ignore_admin': ignore_admin,
                'ignore_static': ignore_static,
                'title': 'Discover Unsecured Endpoints',
                'site_title': self.admin_site.site_title,
                'site_header': self.admin_site.site_header,
            }
            
            return render(request, 'admin/hub_auth_client/endpointpermission/discover_endpoints.html', context)
            
        except Exception as e:
            self.message_user(
                request,
                f"Error discovering endpoints: {str(e)}",
                level=messages.ERROR
            )
            return redirect('admin:hub_auth_client_apiendpointmapping_changelist')
    
    def create_endpoint_permissions_view(self, request):
        """Bulk create endpoint permissions from selected endpoints."""
        if request.method != 'POST':
            return redirect('admin:discover_unsecured_endpoints')
        
        selected_endpoints = request.POST.getlist('endpoints')
        
        if not selected_endpoints:
            self.message_user(
                request,
                "No endpoints selected.",
                level=messages.WARNING
            )
            return redirect('admin:discover_unsecured_endpoints')
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        for endpoint_data in selected_endpoints:
            try:
                # Parse endpoint data: url_pattern|http_methods|view_name|serializer_class
                parts = endpoint_data.split('|')
                url_pattern = parts[0] if len(parts) > 0 else ''
                http_methods = parts[1] if len(parts) > 1 else 'GET'
                view_name = parts[2] if len(parts) > 2 else ''
                serializer_class = parts[3] if len(parts) > 3 else ''
                
                # Check if permission already exists
                if EndpointPermission.objects.filter(url_pattern=url_pattern).exists():
                    skipped_count += 1
                    continue
                
                # Create unique name from URL pattern and view name
                # Extract action or endpoint identifier from URL
                url_parts = [p for p in url_pattern.replace('^', '').replace('$', '').split('/') if p and not p.startswith('?P<')]
                
                if view_name:
                    # Use view class name + URL-based identifier
                    view_class = view_name.split('.')[-1]
                    if len(url_parts) > 1:
                        # e.g., "EmployeeViewSet-active" or "EmployeeViewSet-names"
                        action = url_parts[-1].replace('.(?P<format>[a-z0-9]+)/?', '')
                        name = f"{view_class}-{action}"
                    else:
                        # e.g., "EmployeeViewSet-list"
                        name = f"{view_class}-list"
                else:
                    # Fallback to URL pattern-based name
                    name = url_pattern.replace('/', '_').replace('^', '').replace('$', '').strip('_')
                
                if not name or len(name) < 3:
                    name = f"endpoint_{created_count + 1}"
                
                # Ensure uniqueness by checking if name exists
                base_name = name
                counter = 1
                while EndpointPermission.objects.filter(name=name).exists():
                    name = f"{base_name}_{counter}"
                    counter += 1
                
                # Create endpoint permission
                EndpointPermission.objects.create(
                    name=name,
                    url_pattern=url_pattern,
                    http_methods=http_methods,
                    description=f"Auto-created from {view_name}" if view_name else "Auto-created endpoint",
                    is_active=False,  # Start as inactive until configured
                    priority=100
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"{url_pattern}: {str(e)}")
        
        # Show results
        if created_count > 0:
            self.message_user(
                request,
                f"Successfully created {created_count} endpoint permission(s).",
                level=messages.SUCCESS
            )
        
        if skipped_count > 0:
            self.message_user(
                request,
                f"Skipped {skipped_count} endpoint(s) - already exist.",
                level=messages.INFO
            )
        
        if errors:
            self.message_user(
                request,
                f"Errors: {'; '.join(errors[:5])}",
                level=messages.ERROR
            )
        
        # Redirect back to the changelist
        return redirect('admin:hub_auth_client_apiendpointmapping_changelist')
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist view to display endpoint mappings."""
        from django.contrib.admin.views.main import ChangeList
        
        class EndpointChangeList(ChangeList):
            """Custom ChangeList that uses discovered endpoint data."""
            
            def get_results(self, request):
                """Override to use dynamically discovered data."""
                # Create mock objects from discovered endpoints
                class MockMeta:
                    """Mock _meta attribute for Django admin compatibility."""
                    model_name = 'apiendpointmapping'
                    app_label = 'hub_auth_client'
                    pk = type('MockPK', (), {'attname': 'pk'})()
                    
                    def get_field(self, field_name):
                        """Mock get_field method for Django admin compatibility."""
                        from django.db import models
                        
                        # Return mock field objects for our display fields
                        class MockField:
                            def __init__(self, name):
                                self.name = name
                                self.attname = name
                                self.verbose_name = name.replace('_', ' ').title()
                                self.primary_key = (name == 'pk')
                                self.editable = False
                                self.blank = True
                                self.null = True
                                self.is_relation = False
                                self.many_to_many = False
                                self.one_to_many = False
                                self.one_to_one = False
                                self.remote_field = None
                                self.related_model = None
                                self.auto_created = False
                                self.concrete = True
                                self.column = name
                                self.empty_values = (None, '', [], (), {})
                                # Additional attributes that Django admin may check
                                self.choices = None
                                self.flatchoices = None
                                self.help_text = ''
                                self.db_column = None
                                self.db_tablespace = None
                                self.unique = False
                                self.unique_for_date = None
                                self.unique_for_month = None
                                self.unique_for_year = None
                                self.validators = []
                                self.error_messages = {}
                                self.db_index = False
                                self.default = models.NOT_PROVIDED
                                self.max_length = None
                                self.rel = None  # Deprecated alias for remote_field
                                self.has_default = lambda: False
                            
                            def value_from_object(self, obj):
                                return getattr(obj, self.name, None)
                        
                        return MockField(field_name)
                
                class EndpointRow:
                    _meta = MockMeta()
                    
                    def __init__(self, data):
                        self.pk = data['order']
                        self.viewset = data['viewset']
                        self.url = data['url']
                        self.action = data['action']
                        self.serializer = data['serializer']
                        self.http_method = data['http_method']
                        self.app = data.get('app', 'unknown')
                        
                        # Pre-compute display values to avoid method reference issues
                        from django.utils.html import format_html
                        
                        # Compute viewset_display
                        viewset_colors = {
                            'EmployeeViewSet': '#2e7d32',
                            'EmployeePositionViewSet': '#1565c0',
                            'SupervisorViewSet': '#e65100',
                        }
                        color = viewset_colors.get(self.viewset, '#5e35b1')
                        self.viewset_display = format_html(
                            '<strong style="color: {};">{}</strong>',
                            color,
                            self.viewset
                        )
                        
                        # Compute url_display
                        method_colors = {
                            'GET': '#0d47a1',
                            'POST': '#2e7d32',
                            'PUT/PATCH': '#f57c00',
                            'DELETE': '#c62828',
                        }
                        color = method_colors.get(self.http_method, '#000000')
                        self.url_display = format_html(
                            '<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; color: {}; font-weight: bold;">{}</code>',
                            color,
                            self.url
                        )
                        
                        # Compute action_display
                        self.action_display = self.action
                        
                        # Compute serializer_display
                        if self.serializer == '(none)':
                            self.serializer_display = format_html(
                                '<em style="color: #9e9e9e;">{}</em>',
                                self.serializer
                            )
                        elif '✅' in self.serializer:
                            self.serializer_display = format_html(
                                '<strong style="color: #2e7d32;">{}</strong>',
                                self.serializer
                            )
                        elif '(auto)' in self.serializer:
                            self.serializer_display = format_html(
                                '<em style="color: #757575;">{}</em>',
                                self.serializer
                            )
                        else:
                            self.serializer_display = format_html(
                                '<code style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px;">{}</code>',
                                self.serializer
                            )
                        
                        # Compute app_display
                        self.app_display = format_html(
                            '<span style="background: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
                            self.app
                        )
                
                # Discover endpoints dynamically
                endpoint_data = request._endpoint_data
                self.result_list = [EndpointRow(data) for data in endpoint_data]
                self.result_count = len(self.result_list)
                self.full_result_count = self.result_count
                self.show_admin_actions = False
                self.show_full_result_count = True
                
                # Pagination attributes required by Django admin templates
                self.can_show_all = True
                self.show_all = False
                self.multi_page = False  # No pagination for this view
                self.paginator = None
        
        # Store discovered data in request
        request._endpoint_data = self._discover_viewsets()
        
        # Override get_changelist to use our custom ChangeList
        original_get_changelist = self.get_changelist
        self.get_changelist = lambda request: EndpointChangeList
        
        # Add custom context for action buttons
        if extra_context is None:
            extra_context = {}
        
        extra_context['show_discover_button'] = True
        extra_context['discover_url'] = reverse('admin:discover_unsecured_endpoints')
        
        try:
            return super().changelist_view(request, extra_context)
        finally:
            self.get_changelist = original_get_changelist
    
    def viewset_display(self, obj):
        """Display the ViewSet name with formatting."""
        return obj.viewset_display
    viewset_display.short_description = 'ViewSet'
    
    def url_display(self, obj):
        """Display the URL with formatted HTTP method."""
        return obj.url_display
    url_display.short_description = 'URL Pattern'
    
    def action_display(self, obj):
        """Display the action description."""
        return obj.action_display
    action_display.short_description = 'Action'
    
    def serializer_display(self, obj):
        """Display the serializer with highlighting."""
        return obj.serializer_display
    serializer_display.short_description = 'Expected Serializer'
    
    def app_display(self, obj):
        """Display the app name."""
        return obj.app_display
    app_display.short_description = 'App'
    
    list_display = ('viewset_display', 'url_display', 'action_display', 'serializer_display', 'app_display')
    list_display_links = None
    
    class Media:
        css = {
            'all': ('admin/css/endpoint_mappings.css',)
        }

