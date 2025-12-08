"""
DRF permission classes for scope and role-based access control.

Usage in views:
    from hub_auth_client.django import HasScopes, HasRoles
    
    class MyView(APIView):
        permission_classes = [HasScopes(['User.Read', 'Files.ReadWrite'])]
        
        def get(self, request):
            # User has at least one of the required scopes
            ...
"""

from typing import List
from rest_framework import permissions


class HasScopes(permissions.BasePermission):
    """
    Permission class that requires user to have at least one of the specified scopes.
    
    Usage:
        permission_classes = [HasScopes(['User.Read', 'Files.ReadWrite'])]
    """
    
    def __init__(self, required_scopes: List[str]):
        """
        Initialize permission with required scopes.
        
        Args:
            required_scopes: List of scopes (user needs at least one)
        """
        self.required_scopes = required_scopes
        super().__init__()
    
    def has_permission(self, request, view):
        """Check if user has required scopes."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Check if user has any of the required scopes
        if hasattr(request.user, 'has_any_scope'):
            return request.user.has_any_scope(self.required_scopes)
        
        # Fallback: check scopes in request.auth (token claims)
        if hasattr(request, 'auth') and request.auth:
            token_scopes = request.auth.get('scp', '').split() or request.auth.get('scopes', [])
            return any(scope in token_scopes for scope in self.required_scopes)
        
        return False
    
    def __call__(self):
        """Allow class to be used as decorator."""
        return self


class HasAllScopes(permissions.BasePermission):
    """
    Permission class that requires user to have ALL of the specified scopes.
    
    Usage:
        permission_classes = [HasAllScopes(['User.Read', 'Files.ReadWrite'])]
    """
    
    def __init__(self, required_scopes: List[str]):
        """
        Initialize permission with required scopes.
        
        Args:
            required_scopes: List of scopes (user needs all of them)
        """
        self.required_scopes = required_scopes
        super().__init__()
    
    def has_permission(self, request, view):
        """Check if user has all required scopes."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Check if user has all required scopes
        if hasattr(request.user, 'has_all_scopes'):
            return request.user.has_all_scopes(self.required_scopes)
        
        # Fallback: check scopes in request.auth (token claims)
        if hasattr(request, 'auth') and request.auth:
            token_scopes = set(request.auth.get('scp', '').split() or request.auth.get('scopes', []))
            return set(self.required_scopes).issubset(token_scopes)
        
        return False
    
    def __call__(self):
        """Allow class to be used as decorator."""
        return self


class HasRoles(permissions.BasePermission):
    """
    Permission class that requires user to have at least one of the specified roles.
    
    Usage:
        permission_classes = [HasRoles(['Admin', 'Manager'])]
    """
    
    def __init__(self, required_roles: List[str]):
        """
        Initialize permission with required roles.
        
        Args:
            required_roles: List of roles (user needs at least one)
        """
        self.required_roles = required_roles
        super().__init__()
    
    def has_permission(self, request, view):
        """Check if user has required roles."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Check if user has any of the required roles
        if hasattr(request.user, 'has_role'):
            return any(request.user.has_role(role) for role in self.required_roles)
        
        # Fallback: check roles in request.auth (token claims)
        if hasattr(request, 'auth') and request.auth:
            token_roles = request.auth.get('roles', [])
            return any(role in token_roles for role in self.required_roles)
        
        return False
    
    def __call__(self):
        """Allow class to be used as decorator."""
        return self


class HasAllRoles(permissions.BasePermission):
    """
    Permission class that requires user to have ALL of the specified roles.
    
    Usage:
        permission_classes = [HasAllRoles(['Admin', 'Manager'])]
    """
    
    def __init__(self, required_roles: List[str]):
        """
        Initialize permission with required roles.
        
        Args:
            required_roles: List of roles (user needs all of them)
        """
        self.required_roles = required_roles
        super().__init__()
    
    def has_permission(self, request, view):
        """Check if user has all required roles."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Check if user has all required roles
        if hasattr(request.user, 'roles'):
            return all(role in request.user.roles for role in self.required_roles)
        
        # Fallback: check roles in request.auth (token claims)
        if hasattr(request, 'auth') and request.auth:
            token_roles = request.auth.get('roles', [])
            return all(role in token_roles for role in self.required_roles)
        
        return False
    
    def __call__(self):
        """Allow class to be used as decorator."""
        return self


# Aliases for backwards compatibility and convenience
HasAnyScope = HasScopes
HasAnyRole = HasRoles
