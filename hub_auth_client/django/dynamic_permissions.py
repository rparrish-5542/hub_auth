"""
Dynamic permission classes that load requirements from database.

These permission classes check the database for endpoint-specific requirements
instead of hardcoding scopes/roles.
"""

from typing import Optional
from rest_framework import permissions
from django.core.cache import cache
import re
import logging

logger = logging.getLogger(__name__)


class DynamicScopePermission(permissions.BasePermission):
    """
    Permission class that checks scopes based on database configuration.
    
    Looks up the endpoint in the database and checks if user has required scopes.
    
    Usage:
        class MyView(APIView):
            permission_classes = [DynamicScopePermission]
    """
    
    def has_permission(self, request, view):
        """Check if user has required scopes for this endpoint."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Get endpoint permission from database
        endpoint_perm = self._get_endpoint_permission(request)
        
        if not endpoint_perm:
            # No permission defined = allow by default (or deny based on your security policy)
            logger.debug(f"No endpoint permission found for {request.path}")
            return True
        
        # Check if any scopes are configured (even if inactive)
        total_configured_scopes = endpoint_perm.required_scopes.count()
        
        # Get required scopes (active only)
        required_scopes = endpoint_perm.get_required_scope_names()
        
        if total_configured_scopes > 0 and not required_scopes:
            # Scopes are configured but none are active - DENY access
            logger.warning(
                f"Scope check failed for {request.user.username} on {request.path}. "
                f"Scopes are configured ({total_configured_scopes}) but none are active/valid."
            )
            return False
        
        if not required_scopes:
            # No scopes required
            return True
        
        # Get user scopes
        user_scopes = self._get_user_scopes(request)
        
        # Check scope requirement
        if endpoint_perm.scope_requirement == 'all':
            # User must have ALL scopes
            has_permission = all(scope in user_scopes for scope in required_scopes)
        else:
            # User must have ANY scope
            has_permission = any(scope in user_scopes for scope in required_scopes)
        
        if not has_permission:
            logger.warning(
                f"Scope check failed for {request.user.username} on {request.path}. "
                f"Required: {required_scopes} ({endpoint_perm.scope_requirement}), "
                f"User has: {user_scopes}"
            )
        
        return has_permission
    
    def _get_endpoint_permission(self, request):
        """Get endpoint permission from database with caching."""
        cache_key = f"endpoint_perm:{request.path}:{request.method}"
        
        # Try cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Query database
        try:
            from .models import EndpointPermission
            
            # Get all active permissions ordered by priority
            permissions = EndpointPermission.objects.filter(
                is_active=True
            ).order_by('-priority').prefetch_related('required_scopes', 'required_roles')
            
            # Find first matching permission
            for perm in permissions:
                if perm.matches_request(request.path, request.method):
                    # Cache for 5 minutes
                    cache.set(cache_key, perm, 300)
                    return perm
            
            # No match found - cache None for 1 minute
            cache.set(cache_key, None, 60)
            return None
            
        except Exception as e:
            logger.error(f"Error loading endpoint permission: {e}", exc_info=True)
            return None
    
    def _get_user_scopes(self, request):
        """Get user's scopes from token."""
        if hasattr(request.user, 'scopes'):
            return request.user.scopes
        
        if hasattr(request, 'auth') and request.auth:
            return request.auth.get('scp', '').split() or request.auth.get('scopes', [])
        
        return []


class DynamicRolePermission(permissions.BasePermission):
    """
    Permission class that checks roles based on database configuration.
    
    Looks up the endpoint in the database and checks if user has required roles.
    
    Usage:
        class MyView(APIView):
            permission_classes = [DynamicRolePermission]
    """
    
    def has_permission(self, request, view):
        """Check if user has required roles for this endpoint."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Get endpoint permission from database
        endpoint_perm = self._get_endpoint_permission(request)
        
        if not endpoint_perm:
            logger.debug(f"No endpoint permission found for {request.path}")
            return True
        
        # Check if any roles are configured (even if inactive)
        total_configured_roles = endpoint_perm.required_roles.count()
        
        # Get required roles (active only)
        required_roles = endpoint_perm.get_required_role_names()
        
        if total_configured_roles > 0 and not required_roles:
            # Roles are configured but none are active - DENY access
            logger.warning(
                f"Role check failed for {request.user.username} on {request.path}. "
                f"Roles are configured ({total_configured_roles}) but none are active/valid."
            )
            return False
        
        if not required_roles:
            # No roles required
            return True
        
        # Get user roles
        user_roles = self._get_user_roles(request)
        
        # Check role requirement
        if endpoint_perm.role_requirement == 'all':
            # User must have ALL roles
            has_permission = all(role in user_roles for role in required_roles)
        else:
            # User must have ANY role
            has_permission = any(role in user_roles for role in required_roles)
        
        if not has_permission:
            logger.warning(
                f"Role check failed for {request.user.username} on {request.path}. "
                f"Required: {required_roles} ({endpoint_perm.role_requirement}), "
                f"User has: {user_roles}"
            )
        
        return has_permission
    
    def _get_endpoint_permission(self, request):
        """Get endpoint permission from database with caching."""
        cache_key = f"endpoint_perm:{request.path}:{request.method}"
        
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from .models import EndpointPermission
            
            permissions = EndpointPermission.objects.filter(
                is_active=True
            ).order_by('-priority').prefetch_related('required_scopes', 'required_roles')
            
            for perm in permissions:
                if perm.matches_request(request.path, request.method):
                    cache.set(cache_key, perm, 300)
                    return perm
            
            cache.set(cache_key, None, 60)
            return None
            
        except Exception as e:
            logger.error(f"Error loading endpoint permission: {e}", exc_info=True)
            return None
    
    def _get_user_roles(self, request):
        """Get user's roles from token."""
        if hasattr(request.user, 'roles'):
            return request.user.roles
        
        if hasattr(request, 'auth') and request.auth:
            return request.auth.get('roles', [])
        
        return []


class DynamicPermission(permissions.BasePermission):
    """
    Combined permission class that checks both scopes and roles from database.
    
    This is the recommended permission class to use - it checks both scopes
    and roles based on database configuration.
    
    Usage:
        class MyView(APIView):
            permission_classes = [DynamicPermission]
    """
    
    def __init__(self):
        self.scope_permission = DynamicScopePermission()
        self.role_permission = DynamicRolePermission()
    
    def has_permission(self, request, view):
        """Check if user has required scopes AND roles for this endpoint."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Get endpoint permission from database
        cache_key = f"endpoint_perm:{request.path}:{request.method}"
        endpoint_perm = cache.get(cache_key)
        
        if endpoint_perm is None:
            try:
                from .models import EndpointPermission
                
                permissions = EndpointPermission.objects.filter(
                    is_active=True
                ).order_by('-priority').prefetch_related('required_scopes', 'required_roles')
                
                for perm in permissions:
                    if perm.matches_request(request.path, request.method):
                        endpoint_perm = perm
                        cache.set(cache_key, perm, 300)
                        break
                
                if endpoint_perm is None:
                    cache.set(cache_key, None, 60)
                    return True  # No permission defined
                    
            except Exception as e:
                logger.error(f"Error loading endpoint permission: {e}", exc_info=True)
                return False
        
        # Check scopes if required
        required_scopes = endpoint_perm.get_required_scope_names()
        if required_scopes:
            has_scopes = self.scope_permission.has_permission(request, view)
            if not has_scopes:
                return False
        
        # Check roles if required
        required_roles = endpoint_perm.get_required_role_names()
        if required_roles:
            has_roles = self.role_permission.has_permission(request, view)
            if not has_roles:
                return False
        
        return True
