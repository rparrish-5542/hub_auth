"""
Django admin configuration for scope and permission management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import connection
from .models import ScopeDefinition, RoleDefinition, EndpointPermission

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
    
    list_display = ['name', 'category', 'is_active', 'is_active_badge', 'endpoint_count', 'updated_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'category']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
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
class EndpointPermissionAdmin(admin.ModelAdmin):
    """Admin for managing endpoint permissions."""
    
    list_display = [
        'name',
        'url_pattern',
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
        
        actions = [
            'enable_rls_on_tables',
            'disable_rls_on_tables',
            'apply_all_policies_for_tables',
            'remove_all_policies_for_tables',
            'check_table_status',
        ]
        
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
            'tenant_id_short',
            'client_id_short',
            'token_version',
            'validate_settings',
            'is_active_badge',
            'updated_at'
        ]
        list_filter = ['is_active', 'token_version', 'created_at']
        search_fields = ['name', 'tenant_id', 'client_id', 'description']
        readonly_fields = ['created_at', 'updated_at']
        
        fieldsets = [
            ('Configuration Name', {
                'fields': ['name', 'description', 'is_active']
            }),
            ('Azure AD Credentials', {
                'fields': ['tenant_id', 'client_id', 'client_secret'],
                'description': 'Find these values in Azure Portal > App registrations'
            }),
            ('Token Validation Settings', {
                'fields': [
                    'token_version',
                    'allowed_audiences',
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
        
        def name_badge(self, obj):
            """Display name with active badge."""
            if obj.is_active:
                return format_html(
                    '<strong>{}</strong> <span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">ACTIVE</span>',
                    obj.name
                )
            return format_html('<span>{}</span>', obj.name)
        name_badge.short_description = 'Name'
        
        def tenant_id_short(self, obj):
            """Display shortened tenant ID."""
            return f"{obj.tenant_id[:8]}...{obj.tenant_id[-8:]}"
        tenant_id_short.short_description = 'Tenant ID'
        
        def client_id_short(self, obj):
            """Display shortened client ID."""
            return f"{obj.client_id[:8]}...{obj.client_id[-8:]}"
        client_id_short.short_description = 'Client ID'
        
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
    
    
    @admin.register(AzureADConfigurationHistory)
    class AzureADConfigurationHistoryAdmin(admin.ModelAdmin):
        """Admin for viewing Azure AD configuration history."""
        
        list_display = [
            'configuration_name',
            'action_badge',
            'tenant_id_short',
            'client_id_short',
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
        
        def tenant_id_short(self, obj):
            """Display shortened tenant ID."""
            return f"{obj.tenant_id[:8]}...{obj.tenant_id[-8:]}"
        tenant_id_short.short_description = 'Tenant ID'
        
        def client_id_short(self, obj):
            """Display shortened client ID."""
            return f"{obj.client_id[:8]}...{obj.client_id[-8:]}"
        client_id_short.short_description = 'Client ID'

