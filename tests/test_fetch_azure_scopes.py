"""
Tests for fetch_azure_scopes management command.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError


class TestFetchAzureScopesCommand:
    """Test fetch_azure_scopes management command."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Azure AD configuration."""
        return {
            'tenant_id': 'test-tenant-id',
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret'
        }
    
    @pytest.fixture
    def mock_token_response(self):
        """Mock token response from Azure."""
        mock_response = Mock()
        mock_response.json.return_value = {'access_token': 'test-token'}
        mock_response.raise_for_status = Mock()
        return mock_response
    
    @pytest.fixture
    def mock_app_response_with_api(self):
        """Mock app response with API scopes."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [{
                'id': 'app-id',
                'displayName': 'Test App',
                'appId': 'test-client-id',
                'identifierUris': ['api://test-app'],
                'api': {
                    'oauth2PermissionScopes': [
                        {
                            'value': 'user.read',
                            'isEnabled': True,
                            'adminConsentDescription': 'Read user data',
                            'type': 'User',
                            'id': 'scope-1'
                        },
                        {
                            'value': 'user.write',
                            'isEnabled': True,
                            'adminConsentDescription': 'Write user data',
                            'type': 'Admin',
                            'id': 'scope-2'
                        }
                    ]
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        return mock_response
    
    @pytest.fixture
    def mock_app_response_without_api(self):
        """Mock app response without API key (needs beta endpoint)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [{
                'id': 'app-id',
                'displayName': 'Test App',
                'appId': 'test-client-id',
                'identifierUris': ['api://test-app']
            }]
        }
        mock_response.raise_for_status = Mock()
        return mock_response
    
    @pytest.fixture
    def mock_beta_response(self):
        """Mock beta endpoint response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'app-id',
            'displayName': 'Test App',
            'appId': 'test-client-id',
            'api': {
                'oauth2PermissionScopes': [
                    {
                        'value': 'user.read',
                        'isEnabled': True,
                        'adminConsentDescription': 'Read user data',
                        'type': 'User',
                        'id': 'scope-1'
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        return mock_response
    
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.post')
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.get')
    def test_fetch_scopes_success_with_v1_endpoint(
        self, mock_get, mock_post, mock_config, mock_token_response, 
        mock_app_response_with_api
    ):
        """Test successful scope fetching from v1.0 endpoint."""
        mock_post.return_value = mock_token_response
        mock_get.return_value = mock_app_response_with_api
        
        out = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config', 
                   return_value=mock_config):
            call_command('fetch_azure_scopes', stdout=out)
        
        output = out.getvalue()
        
        # Should show success indicators
        assert '✓' in output or 'Found' in output
        # Should show scope names
        assert 'user.read' in output
        assert 'user.write' in output
    
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.post')
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.get')
    def test_fetch_scopes_fallback_to_beta_endpoint(
        self, mock_get, mock_post, mock_config, mock_token_response,
        mock_app_response_without_api, mock_beta_response
    ):
        """Test fallback to beta endpoint when v1.0 doesn't have API."""
        mock_post.return_value = mock_token_response
        
        # First call returns app without 'api', second call is beta endpoint
        mock_get.side_effect = [mock_app_response_without_api, mock_beta_response]
        
        out = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=mock_config):
            call_command('fetch_azure_scopes', stdout=out)
        
        output = out.getvalue()
        
        # Should show attempt to use beta endpoint
        assert 'beta' in output.lower()
        # Should still find scopes
        assert 'user.read' in output
    
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.post')
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.get')
    def test_fetch_scopes_no_scopes_found(
        self, mock_get, mock_post, mock_config, mock_token_response
    ):
        """Test handling when no scopes are found."""
        mock_post.return_value = mock_token_response
        
        # App with no scopes
        no_scopes_response = Mock()
        no_scopes_response.json.return_value = {
            'value': [{
                'id': 'app-id',
                'displayName': 'Test App',
                'appId': 'test-client-id'
            }]
        }
        no_scopes_response.raise_for_status = Mock()
        
        mock_get.return_value = no_scopes_response
        
        out = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=mock_config):
            call_command('fetch_azure_scopes', stdout=out)
        
        output = out.getvalue()
        
        # Should indicate no scopes found
        assert 'No scopes found' in output or 'No \'api\' key' in output
    
    def test_no_configuration_provided(self):
        """Test error when no Azure configuration is available."""
        out = StringIO()
        err = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=None):
            call_command('fetch_azure_scopes', stdout=out, stderr=err)
        
        error_output = err.getvalue()
        
        # Should show error about missing configuration
        assert 'configuration not found' in error_output.lower()
    
    @patch('hub_auth_client.django.management.commands.fetch_azure_scopes.requests.post')
    def test_authentication_failure(self, mock_post, mock_config):
        """Test handling of authentication failure."""
        # Mock a request exception which is caught and reported
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("Authentication failed")
        
        out = StringIO()
        err = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=mock_config):
            call_command('fetch_azure_scopes', stdout=out, stderr=err)
        
        # Should handle gracefully - either in stdout or stderr
        combined_output = out.getvalue() + err.getvalue()
        assert 'Error' in combined_output or 'error' in combined_output.lower() or 'Authentication failed' in combined_output
    
    def test_json_output_format(self, mock_config):
        """Test JSON output format."""
        out = StringIO()
        
        mock_scopes = [
            {
                'name': 'api://test/user.read',
                'description': 'Read user',
                'category': 'delegated',
                'type': 'oauth2',
                'enabled': True
            }
        ]
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=mock_config):
            with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.fetch_scopes_from_azure',
                       return_value=mock_scopes):
                call_command('fetch_azure_scopes', '--format=json', stdout=out)
        
        output = out.getvalue()
        
        # Should be valid JSON
        import json
        parsed = json.loads(output)
        assert len(parsed) == 1
        assert parsed[0]['name'] == 'api://test/user.read'


class TestAzureScopeImport:
    """Test importing scopes to database."""
    
    @pytest.mark.django_db
    def test_import_scopes_creates_new_scopes(self):
        """Test that --import flag creates ScopeDefinition objects."""
        from hub_auth_client.django.models import ScopeDefinition
        
        mock_config = {
            'tenant_id': 'test-tenant',
            'client_id': 'test-client',
            'client_secret': 'test-secret'
        }
        
        mock_scopes = [
            {
                'name': 'api://test/user.read',
                'description': 'Read user data',
                'category': 'delegated',
                'type': 'oauth2',  # Include type field
                'enabled': True
            }
        ]
        
        out = StringIO()
        
        with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.get_azure_config',
                   return_value=mock_config):
            with patch('hub_auth_client.django.management.commands.fetch_azure_scopes.Command.fetch_scopes_from_azure',
                       return_value=mock_scopes):
                call_command('fetch_azure_scopes', '--import', stdout=out)
        
        output = out.getvalue()
        
        # Should show import summary
        assert 'Created' in output or 'Import' in output
        
        # Check scope was created
        scope = ScopeDefinition.objects.filter(name='api://test/user.read').first()
        assert scope is not None
        assert scope.description == 'Read user data'
