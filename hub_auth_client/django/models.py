"""
Django models for managing scopes and permissions through admin.

This allows configuring required scopes/roles per endpoint without hardcoding them.
"""

from django.db import models
from django.core.validators import RegexValidator


class ScopeDefinition(models.Model):
    """
    Define available scopes in your application.
    
    These should match the scopes configured in Azure AD.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Scope name (e.g., 'User.Read', 'Employee.Write')"
    )
    description = models.TextField(
        blank=True,
        help_text="What this scope allows"
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category for grouping (e.g., 'User', 'Employee', 'Files')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this scope is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Scope Definition"
        verbose_name_plural = "Scope Definitions"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name}" + (f" ({self.category})" if self.category else "")


class RoleDefinition(models.Model):
    """
    Define available roles in your application.
    
    These should match the app roles configured in Azure AD.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Role name (e.g., 'Admin', 'Manager', 'User')"
    )
    description = models.TextField(
        blank=True,
        help_text="What this role represents"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Role Definition"
        verbose_name_plural = "Role Definitions"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EndpointPermission(models.Model):
    """
    Define permissions required for specific endpoints.
    
    Maps URL patterns to required scopes and roles.
    """
    
    REQUIRE_CHOICES = [
        ('any', 'Any (at least one)'),
        ('all', 'All (must have all)'),
    ]
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Descriptive name for this endpoint"
    )
    url_pattern = models.CharField(
        max_length=500,
        help_text="URL pattern (regex) - e.g., '^/api/employees/$', '/api/employees/.*'"
    )
    http_methods = models.CharField(
        max_length=100,
        default='GET,POST,PUT,PATCH,DELETE',
        help_text="Comma-separated HTTP methods (e.g., 'GET,POST'). Use '*' for all."
    )
    
    # Scope requirements
    required_scopes = models.ManyToManyField(
        ScopeDefinition,
        blank=True,
        related_name='endpoints',
        help_text="Scopes required for this endpoint"
    )
    scope_requirement = models.CharField(
        max_length=10,
        choices=REQUIRE_CHOICES,
        default='any',
        help_text="Whether user needs ANY or ALL of the required scopes"
    )
    
    # Role requirements
    required_roles = models.ManyToManyField(
        RoleDefinition,
        blank=True,
        related_name='endpoints',
        help_text="Roles required for this endpoint"
    )
    role_requirement = models.CharField(
        max_length=10,
        choices=REQUIRE_CHOICES,
        default='any',
        help_text="Whether user needs ANY or ALL of the required roles"
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this permission check is active"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Priority for matching (higher = checked first)"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Description of what this endpoint does"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Endpoint Permission"
        verbose_name_plural = "Endpoint Permissions"
        ordering = ['-priority', 'url_pattern']
        indexes = [
            models.Index(fields=['url_pattern', 'is_active']),
            models.Index(fields=['-priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url_pattern})"
    
    def get_http_methods(self):
        """Get list of HTTP methods."""
        if self.http_methods == '*':
            return ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
        return [m.strip().upper() for m in self.http_methods.split(',')]
    
    def matches_request(self, path, method):
        """Check if this permission rule matches the request."""
        import re
        
        if not self.is_active:
            return False
        
        # Check HTTP method
        if method.upper() not in self.get_http_methods():
            return False
        
        # Check URL pattern
        try:
            pattern = re.compile(self.url_pattern)
            return pattern.match(path) is not None
        except re.error:
            return False
    
    def get_required_scope_names(self):
        """Get list of required scope names."""
        return list(self.required_scopes.filter(is_active=True).values_list('name', flat=True))
    
    def get_required_role_names(self):
        """Get list of required role names."""
        return list(self.required_roles.filter(is_active=True).values_list('name', flat=True))
