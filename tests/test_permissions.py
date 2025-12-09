"""
Tests for hub_auth_client.django.permissions module.

Tests DRF permission classes for scope and role-based access control.
"""

import pytest
from unittest.mock import Mock, MagicMock
from hub_auth_client.django.permissions import (
    HasScopes,
    HasAllScopes,
    HasRoles,
    HasAllRoles,
    HasAnyScope,
    HasAnyRole,
)


class TestHasScopes:
    """Test the HasScopes permission class."""
    
    def test_has_scopes_with_authenticated_user_having_scope(self):
        """Test HasScopes allows user with required scope."""
        permission = HasScopes(['User.Read', 'Files.ReadWrite'])
        
        # Mock request with authenticated user
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_any_scope = Mock(return_value=True)
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
        request.user.has_any_scope.assert_called_once_with(['User.Read', 'Files.ReadWrite'])
    
    def test_has_scopes_with_authenticated_user_missing_scope(self):
        """Test HasScopes denies user without required scope."""
        permission = HasScopes(['Admin.ReadWrite'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_any_scope = Mock(return_value=False)
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_scopes_with_unauthenticated_user(self):
        """Test HasScopes denies unauthenticated user."""
        permission = HasScopes(['User.Read'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_scopes_fallback_to_token_claims(self):
        """Test HasScopes uses token claims when user method not available."""
        permission = HasScopes(['User.Read', 'Files.ReadWrite'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        # No has_any_scope method
        delattr(request.user, 'has_any_scope')
        
        # Token claims in request.auth
        request.auth = {'scp': 'User.Read Files.ReadWrite'}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_scopes_fallback_to_token_scopes_list(self):
        """Test HasScopes uses scopes list from token claims."""
        permission = HasScopes(['User.Read'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'has_any_scope')
        
        # Token claims with scopes as list
        request.auth = {'scopes': ['User.Read', 'Files.ReadWrite']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_scopes_no_user_attribute(self):
        """Test HasScopes denies when request has no user."""
        permission = HasScopes(['User.Read'])
        
        request = Mock(spec=[])  # No user attribute
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False


class TestHasAllScopes:
    """Test the HasAllScopes permission class."""
    
    def test_has_all_scopes_with_user_having_all_scopes(self):
        """Test HasAllScopes allows user with all required scopes."""
        permission = HasAllScopes(['User.Read', 'Files.ReadWrite'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_all_scopes = Mock(return_value=True)
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
        request.user.has_all_scopes.assert_called_once_with(['User.Read', 'Files.ReadWrite'])
    
    def test_has_all_scopes_with_user_missing_some_scopes(self):
        """Test HasAllScopes denies user missing some scopes."""
        permission = HasAllScopes(['User.Read', 'Admin.ReadWrite'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_all_scopes = Mock(return_value=False)
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_all_scopes_fallback_to_token_claims(self):
        """Test HasAllScopes uses token claims when user method not available."""
        permission = HasAllScopes(['User.Read', 'Files.ReadWrite'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'has_all_scopes')
        
        # Token claims with all scopes
        request.auth = {'scp': 'User.Read Files.ReadWrite Mail.Send'}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_all_scopes_fallback_missing_scopes(self):
        """Test HasAllScopes denies when token missing scopes."""
        permission = HasAllScopes(['User.Read', 'Files.ReadWrite', 'Admin.All'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'has_all_scopes')
        
        # Token claims missing Admin.All
        request.auth = {'scopes': ['User.Read', 'Files.ReadWrite']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False


class TestHasRoles:
    """Test the HasRoles permission class."""
    
    def test_has_roles_with_user_having_role(self):
        """Test HasRoles allows user with required role."""
        permission = HasRoles(['Admin', 'Manager'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_role = Mock(side_effect=lambda role: role == 'Admin')
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_roles_with_user_missing_role(self):
        """Test HasRoles denies user without required role."""
        permission = HasRoles(['SuperAdmin'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.has_role = Mock(return_value=False)
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_roles_with_unauthenticated_user(self):
        """Test HasRoles denies unauthenticated user."""
        permission = HasRoles(['Admin'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_roles_fallback_to_token_claims(self):
        """Test HasRoles uses token claims when user method not available."""
        permission = HasRoles(['Admin', 'Manager'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'has_role')
        
        # Token claims with roles
        request.auth = {'roles': ['Admin', 'User']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_roles_fallback_missing_roles(self):
        """Test HasRoles denies when token missing roles."""
        permission = HasRoles(['SuperAdmin'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'has_role')
        
        # Token claims without SuperAdmin role
        request.auth = {'roles': ['User', 'Manager']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False


class TestHasAllRoles:
    """Test the HasAllRoles permission class."""
    
    def test_has_all_roles_with_user_having_all_roles(self):
        """Test HasAllRoles allows user with all required roles."""
        permission = HasAllRoles(['Admin', 'Manager'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.roles = ['Admin', 'Manager', 'User']
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_all_roles_with_user_missing_some_roles(self):
        """Test HasAllRoles denies user missing some roles."""
        permission = HasAllRoles(['Admin', 'SuperAdmin'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.roles = ['Admin', 'Manager']
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_has_all_roles_fallback_to_token_claims(self):
        """Test HasAllRoles uses token claims when user attribute not available."""
        permission = HasAllRoles(['Admin', 'Manager'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'roles')
        
        # Token claims with all roles
        request.auth = {'roles': ['Admin', 'Manager', 'User']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_has_all_roles_fallback_missing_roles(self):
        """Test HasAllRoles denies when token missing roles."""
        permission = HasAllRoles(['Admin', 'Manager', 'SuperAdmin'])
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        delattr(request.user, 'roles')
        
        # Token claims missing SuperAdmin
        request.auth = {'roles': ['Admin', 'Manager']}
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False


class TestAliases:
    """Test the permission class aliases."""
    
    def test_has_any_scope_is_alias_for_has_scopes(self):
        """Test HasAnyScope is an alias for HasScopes."""
        assert HasAnyScope is HasScopes
    
    def test_has_any_role_is_alias_for_has_roles(self):
        """Test HasAnyRole is an alias for HasRoles."""
        assert HasAnyRole is HasRoles


class TestCallablePermissions:
    """Test that permission classes can be used as decorators."""
    
    def test_has_scopes_callable(self):
        """Test HasScopes __call__ returns self."""
        permission = HasScopes(['User.Read'])
        
        result = permission()
        
        assert result is permission
    
    def test_has_all_scopes_callable(self):
        """Test HasAllScopes __call__ returns self."""
        permission = HasAllScopes(['User.Read'])
        
        result = permission()
        
        assert result is permission
    
    def test_has_roles_callable(self):
        """Test HasRoles __call__ returns self."""
        permission = HasRoles(['Admin'])
        
        result = permission()
        
        assert result is permission
    
    def test_has_all_roles_callable(self):
        """Test HasAllRoles __call__ returns self."""
        permission = HasAllRoles(['Admin'])
        
        result = permission()
        
        assert result is permission
