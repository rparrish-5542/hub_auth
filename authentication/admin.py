# hub_auth/authentication/admin.py
"""Django admin for authentication models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, TokenValidation, ServiceClient


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for custom User model."""
    
    list_display = [
        'username',
        'email',
        'display_name',
        'azure_status',
        'is_active',
        'is_staff',
        'last_token_validation'
    ]
    
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'last_token_validation',
        'created_at'
    ]
    
    search_fields = [
        'username',
        'email',
        'display_name',
        'azure_ad_object_id',
        'user_principal_name',
        'employee_id'
    ]
    
    readonly_fields = [
        'azure_ad_object_id',
        'azure_ad_tenant_id',
        'last_token_validation',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'display_name')
        }),
        ('Azure AD info', {
            'fields': (
                'azure_ad_object_id',
                'azure_ad_tenant_id',
                'user_principal_name',
                'job_title',
                'department',
                'office_location',
                'employee_id'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'last_token_validation', 'created_at', 'updated_at')
        }),
    )
    
    def azure_status(self, obj):
        """Display Azure AD sync status."""
        if obj.azure_ad_object_id:
            return format_html(
                '<span style="color: green;">✓ Synced</span>'
            )
        return format_html(
            '<span style="color: gray;">Not synced</span>'
        )
    azure_status.short_description = 'Azure AD'


@admin.register(TokenValidation)
class TokenValidationAdmin(admin.ModelAdmin):
    """Admin for token validation logs."""
    
    list_display = [
        'validation_timestamp',
        'service_name',
        'user_display',
        'validation_status',
        'validation_time_ms',
        'ip_address'
    ]
    
    list_filter = [
        'is_valid',
        'service_name',
        'validation_timestamp'
    ]
    
    search_fields = [
        'service_name',
        'token_upn',
        'token_oid',
        'ip_address',
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'user',
        'service_name',
        'ip_address',
        'user_agent',
        'token_oid',
        'token_upn',
        'token_app_id',
        'is_valid',
        'validation_timestamp',
        'error_message',
        'validation_time_ms'
    ]
    
    date_hierarchy = 'validation_timestamp'
    
    def user_display(self, obj):
        """Display user info."""
        if obj.user:
            return obj.user.display_name or obj.user.username
        return obj.token_upn or '-'
    user_display.short_description = 'User'
    
    def validation_status(self, obj):
        """Display validation status with color."""
        if obj.is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
        )
    validation_status.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Logs are created automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Logs are read-only."""
        return False


@admin.register(ServiceClient)
class ServiceClientAdmin(admin.ModelAdmin):
    """Admin for service clients."""
    
    list_display = [
        'name',
        'is_active',
        'stats_display',
        'success_rate',
        'last_used',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'created_at',
        'last_used'
    ]
    
    search_fields = [
        'name',
        'description',
        'api_key'
    ]
    
    readonly_fields = [
        'id',
        'api_key',
        'total_validations',
        'successful_validations',
        'failed_validations',
        'last_used',
        'created_at',
        'updated_at',
        'success_rate_display'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'allowed_origins')
        }),
        ('Statistics', {
            'fields': (
                'total_validations',
                'successful_validations',
                'failed_validations',
                'success_rate_display',
                'last_used'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Generate API key on creation."""
        if not change:  # New object
            import secrets
            obj.api_key = secrets.token_urlsafe(32)
        super().save_model(request, obj, form, change)
    
    def stats_display(self, obj):
        """Display validation statistics."""
        return f"{obj.successful_validations}/{obj.total_validations}"
    stats_display.short_description = 'Success/Total'
    
    def success_rate(self, obj):
        """Display success rate percentage."""
        if obj.total_validations > 0:
            rate = (obj.successful_validations / obj.total_validations) * 100
            color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color,
                rate
            )
        return '-'
    success_rate.short_description = 'Success Rate'
    
    def success_rate_display(self, obj):
        """Display success rate in detail view."""
        if obj.total_validations > 0:
            rate = (obj.successful_validations / obj.total_validations) * 100
            return f"{rate:.2f}%"
        return "No validations yet"
    success_rate_display.short_description = 'Success Rate'
