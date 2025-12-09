"""
Tests for hub_auth_client.django.dynamic_permissions module.

Tests the dynamic permission classes that load requirements from database.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from hub_auth_client.django.dynamic_permissions import (
    DynamicScopePermission,
    DynamicRolePermission,
    DynamicPermission,
)


class TestDynamicScopePermission:
    """Test the DynamicScopePermission class."""
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_no_endpoint_permission_allows_access(self):
        """Test that endpoints without defined permissions allow access."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.path = '/api/test/'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=None):
            result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_endpoint_with_no_required_scopes_allows_access(self):
        """Test that endpoints with no scope requirements allow access."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = []
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_user_with_any_required_scope_allowed(self):
        """Test user with at least one required scope is allowed."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['User.Read', 'Files.ReadWrite']
        mock_endpoint.scope_requirement = 'any'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_scopes', return_value=['User.Read']):
                result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_user_without_required_scopes_denied(self):
        """Test user without required scopes is denied."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['Admin.ReadWrite']
        mock_endpoint.scope_requirement = 'any'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_scopes', return_value=['User.Read']):
                result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_user_with_all_required_scopes_allowed(self):
        """Test user with all required scopes when require_all is True."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['User.Read', 'Files.ReadWrite']
        mock_endpoint.scope_requirement = 'all'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_scopes', return_value=['User.Read', 'Files.ReadWrite', 'Mail.Send']):
                result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_user_missing_some_scopes_when_all_required_denied(self):
        """Test user missing some scopes when all are required is denied."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['User.Read', 'Files.ReadWrite', 'Admin.All']
        mock_endpoint.scope_requirement = 'all'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_scopes', return_value=['User.Read', 'Files.ReadWrite']):
                result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_get_user_scopes_from_user_attribute(self):
        """Test getting scopes from user.scopes attribute."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.scopes = ['User.Read', 'Files.ReadWrite']
        
        result = permission._get_user_scopes(request)
        
        assert result == ['User.Read', 'Files.ReadWrite']
    
    def test_get_user_scopes_from_token_scp(self):
        """Test getting scopes from token 'scp' claim."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock(spec=[])  # No scopes attribute
        request.auth = {'scp': 'User.Read Files.ReadWrite'}
        
        result = permission._get_user_scopes(request)
        
        assert result == ['User.Read', 'Files.ReadWrite']
    
    def test_get_user_scopes_from_token_scopes_array(self):
        """Test getting scopes from token 'scopes' array."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock(spec=[])
        request.auth = {'scopes': ['User.Read', 'Files.ReadWrite']}
        
        result = permission._get_user_scopes(request)
        
        assert result == ['User.Read', 'Files.ReadWrite']
    
    def test_get_user_scopes_returns_empty_when_not_found(self):
        """Test getting scopes returns empty list when not found."""
        permission = DynamicScopePermission()
        
        request = Mock()
        request.user = Mock(spec=[])
        # No auth attribute
        delattr(request, 'auth')
        
        result = permission._get_user_scopes(request)
        
        assert result == []


class TestDynamicRolePermission:
    """Test the DynamicRolePermission class."""
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied."""
        permission = DynamicRolePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_user_with_any_required_role_allowed(self):
        """Test user with at least one required role is allowed."""
        permission = DynamicRolePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_role_names.return_value = ['Admin', 'Manager']
        mock_endpoint.role_requirement = 'any'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_roles', return_value=['Admin']):
                result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_user_with_all_required_roles_allowed(self):
        """Test user with all required roles when require_all is True."""
        permission = DynamicRolePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_role_names.return_value = ['Admin', 'Manager']
        mock_endpoint.role_requirement = 'all'
        
        view = Mock()
        
        with patch.object(permission, '_get_endpoint_permission', return_value=mock_endpoint):
            with patch.object(permission, '_get_user_roles', return_value=['Admin', 'Manager', 'User']):
                result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_get_user_roles_from_user_attribute(self):
        """Test getting roles from user.roles attribute."""
        permission = DynamicRolePermission()
        
        request = Mock()
        request.user = Mock()
        request.user.roles = ['Admin', 'Manager']
        
        result = permission._get_user_roles(request)
        
        assert result == ['Admin', 'Manager']
    
    def test_get_user_roles_from_token(self):
        """Test getting roles from token claims."""
        permission = DynamicRolePermission()
        
        request = Mock()
        request.user = Mock(spec=[])
        request.auth = {'roles': ['Admin', 'Manager']}
        
        result = permission._get_user_roles(request)
        
        assert result == ['Admin', 'Manager']


class TestDynamicPermission:
    """Test the combined DynamicPermission class."""
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied."""
        permission = DynamicPermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        
        result = permission.has_permission(request, view)
        
        assert result is False
    
    def test_user_with_both_scopes_and_roles_allowed(self):
        """Test user with required scopes and roles is allowed."""
        permission = DynamicPermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        request.method = 'GET'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['User.Read']
        mock_endpoint.get_required_role_names.return_value = ['User']
        
        view = Mock()
        
        with patch('hub_auth_client.django.dynamic_permissions.cache') as mock_cache:
            mock_cache.get.return_value = mock_endpoint
            
            with patch('hub_auth_client.django.dynamic_permissions.DynamicScopePermission.has_permission', return_value=True):
                with patch('hub_auth_client.django.dynamic_permissions.DynamicRolePermission.has_permission', return_value=True):
                    result = permission.has_permission(request, view)
        
        assert result is True
    
    def test_user_missing_required_scopes_denied(self):
        """Test user missing required scopes is denied."""
        permission = DynamicPermission()
        
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        request.path = '/api/test/'
        request.method = 'POST'
        
        mock_endpoint = Mock()
        mock_endpoint.get_required_scope_names.return_value = ['Admin.ReadWrite']
        mock_endpoint.get_required_role_names.return_value = []
        
        view = Mock()
        
        with patch('hub_auth_client.django.dynamic_permissions.cache') as mock_cache:
            mock_cache.get.return_value = mock_endpoint
            
            with patch('hub_auth_client.django.dynamic_permissions.DynamicScopePermission.has_permission', return_value=False):
                result = permission.has_permission(request, view)
        
        assert result is False
