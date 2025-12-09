"""
Reusable admin mixins for common functionality.
"""

from django.utils.html import format_html
from .admin_helpers import (
    format_active_badge,
    format_count_with_requirement,
    format_masked_guid,
    format_sensitive_field_with_reveal,
    format_validation_badges,
    format_badge,
    format_sql_preview,
    humanize_url_pattern
)


class ActiveBadgeMixin:
    """Mixin to add is_active_badge display method."""
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        return format_active_badge(obj.is_active)
    is_active_badge.short_description = 'Status'


class EndpointCountMixin:
    """Mixin to add endpoint_count display method."""
    
    def endpoint_count(self, obj):
        """Count endpoints using this scope/role."""
        count = obj.endpoints.filter(is_active=True).count()
        return format_html(f'<span>{count} endpoints</span>')
    endpoint_count.short_description = 'Used By'


class ScopeCountMixin:
    """Mixin to add scope_count display method."""
    
    def scope_count(self, obj):
        """Count required scopes."""
        count = obj.required_scopes.filter(is_active=True).count()
        requirement = getattr(obj, 'scope_requirement', '')
        return format_count_with_requirement(count, requirement)
    scope_count.short_description = 'Scopes'


class RoleCountMixin:
    """Mixin to add role_count display method."""
    
    def role_count(self, obj):
        """Count required roles."""
        count = obj.required_roles.filter(is_active=True).count()
        requirement = getattr(obj, 'role_requirement', '')
        return format_count_with_requirement(count, requirement)
    role_count.short_description = 'Roles'


class MaskedFieldMixin:
    """Mixin for Azure AD credential masking."""
    
    def tenant_id_masked(self, obj):
        """Display masked tenant ID."""
        return format_masked_guid(obj.tenant_id)
    tenant_id_masked.short_description = 'Tenant ID'
    
    def client_id_masked(self, obj):
        """Display masked client ID."""
        return format_masked_guid(obj.client_id)
    client_id_masked.short_description = 'Client ID'


class SensitiveFieldRevealMixin:
    """Mixin for revealing sensitive fields with eye button."""
    
    def tenant_id_reveal(self, obj):
        """Display tenant ID with reveal button."""
        return format_sensitive_field_with_reveal(
            obj.tenant_id if obj and obj.pk else None,
            'tenant_id',
            obj.pk if obj else None
        )
    tenant_id_reveal.short_description = ''
    
    def client_id_reveal(self, obj):
        """Display client ID with reveal button."""
        return format_sensitive_field_with_reveal(
            obj.client_id if obj and obj.pk else None,
            'client_id',
            obj.pk if obj else None
        )
    client_id_reveal.short_description = ''
    
    def client_secret_reveal(self, obj):
        """Display client secret with reveal button."""
        return format_sensitive_field_with_reveal(
            obj.client_secret if obj and obj.pk else None,
            'client_secret',
            obj.pk if obj else None,
            visible_chars=40
        )
    client_secret_reveal.short_description = ''


class AzureADConfigBadgeMixin:
    """Mixin for Azure AD configuration badges."""
    
    def name_badge(self, obj):
        """Display name with active badge."""
        if obj.is_active:
            return format_html(
                '<strong>{}</strong> {}',
                obj.name,
                format_badge('ACTIVE')
            )
        return format_html('<span>{}</span>', obj.name)
    name_badge.short_description = 'Name'
    
    def validate_settings(self, obj):
        """Display validation settings as badges."""
        return format_validation_badges(
            obj.validate_audience,
            obj.validate_issuer,
            obj.token_leeway
        )
    validate_settings.short_description = 'Validation'


class RLSStatusMixin:
    """Mixin for RLS status display."""
    
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


class SQLPreviewMixin:
    """Mixin for SQL preview display."""
    
    def preview_sql(self, obj):
        """Preview the generated SQL for this policy."""
        if obj.pk:
            sql = obj.generate_create_policy_sql()
            return format_sql_preview(sql)
        return "Save policy to preview SQL"
    preview_sql.short_description = 'SQL Preview'


class URLPatternMixin:
    """Mixin for displaying URL patterns with human-readable descriptions."""
    
    def url_pattern_display(self, obj):
        """Display URL pattern with human-readable description."""
        if not obj.url_pattern:
            return '-'
        
        readable = humanize_url_pattern(obj.url_pattern)
        
        return format_html(
            '<div title="Regex: {}">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.url_pattern,
            obj.url_pattern,
            readable
        )
    url_pattern_display.short_description = 'URL Pattern'
    
    def url_pattern_readable(self, obj):
        """Display only the human-readable URL pattern."""
        if not obj.url_pattern:
            return '-'
        return humanize_url_pattern(obj.url_pattern)
    url_pattern_readable.short_description = 'URL Pattern (Readable)'
