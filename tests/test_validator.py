"""
Tests for MSALTokenValidator.

Run with: pytest tests/
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from hub_auth_client import MSALTokenValidator
from hub_auth_client.exceptions import (
    TokenValidationError,
    TokenExpiredError,
    InvalidTokenError,
)


class TestMSALTokenValidator:
    """Tests for MSALTokenValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return MSALTokenValidator(
            tenant_id="test-tenant-id",
            client_id="test-client-id"
        )
    
    @pytest.fixture
    def mock_token_claims(self):
        """Mock token claims for testing."""
        now = datetime.now(timezone.utc)
        return {
            'oid': 'test-object-id',
            'tid': 'test-tenant-id',
            'aud': 'test-client-id',
            'iss': 'https://login.microsoftonline.com/test-tenant-id/v2.0',
            'exp': int((now + timedelta(hours=1)).timestamp()),
            'nbf': int(now.timestamp()),
            'iat': int(now.timestamp()),
            'upn': 'test@example.com',
            'name': 'Test User',
            'scp': 'User.Read Files.ReadWrite',
            'roles': ['Admin', 'User'],
        }
    
    def test_extract_user_info(self, validator, mock_token_claims):
        """Test extracting user info from token claims."""
        user_info = validator.extract_user_info(mock_token_claims)
        
        assert user_info['object_id'] == 'test-object-id'
        assert user_info['tenant_id'] == 'test-tenant-id'
        assert user_info['user_principal_name'] == 'test@example.com'
        assert user_info['name'] == 'Test User'
        assert 'User.Read' in user_info['scopes']
        assert 'Files.ReadWrite' in user_info['scopes']
        assert 'Admin' in user_info['roles']
    
    def test_has_scope(self, validator, mock_token_claims):
        """Test checking if token has specific scope."""
        assert validator.has_scope(mock_token_claims, 'User.Read') is True
        assert validator.has_scope(mock_token_claims, 'Files.ReadWrite') is True
        assert validator.has_scope(mock_token_claims, 'NonExistent.Scope') is False
    
    def test_has_role(self, validator, mock_token_claims):
        """Test checking if token has specific role."""
        assert validator.has_role(mock_token_claims, 'Admin') is True
        assert validator.has_role(mock_token_claims, 'User') is True
        assert validator.has_role(mock_token_claims, 'NonExistentRole') is False
    
    def test_has_any_scope(self, validator, mock_token_claims):
        """Test checking if token has any of specified scopes."""
        assert validator.has_any_scope(
            mock_token_claims,
            ['User.Read', 'Files.Write']
        ) is True
        
        assert validator.has_any_scope(
            mock_token_claims,
            ['NonExistent.Scope1', 'NonExistent.Scope2']
        ) is False
    
    def test_has_all_scopes(self, validator, mock_token_claims):
        """Test checking if token has all specified scopes."""
        assert validator.has_all_scopes(
            mock_token_claims,
            ['User.Read', 'Files.ReadWrite']
        ) is True
        
        assert validator.has_all_scopes(
            mock_token_claims,
            ['User.Read', 'NonExistent.Scope']
        ) is False
    
    def test_get_token_expiry(self, validator, mock_token_claims):
        """Test getting token expiration time."""
        expiry = validator.get_token_expiry(mock_token_claims)
        
        assert expiry is not None
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)
    
    def test_validate_claims_missing_required_claim(self, validator):
        """Test validation fails when required claim is missing."""
        claims = {
            'tid': 'test-tenant-id',
            # Missing 'oid'
        }
        
        error = validator._validate_claims(claims, None, None, False, False)
        assert error is not None
        assert 'Missing required claim' in error
    
    def test_validate_claims_wrong_tenant(self, validator):
        """Test validation fails when tenant doesn't match."""
        claims = {
            'oid': 'test-oid',
            'tid': 'wrong-tenant-id',
        }
        
        error = validator._validate_claims(claims, None, None, False, False)
        assert error is not None
        assert 'wrong tenant' in error.lower()
    
    def test_validate_scopes_any(self, validator, mock_token_claims):
        """Test scope validation with require_all=False."""
        # User has User.Read, requires User.Read OR Files.Write
        error = validator._validate_scopes(
            mock_token_claims,
            ['User.Read', 'Files.Write'],
            require_all=False
        )
        assert error is None
        
        # User doesn't have any required scopes
        error = validator._validate_scopes(
            mock_token_claims,
            ['NonExistent.Scope1', 'NonExistent.Scope2'],
            require_all=False
        )
        assert error is not None
    
    def test_validate_scopes_all(self, validator, mock_token_claims):
        """Test scope validation with require_all=True."""
        # User has both scopes
        error = validator._validate_scopes(
            mock_token_claims,
            ['User.Read', 'Files.ReadWrite'],
            require_all=True
        )
        assert error is None
        
        # User is missing one scope
        error = validator._validate_scopes(
            mock_token_claims,
            ['User.Read', 'NonExistent.Scope'],
            require_all=True
        )
        assert error is not None
        assert 'Missing required scopes' in error
    
    def test_validate_roles_any(self, validator, mock_token_claims):
        """Test role validation with require_all=False."""
        # User has Admin role
        error = validator._validate_roles(
            mock_token_claims,
            ['Admin', 'Manager'],
            require_all=False
        )
        assert error is None
        
        # User doesn't have any required roles
        error = validator._validate_roles(
            mock_token_claims,
            ['NonExistentRole1', 'NonExistentRole2'],
            require_all=False
        )
        assert error is not None
    
    def test_validate_roles_all(self, validator, mock_token_claims):
        """Test role validation with require_all=True."""
        # User has both roles
        error = validator._validate_roles(
            mock_token_claims,
            ['Admin', 'User'],
            require_all=True
        )
        assert error is None
        
        # User is missing one role
        error = validator._validate_roles(
            mock_token_claims,
            ['Admin', 'NonExistentRole'],
            require_all=True
        )
        assert error is not None
        assert 'Missing required roles' in error


class TestScopeFormats:
    """Test different scope claim formats."""
    
    @pytest.fixture
    def validator(self):
        return MSALTokenValidator(
            tenant_id="test-tenant-id",
            client_id="test-client-id"
        )
    
    def test_scopes_as_string(self, validator):
        """Test scopes in 'scp' claim as space-separated string."""
        claims = {
            'scp': 'User.Read Files.ReadWrite',
        }
        
        assert validator.has_scope(claims, 'User.Read') is True
        assert validator.has_scope(claims, 'Files.ReadWrite') is True
    
    def test_scopes_as_list(self, validator):
        """Test scopes in 'scopes' claim as list."""
        claims = {
            'scopes': ['User.Read', 'Files.ReadWrite'],
        }
        
        assert validator.has_scope(claims, 'User.Read') is True
        assert validator.has_scope(claims, 'Files.ReadWrite') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
