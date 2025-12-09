"""
Tests for hub_auth_client.django.rls_middleware module.

Tests the RLS middleware for setting PostgreSQL session variables.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from django.test import RequestFactory
from hub_auth_client.django.rls_middleware import RLSMiddleware, RLSDebugMiddleware


@pytest.fixture
def request_factory():
    """Provide Django request factory."""
    return RequestFactory()


class TestRLSMiddleware:
    """Test the RLSMiddleware class."""
    
    def test_unauthenticated_user_skipped(self, request_factory):
        """Test that unauthenticated users are skipped."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        result = middleware.process_request(request)
        
        assert result is None
    
    def test_non_postgresql_database_skipped(self, request_factory):
        """Test that non-PostgreSQL databases are skipped."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        
        with patch('hub_auth_client.django.rls_middleware.connection') as mock_conn:
            mock_conn.settings_dict = {'ENGINE': 'django.db.backends.sqlite3'}
            
            result = middleware.process_request(request)
        
        assert result is None
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_sets_user_id_from_oid(self, mock_conn, request_factory):
        """Test setting user_id from oid attribute."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.oid = 'user-oid-123'
        request.user.email = 'test@example.com'
        request.user.name = 'Test User'
        request.user.scopes = ['User.Read']
        request.user.roles = ['User']
        request.user.tid = 'tenant-123'
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(middleware, '_set_session_variables') as mock_set_vars:
            result = middleware.process_request(request)
        
        assert result is None
        mock_set_vars.assert_called_once()
        
        # Check that session vars were prepared correctly
        call_args = mock_set_vars.call_args[0][0]
        assert call_args['app.user_id'] == 'user-oid-123'
        assert call_args['app.user_email'] == 'test@example.com'
        assert call_args['app.user_scopes'] == 'User.Read'
        assert call_args['app.user_roles'] == 'User'
        assert call_args['app.tenant_id'] == 'tenant-123'
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_sets_user_id_from_email_when_no_oid(self, mock_conn, request_factory):
        """Test setting user_id from email when oid not available."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.email = 'test@example.com'
        request.user.scopes = []
        request.user.roles = []
        
        # Remove oid attribute
        delattr(request.user, 'oid')
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(middleware, '_set_session_variables') as mock_set_vars:
            result = middleware.process_request(request)
        
        call_args = mock_set_vars.call_args[0][0]
        assert call_args['app.user_id'] == 'test@example.com'
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_handles_empty_scopes_and_roles(self, mock_conn, request_factory):
        """Test handling empty scopes and roles."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.oid = 'user-123'
        request.user.scopes = []
        request.user.roles = None
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(middleware, '_set_session_variables') as mock_set_vars:
            middleware.process_request(request)
        
        call_args = mock_set_vars.call_args[0][0]
        assert call_args['app.user_scopes'] == ''
        assert call_args['app.user_roles'] == ''
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_handles_multiple_scopes_and_roles(self, mock_conn, request_factory):
        """Test handling multiple scopes and roles."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.oid = 'user-123'
        request.user.scopes = ['User.Read', 'Files.ReadWrite', 'Mail.Send']
        request.user.roles = ['Admin', 'Manager', 'User']
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(middleware, '_set_session_variables') as mock_set_vars:
            middleware.process_request(request)
        
        call_args = mock_set_vars.call_args[0][0]
        assert call_args['app.user_scopes'] == 'User.Read,Files.ReadWrite,Mail.Send'
        assert call_args['app.user_roles'] == 'Admin,Manager,User'
    
    def test_get_nested_attr_single_level(self):
        """Test getting single-level nested attribute."""
        middleware = RLSMiddleware(lambda r: None)
        
        obj = Mock()
        obj.name = 'Test Name'
        
        result = middleware._get_nested_attr(obj, 'name')
        
        assert result == 'Test Name'
    
    def test_get_nested_attr_multiple_levels(self):
        """Test getting multi-level nested attribute."""
        middleware = RLSMiddleware(lambda r: None)
        
        obj = Mock()
        obj.department = Mock()
        obj.department.id = 123
        
        result = middleware._get_nested_attr(obj, 'department.id')
        
        assert result == 123
    
    def test_get_nested_attr_missing_attribute(self):
        """Test getting nested attribute that doesn't exist."""
        middleware = RLSMiddleware(lambda r: None)
        
        obj = Mock(spec=['name'])
        
        result = middleware._get_nested_attr(obj, 'department.id')
        
        assert result is None
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_set_session_variables_executes_sql(self, mock_conn):
        """Test that session variables are set with SQL."""
        middleware = RLSMiddleware(lambda r: None)
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        variables = {
            'app.user_id': 'user-123',
            'app.user_email': 'test@example.com',
        }
        
        middleware._set_session_variables(variables)
        
        # Should execute SQL for each variable
        assert mock_cursor.execute.call_count == 2
        
        # Check SQL format
        calls = mock_cursor.execute.call_args_list
        assert "SET LOCAL app.user_id = 'user-123'" in calls[0][0][0]
        assert "SET LOCAL app.user_email = 'test@example.com'" in calls[1][0][0]
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_set_session_variables_escapes_quotes(self, mock_conn):
        """Test that single quotes in values are escaped."""
        middleware = RLSMiddleware(lambda r: None)
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        variables = {
            'app.user_name': "O'Brien",
        }
        
        middleware._set_session_variables(variables)
        
        # Should escape single quote
        call_args = mock_cursor.execute.call_args[0][0]
        assert "O''Brien" in call_args
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_set_session_variables_handles_errors_gracefully(self, mock_conn):
        """Test that errors in setting variables don't crash."""
        middleware = RLSMiddleware(lambda r: None)
        
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        variables = {'app.user_id': 'user-123'}
        
        # Should not raise exception
        middleware._set_session_variables(variables)
    
    def test_process_response_returns_response(self, request_factory):
        """Test that process_response returns the response unchanged."""
        middleware = RLSMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        response = Mock()
        
        result = middleware.process_response(request, response)
        
        assert result is response


class TestRLSDebugMiddleware:
    """Test the RLSDebugMiddleware class."""
    
    def test_unauthenticated_user_skipped(self, request_factory):
        """Test that unauthenticated users are skipped."""
        middleware = RLSDebugMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        result = middleware.process_request(request)
        
        assert result is None
    
    def test_non_postgresql_database_skipped(self, request_factory):
        """Test that non-PostgreSQL databases are skipped."""
        middleware = RLSDebugMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        
        with patch('hub_auth_client.django.rls_middleware.connection') as mock_conn:
            mock_conn.settings_dict = {'ENGINE': 'django.db.backends.sqlite3'}
            
            result = middleware.process_request(request)
        
        assert result is None
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_queries_session_variables_for_debugging(self, mock_conn, request_factory):
        """Test that debug middleware queries session variables."""
        middleware = RLSDebugMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.path = '/api/test/'
        request.user = Mock()
        request.user.is_authenticated = True
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ['user-123']
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = middleware.process_request(request)
        
        # Should query for session variables
        assert mock_cursor.execute.call_count > 0
        assert result is None
    
    @patch('hub_auth_client.django.rls_middleware.connection')
    def test_handles_errors_gracefully(self, mock_conn, request_factory):
        """Test that errors during debugging don't crash."""
        middleware = RLSDebugMiddleware(lambda r: None)
        
        request = request_factory.get('/api/test/')
        request.path = '/api/test/'
        request.user = Mock()
        request.user.is_authenticated = True
        
        mock_conn.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Should not raise exception
        result = middleware.process_request(request)
        
        assert result is None
