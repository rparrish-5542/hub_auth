"""
Tests for hub_auth_client.django.middleware module.

Tests the MSAL authentication middleware for Django.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.http import JsonResponse
from django.test import RequestFactory
from hub_auth_client.django.middleware import MSALAuthenticationMiddleware


@pytest.fixture
def request_factory():
    """Provide Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_settings():
    """Mock Django settings with Azure AD config."""
    settings = Mock()
    settings.AZURE_AD_TENANT_ID = 'test-tenant-id'
    settings.AZURE_AD_CLIENT_ID = 'test-client-id'
    settings.MSAL_VALIDATE_AUDIENCE = True
    settings.MSAL_VALIDATE_ISSUER = True
    settings.MSAL_TOKEN_LEEWAY = 0
    settings.MSAL_EXEMPT_PATHS = ['/health/', '/metrics/']
    return settings


class TestMSALAuthenticationMiddleware:
    """Test the MSALAuthenticationMiddleware class."""
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_middleware_initialization_with_valid_settings(self, mock_settings_module, mock_validator_class):
        """Test middleware initializes correctly with valid settings."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_VALIDATE_AUDIENCE = True
        mock_settings_module.MSAL_VALIDATE_ISSUER = True
        mock_settings_module.MSAL_TOKEN_LEEWAY = 0
        mock_settings_module.MSAL_EXEMPT_PATHS = ['/health/']
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        assert middleware.get_response == get_response
        assert middleware.exempt_paths == ['/health/']
        mock_validator_class.assert_called_once_with(
            tenant_id='test-tenant',
            client_id='test-client',
            validate_audience=True,
            validate_issuer=True,
            leeway=0,
        )
    
    @patch('hub_auth_client.django.middleware.settings')
    def test_middleware_initialization_missing_tenant_id(self, mock_settings_module):
        """Test middleware raises error when tenant_id is missing."""
        mock_settings_module.AZURE_AD_TENANT_ID = None
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            with pytest.raises(ValueError, match="AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID must be set"):
                MSALAuthenticationMiddleware(get_response)
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_with_valid_token(self, mock_settings_module, mock_validator_class, request_factory):
        """Test process_request validates token and attaches to request."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = []
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
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
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        # Create request with auth header
        request = request_factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        result = middleware.process_request(request)
        
        assert result is None
        assert request.msal_token == {'sub': 'user-id', 'name': 'Test User'}
        assert request.msal_user == {'object_id': 'user-id', 'name': 'Test User'}
        mock_validator.validate_token.assert_called_once_with('Bearer valid-token')
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_with_invalid_token(self, mock_settings_module, mock_validator_class, request_factory):
        """Test process_request returns 401 for invalid token."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = []
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        # Mock validator returning invalid
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            False,
            None,
            'Token signature verification failed'
        )
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        request = request_factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid-token'
        
        result = middleware.process_request(request)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 401
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_without_auth_header(self, mock_settings_module, mock_validator_class, request_factory):
        """Test process_request allows request without auth header."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = []
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        request = request_factory.get('/api/test/')
        
        result = middleware.process_request(request)
        
        assert result is None
        assert request.msal_token is None
        assert request.msal_user is None
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_with_exempt_path(self, mock_settings_module, mock_validator_class, request_factory):
        """Test process_request skips validation for exempt paths."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = ['/health/', '/metrics/']
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        # Request to exempt path
        request = request_factory.get('/health/check')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer should-not-validate'
        
        result = middleware.process_request(request)
        
        assert result is None
        # Validator should not be called
        mock_validator.validate_token.assert_not_called()
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_multiple_exempt_paths(self, mock_settings_module, mock_validator_class, request_factory):
        """Test process_request handles multiple exempt paths correctly."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = ['/health/', '/metrics/', '/admin/']
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        # Test each exempt path
        for path in ['/health/', '/metrics/prometheus', '/admin/login']:
            request = request_factory.get(path)
            request.META['HTTP_AUTHORIZATION'] = 'Bearer token'
            
            result = middleware.process_request(request)
            
            assert result is None
        
        # Validator should never be called
        mock_validator.validate_token.assert_not_called()
    
    @patch('hub_auth_client.django.middleware.MSALTokenValidator')
    @patch('hub_auth_client.django.middleware.settings')
    def test_process_request_non_exempt_path_requires_validation(self, mock_settings_module, mock_validator_class, request_factory):
        """Test non-exempt paths still require validation."""
        mock_settings_module.AZURE_AD_TENANT_ID = 'test-tenant'
        mock_settings_module.AZURE_AD_CLIENT_ID = 'test-client'
        mock_settings_module.MSAL_EXEMPT_PATHS = ['/health/']
        
        def getattr_side_effect(obj, name, default=None):
            return getattr(mock_settings_module, name, default)
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = (
            True,
            {'sub': 'user-id'},
            None
        )
        mock_validator.extract_user_info.return_value = {'object_id': 'user-id'}
        mock_validator_class.return_value = mock_validator
        
        get_response = Mock()
        
        with patch('hub_auth_client.django.middleware.getattr', side_effect=getattr_side_effect):
            middleware = MSALAuthenticationMiddleware(get_response)
        
        # Request to non-exempt path
        request = request_factory.get('/api/users/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid-token'
        
        result = middleware.process_request(request)
        
        assert result is None
        mock_validator.validate_token.assert_called_once_with('Bearer valid-token')
