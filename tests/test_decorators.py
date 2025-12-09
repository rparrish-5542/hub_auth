"""
Tests for hub_auth_client.django.decorators module.

Tests the view decorators for MSAL token validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.http import JsonResponse
from django.test import RequestFactory
from hub_auth_client.django.decorators import (
    get_validator,
    require_token,
    require_scopes,
    require_roles,
)


@pytest.fixture
def request_factory():
    """Provide Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_settings():
    """Mock Django settings with Azure AD config."""
    return {
        'AZURE_AD_TENANT_ID': 'test-tenant-id',
        'AZURE_AD_CLIENT_ID': 'test-client-id',
        'MSAL_VALIDATE_AUDIENCE': True,
        'MSAL_VALIDATE_ISSUER': True,
        'MSAL_TOKEN_LEEWAY': 0,
    }


class TestGetValidator:
    """Test the get_validator function."""
    
    @patch('hub_auth_client.django.decorators.MSALTokenValidator')
    @patch('hub_auth_client.django.decorators.settings')
    def test_get_validator_with_valid_settings(self, mock_settings_module, mock_validator):
        """Test get_validator returns validator when settings are valid."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_VALIDATE_AUDIENCE = True
        mock_settings_module.MSAL_VALIDATE_ISSUER = True
        mock_settings_module.MSAL_TOKEN_LEEWAY = 0
        
        # Use getattr side effect to return values
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        with patch('hub_auth_client.django.decorators.getattr', side_effect=getattr_side_effect):
            result = get_validator()
        
        mock_validator.assert_called_once_with(
            tenant_id='test-tenant',
            client_id='test-client',
            validate_audience=True,
            validate_issuer=True,
            leeway=0,
        )
    
    @patch('hub_auth_client.django.decorators.settings')
    def test_get_validator_missing_tenant_id(self, mock_settings_module):
        """Test get_validator raises error when tenant_id is missing."""
        mock_settings_module.AZURE_AD_TENANT_ID = None
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        with patch('hub_auth_client.django.decorators.getattr', side_effect=getattr_side_effect):
            with pytest.raises(ValueError, match="AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID must be set"):
                get_validator()
    
    @patch('hub_auth_client.django.decorators.settings')
    def test_get_validator_missing_client_id(self, mock_settings_module):
        """Test get_validator raises error when client_id is missing."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = None
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        with patch('hub_auth_client.django.decorators.getattr', side_effect=getattr_side_effect):
            with pytest.raises(ValueError, match="AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID must be set"):
                get_validator()


class TestRequireToken:
    """Test the require_token decorator."""
    
    def test_require_token_with_valid_token(self, request_factory):
        """Test require_token allows request with valid token."""
        # Create mock view
        @require_token
        def test_view(request):
            return JsonResponse({'user': request.msal_user})
        
        # Create request with auth header
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id', 'name': 'Test User'},
            None
        )
        mock_validator.extract_user_info.return_value = {
            'object_id': 'user-id',
            'name': 'Test User'
        }
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 200
        assert hasattr(request, 'msal_token')
        assert hasattr(request, 'msal_user')
    
    def test_require_token_missing_authorization_header(self, request_factory):
        """Test require_token rejects request without auth header."""
        @require_token
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        
        response = test_view(request)
        
        assert response.status_code == 401
        assert b'Missing Authorization header' in response.content
    
    def test_require_token_with_invalid_token(self, request_factory):
        """Test require_token rejects request with invalid token."""
        @require_token
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid-token'
        
        # Mock validator returning invalid
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            False,
            None,
            'Token signature verification failed'
        )
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 401
        assert b'Invalid token' in response.content


class TestRequireScopes:
    """Test the require_scopes decorator."""
    
    def test_require_scopes_with_valid_scopes(self, request_factory):
        """Test require_scopes allows request with valid scopes."""
        @require_scopes(['User.Read', 'Files.ReadWrite'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id', 'scp': 'User.Read Files.ReadWrite'},
            None
        )
        mock_validator.extract_user_info.return_value = {
            'object_id': 'user-id'
        }
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 200
        mock_validator.validate_token.assert_called_once_with(
            'Bearer valid-token',
            required_scopes=['User.Read', 'Files.ReadWrite'],
            require_all_scopes=False,
        )
    
    def test_require_scopes_missing_authorization_header(self, request_factory):
        """Test require_scopes rejects request without auth header."""
        @require_scopes(['User.Read'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        
        response = test_view(request)
        
        assert response.status_code == 401
        assert b'Missing Authorization header' in response.content
    
    def test_require_scopes_insufficient_scopes(self, request_factory):
        """Test require_scopes rejects request with insufficient scopes."""
        @require_scopes(['Admin.ReadWrite'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator returning scope error
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            False,
            None,
            'Missing required scopes'
        )
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 403
        assert b'Insufficient scopes' in response.content
    
    def test_require_scopes_require_all(self, request_factory):
        """Test require_scopes with require_all=True."""
        @require_scopes(['User.Read', 'Files.ReadWrite'], require_all=True)
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id'},
            None
        )
        mock_validator.extract_user_info.return_value = {'object_id': 'user-id'}
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 200
        mock_validator.validate_token.assert_called_once_with(
            'Bearer valid-token',
            required_scopes=['User.Read', 'Files.ReadWrite'],
            require_all_scopes=True,
        )


class TestRequireRoles:
    """Test the require_roles decorator."""
    
    def test_require_roles_with_valid_roles(self, request_factory):
        """Test require_roles allows request with valid roles."""
        @require_roles(['Admin', 'Manager'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id', 'roles': ['Admin']},
            None
        )
        mock_validator.extract_user_info.return_value = {
            'object_id': 'user-id'
        }
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 200
        mock_validator.validate_token.assert_called_once_with(
            'Bearer valid-token',
            required_roles=['Admin', 'Manager'],
            require_all_roles=False,
        )
    
    def test_require_roles_missing_authorization_header(self, request_factory):
        """Test require_roles rejects request without auth header."""
        @require_roles(['Admin'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        
        response = test_view(request)
        
        assert response.status_code == 401
        assert b'Missing Authorization header' in response.content
    
    def test_require_roles_insufficient_roles(self, request_factory):
        """Test require_roles rejects request with insufficient roles."""
        @require_roles(['SuperAdmin'])
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator returning role error
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            False,
            None,
            'Missing required roles'
        )
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 403
        assert b'Insufficient roles' in response.content
    
    def test_require_roles_require_all(self, request_factory):
        """Test require_roles with require_all=True."""
        @require_roles(['Admin', 'Manager'], require_all=True)
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = request_factory.get('/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id'},
            None
        )
        mock_validator.extract_user_info.return_value = {'object_id': 'user-id'}
        
        with patch('hub_auth_client.django.decorators.get_validator', return_value=mock_validator):
            response = test_view(request)
        
        assert response.status_code == 200
        mock_validator.validate_token.assert_called_once_with(
            'Bearer valid-token',
            required_roles=['Admin', 'Manager'],
            require_all_roles=True,
        )
