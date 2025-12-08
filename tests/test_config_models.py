"""
Tests for Azure AD configuration models.

Tests the database-driven configuration system including:
- AzureADConfiguration model
- AzureADConfigurationHistory model
- Validation logic
- Admin integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


def get_models():
    """Lazy import of models to avoid app registry issues."""
    from hub_auth_client.django.config_models import (
        AzureADConfiguration,
        AzureADConfigurationHistory
    )
    return AzureADConfiguration, AzureADConfigurationHistory


def get_admin():
    """Lazy import of admin."""
    from hub_auth_client.django.admin import AzureADConfigurationAdmin
    return AzureADConfigurationAdmin


def get_user_model():
    """Lazy import of User model."""
    from django.contrib.auth.models import User
    return User


def get_test_utils():
    """Lazy import of test utils."""
    from django.test import TestCase, RequestFactory
    from django.core.exceptions import ValidationError
    return TestCase, RequestFactory, ValidationError


@pytest.mark.django_db
class TestAzureADConfiguration:
    """Test AzureADConfiguration model."""
    
    def setup_method(self):
        """Set up test data."""
        self.valid_tenant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        self.valid_client_id = "f9e8d7c6-b5a4-3210-fedc-ba9876543210"
    
    def test_create_valid_configuration(self):
        """Test creating a valid configuration."""
        AzureADConfiguration, _ = get_models()
        
        config = AzureADConfiguration.objects.create(
            name="Test Config",
            tenant_id=self.valid_tenant_id,
            client_id=self.valid_client_id,
            is_active=True
        )
        
        assert config.name == "Test Config"
        assert config.tenant_id == self.valid_tenant_id
        assert config.client_id == self.valid_client_id
        assert config.is_active is True
        assert config.token_version == "2.0"  # default
        assert config.validate_audience is True  # default
        assert config.validate_issuer is True  # default
    
    def test_invalid_tenant_id_format(self):
        """Test that invalid tenant ID format raises validation error."""
        AzureADConfiguration, _ = get_models()
        _, _, ValidationError = get_test_utils()
        
        with pytest.raises(ValidationError):
            config = AzureADConfiguration(
                name="Invalid Config",
                tenant_id="not-a-valid-guid",
                client_id=self.valid_client_id
            )
            config.full_clean()
    
    def test_invalid_client_id_format(self):
        """Test that invalid client ID format raises validation error."""
        AzureADConfiguration, _ = get_models()
        _, _, ValidationError = get_test_utils()
        
        with pytest.raises(ValidationError):
            config = AzureADConfiguration(
                name="Invalid Config",
                tenant_id=self.valid_tenant_id,
                client_id="not-a-valid-guid"
            )
            config.full_clean()
    
    def test_only_one_active_configuration(self):
        """Test that only one configuration can be active at a time."""
        AzureADConfiguration, _ = get_models()
        _, _, ValidationError = get_test_utils()
        
        # Create first active config
        config1 = AzureADConfiguration.objects.create(
            name="Config 1",
            tenant_id=self.valid_tenant_id,
            client_id=self.valid_client_id,
            is_active=True
        )
        
        # Try to create second active config - should raise error
        with pytest.raises(ValidationError, match="already active"):
            config2 = AzureADConfiguration(
                name="Config 2",
                tenant_id="b2c3d4e5-f6a7-8901-bcde-f12345678901",
                client_id="a9b8c7d6-e5f4-3210-fedc-ba9876543210",
                is_active=True
            )
            config2.save()
    
    def test_get_active_config(self):
        """Test get_active_config class method."""
        AzureADConfiguration, _ = get_models()
        
        # No active config
        assert AzureADConfiguration.get_active_config() is None
        
        # Create active config
        config = AzureADConfiguration.objects.create(
            name="Active Config",
            tenant_id=self.valid_tenant_id,
            client_id=self.valid_client_id,
            is_active=True
        )
        
        # Should return the active config
        active = AzureADConfiguration.get_active_config()
        assert active is not None
        assert active.name == "Active Config"
        assert active.is_active is True
    
    @patch('hub_auth_client.MSALTokenValidator')
    def test_get_validator(self, mock_validator):
        """Test get_validator creates MSALTokenValidator instance."""
        AzureADConfiguration, _ = get_models()
        
        config = AzureADConfiguration.objects.create(
            name="Test Config",
            tenant_id=self.valid_tenant_id,
            client_id=self.valid_client_id,
            is_active=True
        )
        
        validator = config.get_validator()
        
        # Should have called MSALTokenValidator with config
        mock_validator.assert_called_once()
        call_kwargs = mock_validator.call_args[1]
        assert call_kwargs['tenant_id'] == self.valid_tenant_id
        assert call_kwargs['client_id'] == self.valid_client_id


@pytest.mark.django_db
class TestAuthenticationWithDatabaseConfig:
    """Test MSALAuthentication with database configuration."""
    
    def setup_method(self):
        """Set up test data."""
        self.valid_tenant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        self.valid_client_id = "f9e8d7c6-b5a4-3210-fedc-ba9876543210"
    
    @patch('hub_auth_client.django.authentication.MSALTokenValidator')
    @patch('hub_auth_client.MSALTokenValidator')
    def test_uses_database_config_when_available(self, mock_validator_main, mock_validator_auth):
        """Test that authentication uses database config when available."""
        AzureADConfiguration, _ = get_models()
        from hub_auth_client.django.authentication import MSALAuthentication
        
        # Create active config
        config = AzureADConfiguration.objects.create(
            name="Active Config",
            tenant_id=self.valid_tenant_id,
            client_id=self.valid_client_id,
            is_active=True,
            exempt_paths=["/admin/", "/health/"]
        )
        
        # Create authentication instance
        auth = MSALAuthentication()
        
        # Should have used database config
        assert hasattr(auth, 'exempt_paths')
        assert auth.exempt_paths == ["/admin/", "/health/"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
