"""
Tests for admin helper functions.
"""
import pytest
from hub_auth_client.django.admin_helpers import (
    humanize_url_pattern,
    format_active_badge,
    format_masked_guid,
)


class TestHumanizeURLPattern:
    """Test URL pattern humanization."""
    
    def test_simple_pattern(self):
        """Test simple URL pattern without regex."""
        pattern = '^api/employees/$'
        result = humanize_url_pattern(pattern)
        assert result == '/api/employees/'
    
    def test_pattern_with_named_group(self):
        """Test URL pattern with named capture group."""
        pattern = '^api/employees/(?P<pk>[^/.]+)/$'
        result = humanize_url_pattern(pattern)
        assert result == '/api/employees/{pk}/'
    
    def test_pattern_with_multiple_named_groups(self):
        """Test URL pattern with multiple named groups."""
        pattern = '^api/(?P<app>[^/]+)/(?P<model>[^/]+)/(?P<pk>[^/.]+)/$'
        result = humanize_url_pattern(pattern)
        assert result == '/api/{app}/{model}/{pk}/'
    
    def test_pattern_with_optional_trailing_slash(self):
        """Test URL pattern with optional trailing slash."""
        pattern = '^api/employees/?$'
        result = humanize_url_pattern(pattern)
        assert 'optional trailing slash' in result
        assert '/api/employees' in result
    
    def test_pattern_with_format_extension(self):
        """Test URL pattern with format extension."""
        pattern = r'^api/employees\.(?P<format>[a-z0-9]+)/?$'
        result = humanize_url_pattern(pattern)
        assert '{format}' in result
        assert '/api/employees.{format}' in result
    
    def test_pattern_with_wildcard(self):
        """Test URL pattern with wildcard."""
        pattern = 'admin/(?P<url>.*)$'
        result = humanize_url_pattern(pattern)
        assert '{url}' in result
        # The wildcard creates a placeholder, not necessarily "any path" text
        assert '/admin/{url}' in result
    
    def test_pattern_with_number_constraint(self):
        """Test URL pattern with number constraint."""
        pattern = r'^api/employees/(?P<id>\d+)/$'
        result = humanize_url_pattern(pattern)
        assert '{id:number}' in result
    
    def test_empty_pattern(self):
        """Test empty pattern returns empty string."""
        assert humanize_url_pattern('') == ''
        assert humanize_url_pattern(None) == ''
    
    def test_pattern_without_anchors(self):
        """Test pattern without anchors gets leading slash."""
        pattern = 'api/employees/'
        result = humanize_url_pattern(pattern)
        assert result == '/api/employees/'
    
    def test_pattern_with_escaped_characters(self):
        """Test pattern with escaped characters."""
        pattern = r'^api/employees\-list/$'
        result = humanize_url_pattern(pattern)
        assert result == '/api/employees-list/'
    
    def test_complex_pattern(self):
        """Test complex pattern with multiple features."""
        pattern = r'^api/(?P<version>v\d+)/employees/(?P<pk>\d+)\.(?P<format>[a-z]+)/?$'
        result = humanize_url_pattern(pattern)
        assert '/api/{version}/employees/{pk:number}.{format}' in result
        assert 'optional trailing slash' in result


class TestFormatActiveBadge:
    """Test active badge formatting."""
    
    def test_active_badge_true(self):
        """Test active badge for active status."""
        result = format_active_badge(True)
        assert 'green' in result
        assert '✓' in result or 'Active' in result
    
    def test_active_badge_false(self):
        """Test active badge for inactive status."""
        result = format_active_badge(False)
        assert 'red' in result or 'gray' in result
        assert '✗' in result or 'Inactive' in result


class TestFormatMaskedGuid:
    """Test GUID masking."""
    
    def test_mask_guid(self):
        """Test GUID masking shows only last 4 chars."""
        guid = '12345678-1234-1234-1234-123456789abc'
        result = format_masked_guid(guid)
        assert '9abc' in result
        # Should have masking characters (dots or asterisks)
        assert '••••' in result or '****' in result or '...' in result or 'masked' in result.lower()
    
    def test_mask_short_string(self):
        """Test masking of short strings."""
        short = 'abc'
        result = format_masked_guid(short)
        # Should handle short strings gracefully
        assert isinstance(result, str)
    
    def test_mask_empty_string(self):
        """Test masking empty string."""
        result = format_masked_guid('')
        assert result == '' or result == '-'
    
    def test_mask_none(self):
        """Test masking None value."""
        result = format_masked_guid(None)
        assert result == '' or result == '-'


class TestFormatSensitiveFieldWithReveal:
    """Test the format_sensitive_field_with_reveal function."""
    
    def test_format_guid_with_reveal(self):
        """Test formatting a GUID with reveal button."""
        from hub_auth_client.django.admin_helpers import format_sensitive_field_with_reveal
        
        guid = 'abc123de-f456-7890-ghij-klmnopqrstuv'
        result = format_sensitive_field_with_reveal(guid, 'tenant_id', 1)
        
        result_str = str(result)
        assert 'klmnopqrstuv' in result_str
        assert '••••' in result_str
        assert 'reveal-btn' in result_str
        assert 'tenant_id_1' in result_str
    
    def test_format_secret_with_reveal(self):
        """Test formatting a non-GUID secret."""
        from hub_auth_client.django.admin_helpers import format_sensitive_field_with_reveal
        
        secret = 'mysecretvalue123'
        result = format_sensitive_field_with_reveal(secret, 'client_secret', 2)
        
        result_str = str(result)
        assert '•' in result_str
        assert 'reveal-btn' in result_str
        assert 'client_secret_2' in result_str
    
    def test_format_empty_value_before_save(self):
        """Test formatting when value not set before save."""
        from hub_auth_client.django.admin_helpers import format_sensitive_field_with_reveal
        
        result = format_sensitive_field_with_reveal(None, 'tenant_id', None)
        
        result_str = str(result)
        assert 'Will be set after saving' in result_str


class TestFormatCountWithRequirement:
    """Test the format_count_with_requirement function."""
    
    def test_count_with_any_requirement(self):
        """Test count with ANY requirement."""
        from hub_auth_client.django.admin_helpers import format_count_with_requirement
        
        result = format_count_with_requirement(3, 'any')
        
        result_str = str(result)
        assert '3' in result_str
        assert 'ANY' in result_str
    
    def test_count_with_all_requirement(self):
        """Test count with ALL requirement."""
        from hub_auth_client.django.admin_helpers import format_count_with_requirement
        
        result = format_count_with_requirement(5, 'all')
        
        result_str = str(result)
        assert '5' in result_str
        assert 'ALL' in result_str
    
    def test_count_without_requirement(self):
        """Test count without requirement type."""
        from hub_auth_client.django.admin_helpers import format_count_with_requirement
        
        result = format_count_with_requirement(2, '')
        
        result_str = str(result)
        assert '2' in result_str
        assert 'ANY' not in result_str
        assert 'ALL' not in result_str
    
    def test_zero_count(self):
        """Test zero count returns dash."""
        from hub_auth_client.django.admin_helpers import format_count_with_requirement
        
        result = format_count_with_requirement(0, 'any')
        
        assert result == '-'


class TestFormatBadge:
    """Test the format_badge function."""
    
    def test_format_badge_default_color(self):
        """Test badge with default color."""
        from hub_auth_client.django.admin_helpers import format_badge
        
        result = format_badge('Test')
        
        result_str = str(result)
        assert 'Test' in result_str
        assert '#28a745' in result_str
    
    def test_format_badge_custom_color(self):
        """Test badge with custom color."""
        from hub_auth_client.django.admin_helpers import format_badge
        
        result = format_badge('Warning', '#ffc107')
        
        result_str = str(result)
        assert 'Warning' in result_str
        assert '#ffc107' in result_str


class TestFormatValidationBadges:
    """Test the format_validation_badges function."""
    
    def test_all_validations_enabled(self):
        """Test with all validations enabled."""
        from hub_auth_client.django.admin_helpers import format_validation_badges
        
        result = format_validation_badges(
            validate_audience=True,
            validate_issuer=True,
            token_leeway=10
        )
        
        result_str = str(result)
        assert 'AUD' in result_str
        assert 'ISS' in result_str
        assert 'Leeway: 10s' in result_str
    
    def test_no_validations(self):
        """Test with no validations enabled."""
        from hub_auth_client.django.admin_helpers import format_validation_badges
        
        result = format_validation_badges(
            validate_audience=False,
            validate_issuer=False,
            token_leeway=0
        )
        
        assert result == '-'
    
    def test_partial_validations(self):
        """Test with partial validations."""
        from hub_auth_client.django.admin_helpers import format_validation_badges
        
        result = format_validation_badges(
            validate_audience=True,
            validate_issuer=False,
            token_leeway=0
        )
        
        result_str = str(result)
        assert 'AUD' in result_str
        assert 'ISS' not in result_str


class TestFormatActionBadge:
    """Test the format_action_badge function."""
    
    def test_created_action(self):
        """Test created action badge."""
        from hub_auth_client.django.admin_helpers import format_action_badge
        
        result = format_action_badge('created')
        
        result_str = str(result)
        assert 'CREATED' in result_str
        assert '#28a745' in result_str
    
    def test_updated_action(self):
        """Test updated action badge."""
        from hub_auth_client.django.admin_helpers import format_action_badge
        
        result = format_action_badge('updated')
        
        result_str = str(result)
        assert 'UPDATED' in result_str
        assert '#17a2b8' in result_str
    
    def test_deleted_action(self):
        """Test deleted action badge."""
        from hub_auth_client.django.admin_helpers import format_action_badge
        
        result = format_action_badge('deleted')
        
        result_str = str(result)
        assert 'DELETED' in result_str
        assert '#dc3545' in result_str
    
    def test_unknown_action(self):
        """Test unknown action uses default color."""
        from hub_auth_client.django.admin_helpers import format_action_badge
        
        result = format_action_badge('unknown')
        
        result_str = str(result)
        assert 'UNKNOWN' in result_str
        assert '#6c757d' in result_str


class TestDatabaseHelpers:
    """Test database helper functions."""
    
    def test_is_postgresql_database(self):
        """Test PostgreSQL detection."""
        from hub_auth_client.django.admin_helpers import is_postgresql_database
        
        # Should work with test database (likely SQLite)
        result = is_postgresql_database()
        
        # Result is bool
        assert isinstance(result, bool)

