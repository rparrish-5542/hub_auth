"""
Tests for MSAL-based admin SSO authentication.

Tests the admin authentication backend and SSO login views.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage


def get_admin_backend():
    """Lazy import of admin backend."""
    from hub_auth_client.django.admin_auth import MSALAdminBackend
    return MSALAdminBackend


def get_admin_views():
    """Lazy import of admin views."""
    from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView
    return MSALAdminLoginView, MSALAdminCallbackView


def get_user_model():
    """Lazy import of User model."""
    from django.contrib.auth import get_user_model
    return get_user_model()


@pytest.mark.django_db
class TestMSALAdminBackend:
    """Test MSAL admin authentication backend."""
    
    def setup_method(self):
        """Set up test data."""
        self.backend = get_admin_backend()()
        self.User = get_user_model()
        
        # Sample token claims
        self.valid_claims = {
            'oid': 'test-user-id-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['Staff'],
        }
    
    def test_create_user_from_claims(self):
        """Test creating a new user from token claims."""
        user = self.backend._get_or_create_user(
            user_id=self.valid_claims['oid'],
            email=self.valid_claims['email'],
            name=self.valid_claims['name'],
            roles=self.valid_claims['roles']
        )
        
        assert user is not None
        assert user.username == 'test-user-id-123'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_staff is True
        assert user.is_superuser is False
        assert user.is_active is True
    
    def test_create_superuser_with_admin_role(self):
        """Test that Admin role grants superuser permissions."""
        claims = {
            'oid': 'admin-user-123',
            'email': 'admin@example.com',
            'name': 'Admin User',
            'roles': ['Admin'],
        }
        
        user = self.backend._get_or_create_user(
            user_id=claims['oid'],
            email=claims['email'],
            name=claims['name'],
            roles=claims['roles']
        )
        
        assert user.is_staff is True
        assert user.is_superuser is True
    
    def test_update_existing_user(self):
        """Test updating existing user information."""
        # Create initial user
        user = self.User.objects.create_user(
            username='test-user-id-123',
            email='old@example.com',
            first_name='Old',
            last_name='Name',
            is_staff=False
        )
        
        # Update user with new claims
        updated_user = self.backend._get_or_create_user(
            user_id='test-user-id-123',
            email='new@example.com',
            name='New Name',
            roles=['Staff']
        )
        
        assert updated_user.id == user.id
        assert updated_user.email == 'new@example.com'
        assert updated_user.first_name == 'New'
        assert updated_user.last_name == 'Name'
        assert updated_user.is_staff is True
    
    def test_authenticate_with_valid_claims(self):
        """Test authentication with pre-validated claims."""
        user = self.backend.authenticate(
            request=None,
            claims=self.valid_claims
        )
        
        assert user is not None
        assert user.username == 'test-user-id-123'
        assert user.email == 'test@example.com'
    
    def test_authenticate_missing_required_claims(self):
        """Test authentication fails with missing required claims."""
        invalid_claims = {
            'name': 'Test User',
            # Missing oid and email
        }
        
        user = self.backend.authenticate(
            request=None,
            claims=invalid_claims
        )
        
        assert user is None
    
    @patch('hub_auth_client.django.admin_auth.MSALAdminBackend._validate_token')
    def test_authenticate_with_token(self, mock_validate):
        """Test authentication by validating token."""
        mock_validate.return_value = self.valid_claims
        
        user = self.backend.authenticate(
            request=None,
            token='Bearer test-token'
        )
        
        assert user is not None
        assert user.username == 'test-user-id-123'
        mock_validate.assert_called_once_with('Bearer test-token')
    
    @patch('hub_auth_client.django.admin_auth.MSALAdminBackend._validate_token')
    def test_authenticate_with_invalid_token(self, mock_validate):
        """Test authentication fails with invalid token."""
        mock_validate.return_value = None
        
        user = self.backend.authenticate(
            request=None,
            token='Bearer invalid-token'
        )
        
        assert user is None
    
    def test_get_user(self):
        """Test retrieving user by ID."""
        # Create user
        created_user = self.User.objects.create_user(
            username='test-user',
            email='test@example.com'
        )
        
        # Retrieve user
        user = self.backend.get_user(created_user.id)
        
        assert user is not None
        assert user.id == created_user.id
        assert user.username == 'test-user'
    
    def test_get_user_not_found(self):
        """Test retrieving non-existent user returns None."""
        user = self.backend.get_user(99999)
        
        assert user is None
    
    def test_has_superuser_role(self):
        """Test superuser role detection."""
        assert self.backend._has_superuser_role(['Admin']) is True
        assert self.backend._has_superuser_role(['GlobalAdmin']) is True
        assert self.backend._has_superuser_role(['Staff']) is False
        assert self.backend._has_superuser_role([]) is False
    
    def test_has_staff_role(self):
        """Test staff role detection."""
        assert self.backend._has_staff_role(['Staff']) is True
        assert self.backend._has_staff_role(['Manager']) is True
        assert self.backend._has_staff_role(['Admin']) is True
        assert self.backend._has_staff_role(['User']) is False
        assert self.backend._has_staff_role([]) is False
    
    def test_role_priority_superuser_includes_staff(self):
        """Test that superuser automatically gets staff privileges."""
        user = self.backend._get_or_create_user(
            user_id='superuser-123',
            email='super@example.com',
            name='Super User',
            roles=['Admin']  # Superuser role
        )
        
        assert user.is_superuser is True
        assert user.is_staff is True  # Should also be staff
    
    def test_demote_user_when_roles_removed(self):
        """Test that user permissions are downgraded when roles are removed."""
        # Create admin user
        user = self.User.objects.create_user(
            username='test-admin',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        
        # Update with no admin roles
        updated_user = self.backend._update_user(
            user=user,
            email='admin@example.com',
            name='Test Admin',
            roles=[]  # No roles
        )
        
        assert updated_user.is_staff is False
        assert updated_user.is_superuser is False


@pytest.mark.django_db
class TestMSALAdminLoginView:
    """Test MSAL admin login view."""
    
    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        MSALAdminLoginView, _ = get_admin_views()
        self.view = MSALAdminLoginView.as_view()
        
    def _add_session_to_request(self, request):
        """Add session middleware to request."""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request
    
    @patch('hub_auth_client.django.admin_views.MSALAdminLoginView._get_config')
    def test_login_redirects_to_microsoft(self, mock_config):
        """Test that login view redirects to Microsoft login."""
        mock_config.return_value = ('tenant-123', 'client-456')
        
        request = self.factory.get('/admin/login/msal/')
        request = self._add_session_to_request(request)
        
        response = self.view(request)
        
        assert response.status_code == 302
        assert 'login.microsoftonline.com' in response.url
        assert 'tenant-123' in response.url
        assert 'client-456' in response.url
        assert 'msal_state' in request.session
    
    @patch('hub_auth_client.django.admin_views.MSALAdminLoginView._get_config')
    def test_login_without_config_redirects_to_admin(self, mock_config):
        """Test that login fails gracefully without Azure AD config."""
        mock_config.return_value = None
        
        request = self.factory.get('/admin/login/msal/')
        request = self._add_session_to_request(request)
        
        # Add messages framework
        setattr(request, '_messages', FallbackStorage(request))
        
        response = self.view(request)
        
        assert response.status_code == 302
        assert response.url == '/admin/login/'


@pytest.mark.django_db
class TestMSALAdminCallbackView:
    """Test MSAL admin callback view."""
    
    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        _, MSALAdminCallbackView = get_admin_views()
        self.view = MSALAdminCallbackView.as_view()
        self.User = get_user_model()
    
    def _add_session_to_request(self, request):
        """Add session middleware to request."""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request
    
    def _add_messages_to_request(self, request):
        """Add messages framework to request."""
        setattr(request, '_messages', FallbackStorage(request))
        return request
    
    def test_callback_rejects_invalid_state(self):
        """Test callback rejects request with invalid state."""
        request = self.factory.get('/admin/login/msal/callback/?state=wrong&code=123')
        request = self._add_session_to_request(request)
        request = self._add_messages_to_request(request)
        request.session['msal_state'] = 'correct'
        
        response = self.view(request)
        
        assert response.status_code == 302
        assert response.url == '/admin/login/'
    
    def test_callback_handles_error_from_microsoft(self):
        """Test callback handles error response from Microsoft."""
        request = self.factory.get('/admin/login/msal/callback/?error=access_denied&error_description=User%20cancelled')
        request = self._add_session_to_request(request)
        request = self._add_messages_to_request(request)
        request.session['msal_state'] = 'test-state'
        
        response = self.view(request)
        
        assert response.status_code == 302
        assert response.url == '/admin/login/'
    
    @patch('hub_auth_client.django.admin_views.MSALAdminCallbackView._exchange_code_for_token')
    @patch('hub_auth_client.django.admin_views.MSALAdminCallbackView._validate_id_token')
    def test_successful_login_creates_user_and_redirects(self, mock_validate, mock_exchange):
        """Test successful login flow."""
        # Mock token exchange
        mock_exchange.return_value = {
            'access_token': 'access-token',
            'id_token': 'id-token'
        }
        
        # Mock token validation
        mock_validate.return_value = {
            'oid': 'user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['Admin']
        }
        
        request = self.factory.get('/admin/login/msal/callback/?state=test-state&code=auth-code')
        request = self._add_session_to_request(request)
        request = self._add_messages_to_request(request)
        request.session['msal_state'] = 'test-state'
        request.session['msal_redirect_uri'] = 'http://localhost/callback'
        
        response = self.view(request)
        
        # Should create user and redirect to admin
        assert response.status_code == 302
        assert '/admin/' in response.url
        
        # Verify user was created
        user = self.User.objects.get(username='user-123')
        assert user.email == 'test@example.com'
        assert user.is_staff is True
    
    @patch('hub_auth_client.django.admin_views.MSALAdminCallbackView._exchange_code_for_token')
    @patch('hub_auth_client.django.admin_views.MSALAdminCallbackView._validate_id_token')
    def test_login_denies_non_staff_users(self, mock_validate, mock_exchange):
        """Test that non-staff users are denied admin access."""
        # Mock token exchange
        mock_exchange.return_value = {
            'access_token': 'access-token',
            'id_token': 'id-token'
        }
        
        # Mock token validation with no staff roles
        mock_validate.return_value = {
            'oid': 'user-456',
            'email': 'nonadmin@example.com',
            'name': 'Regular User',
            'roles': []  # No staff/admin roles
        }
        
        request = self.factory.get('/admin/login/msal/callback/?state=test-state&code=auth-code')
        request = self._add_session_to_request(request)
        request = self._add_messages_to_request(request)
        request.session['msal_state'] = 'test-state'
        request.session['msal_redirect_uri'] = 'http://localhost/callback'
        
        response = self.view(request)
        
        # Should deny access and redirect back to login
        assert response.status_code == 302
        assert response.url == '/admin/login/'


@pytest.mark.django_db
class TestAdminSSOIntegration:
    """Integration tests for complete admin SSO flow."""
    
    def setup_method(self):
        """Set up test data."""
        self.User = get_user_model()
        self.backend = get_admin_backend()()
    
    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle from creation to update."""
        # First login - creates user
        user1 = self.backend._get_or_create_user(
            user_id='lifecycle-user',
            email='first@example.com',
            name='First Name',
            roles=['Staff']
        )
        
        assert user1 is not None
        assert user1.email == 'first@example.com'
        assert user1.first_name == 'First'
        assert user1.is_staff is True
        
        # Second login - updates user
        user2 = self.backend._get_or_create_user(
            user_id='lifecycle-user',  # Same user ID
            email='updated@example.com',
            name='Updated Name',
            roles=['Admin']  # Promoted to admin
        )
        
        assert user2.id == user1.id  # Same user
        assert user2.email == 'updated@example.com'
        assert user2.first_name == 'Updated'
        assert user2.is_staff is True
        assert user2.is_superuser is True
    
    def test_multiple_users_with_different_roles(self):
        """Test creating multiple users with different role combinations."""
        # Regular staff
        staff = self.backend._get_or_create_user(
            user_id='staff-user',
            email='staff@example.com',
            name='Staff User',
            roles=['Staff']
        )
        
        # Manager
        manager = self.backend._get_or_create_user(
            user_id='manager-user',
            email='manager@example.com',
            name='Manager User',
            roles=['Manager']
        )
        
        # Admin
        admin = self.backend._get_or_create_user(
            user_id='admin-user',
            email='admin@example.com',
            name='Admin User',
            roles=['Admin']
        )
        
        assert staff.is_staff is True
        assert staff.is_superuser is False
        
        assert manager.is_staff is True
        assert manager.is_superuser is False
        
        assert admin.is_staff is True
        assert admin.is_superuser is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
