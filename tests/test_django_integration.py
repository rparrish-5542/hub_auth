"""Tests for Django integration."""

import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from hub_auth_client.django.authentication import MSALUser, MSALAuthentication


class TestMSALUser:
    """Tests for MSALUser class."""
    
    @pytest.fixture
    def mock_claims(self):
        return {
            'oid': 'test-object-id',
            'tid': 'test-tenant-id',
            'upn': 'test@example.com',
            'email': 'test@example.com',
            'name': 'Test User',
            'scp': 'User.Read Files.ReadWrite',
            'roles': ['Admin', 'User'],
            'groups': ['group1', 'group2'],
        }
    
    def test_msal_user_creation(self, mock_claims):
        """Test creating MSALUser from claims."""
        user = MSALUser(mock_claims)
        
        assert user.object_id == 'test-object-id'
        assert user.username == 'test@example.com'
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False
    
    def test_msal_user_has_scope(self, mock_claims):
        """Test MSALUser.has_scope method."""
        user = MSALUser(mock_claims)
        
        assert user.has_scope('User.Read') is True
        assert user.has_scope('Files.ReadWrite') is True
        assert user.has_scope('NonExistent') is False
    
    def test_msal_user_has_role(self, mock_claims):
        """Test MSALUser.has_role method."""
        user = MSALUser(mock_claims)
        
        assert user.has_role('Admin') is True
        assert user.has_role('User') is True
        assert user.has_role('NonExistent') is False
    
    def test_msal_user_has_any_scope(self, mock_claims):
        """Test MSALUser.has_any_scope method."""
        user = MSALUser(mock_claims)
        
        assert user.has_any_scope(['User.Read', 'Files.Write']) is True
        assert user.has_any_scope(['NonExistent1', 'NonExistent2']) is False
    
    def test_msal_user_has_all_scopes(self, mock_claims):
        """Test MSALUser.has_all_scopes method."""
        user = MSALUser(mock_claims)
        
        assert user.has_all_scopes(['User.Read', 'Files.ReadWrite']) is True
        assert user.has_all_scopes(['User.Read', 'NonExistent']) is False


class TestMSALAuthentication:
    """Tests for MSALAuthentication backend."""
    
    @pytest.fixture
    def factory(self):
        return APIRequestFactory()
    
    @pytest.fixture
    def mock_validator(self):
        with patch('hub_auth_client.django.authentication.MSALTokenValidator') as mock:
            yield mock
    
    def test_authenticate_no_header(self, factory):
        """Test authentication with no Authorization header."""
        request = factory.get('/api/test/')
        auth = MSALAuthentication()
        
        result = auth.authenticate(request)
        assert result is None
    
    def test_authenticate_header(self):
        """Test authentication header in 401 response."""
        auth = MSALAuthentication()
        header = auth.authenticate_header(None)
        
        assert header == 'Bearer realm="api"'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
