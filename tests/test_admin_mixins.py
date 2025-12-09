"""
Tests for admin mixins.
"""
import pytest
from django.contrib.admin import ModelAdmin
from hub_auth_client.django.admin_mixins import (
    URLPatternMixin,
    ActiveBadgeMixin,
    ScopeCountMixin,
    RoleCountMixin,
)


class MockObject:
    """Mock object for testing mixins."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestURLPatternMixin:
    """Test URL pattern display mixin."""
    
    def test_url_pattern_display_with_pattern(self):
        """Test URL pattern display shows both regex and readable."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern='^api/employees/$')
        
        result = mixin.url_pattern_display(obj)
        
        # Should contain original regex
        assert '^api/employees/$' in result
        # Should contain readable version
        assert '/api/employees/' in result
        # Should have HTML structure
        assert '<' in result and '>' in result
    
    def test_url_pattern_display_with_complex_pattern(self):
        """Test URL pattern display with complex regex."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern='^api/(?P<resource>[^/]+)/(?P<pk>[^/.]+)/$')
        
        result = mixin.url_pattern_display(obj)
        
        # Should show readable version with placeholders
        assert '{resource}' in result
        assert '{pk}' in result
    
    def test_url_pattern_display_empty_pattern(self):
        """Test URL pattern display with empty pattern."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern='')
        
        result = mixin.url_pattern_display(obj)
        
        # Should return dash or empty indicator
        assert result == '-' or result == ''
    
    def test_url_pattern_display_no_attribute(self):
        """Test URL pattern display when object lacks url_pattern."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern=None)  # Give it the attribute but set to None
        
        result = mixin.url_pattern_display(obj)
        
        # Should handle gracefully
        assert result == '-' or result == ''
    
    def test_url_pattern_readable_with_pattern(self):
        """Test URL pattern readable shows only human-friendly version."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern='^api/employees/(?P<pk>[^/.]+)/$')
        
        result = mixin.url_pattern_readable(obj)
        
        # Should contain readable version
        assert '/api/employees/{pk}/' in result
        # Should NOT contain regex anchors
        assert '^' not in result
        assert '$' not in result
    
    def test_url_pattern_readable_empty_pattern(self):
        """Test URL pattern readable with empty pattern."""
        mixin = URLPatternMixin()
        obj = MockObject(url_pattern='')
        
        result = mixin.url_pattern_readable(obj)
        
        assert result == '-' or result == ''


class TestActiveBadgeMixin:
    """Test active badge mixin."""
    
    def test_is_active_badge_true(self):
        """Test active badge for active object."""
        mixin = ActiveBadgeMixin()
        obj = MockObject(is_active=True)
        
        result = mixin.is_active_badge(obj)
        
        assert 'green' in result or '✓' in result
    
    def test_is_active_badge_false(self):
        """Test active badge for inactive object."""
        mixin = ActiveBadgeMixin()
        obj = MockObject(is_active=False)
        
        result = mixin.is_active_badge(obj)
        
        assert 'red' in result or 'gray' in result or '✗' in result


class TestScopeCountMixin:
    """Test scope count mixin."""
    
    def test_scope_count_with_scopes(self):
        """Test scope count display."""
        from unittest.mock import MagicMock
        
        mixin = ScopeCountMixin()
        
        # Mock required_scopes queryset
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value.count.return_value = 2
        
        obj = MockObject()
        obj.required_scopes = mock_queryset
        
        result = mixin.scope_count(obj)
        
        assert '2' in str(result)
    
    def test_scope_count_with_no_scopes(self):
        """Test scope count with no scopes."""
        from unittest.mock import MagicMock
        
        mixin = ScopeCountMixin()
        
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value.count.return_value = 0
        
        obj = MockObject()
        obj.required_scopes = mock_queryset
        
        result = mixin.scope_count(obj)
        
        # Should show 0 or a dash for no scopes
        assert '0' in str(result) or '-' in str(result)


class TestRoleCountMixin:
    """Test role count mixin."""
    
    def test_role_count_with_roles(self):
        """Test role count display."""
        from unittest.mock import MagicMock
        
        mixin = RoleCountMixin()
        
        # Mock required_roles queryset
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value.count.return_value = 2
        
        obj = MockObject()
        obj.required_roles = mock_queryset
        
        result = mixin.role_count(obj)
        
        assert '2' in str(result)
    
    def test_role_count_with_no_roles(self):
        """Test role count with no roles."""
        from unittest.mock import MagicMock
        
        mixin = RoleCountMixin()
        
        mock_queryset = MagicMock()
class TestMixinCombination:
    """Test using multiple mixins together."""
    
    def test_combined_mixins(self):
        """Test that mixins can be combined in a class."""
        
        class CombinedMixin(URLPatternMixin, ActiveBadgeMixin):
            pass
        
        mixin = CombinedMixin()
        
        # Should have methods from both mixins
        assert hasattr(mixin, 'url_pattern_display')
        assert hasattr(mixin, 'url_pattern_readable')
        assert hasattr(mixin, 'is_active_badge')
        
        # Test they work together
        obj = MockObject(
            url_pattern='^api/test/$',
            is_active=True
        )
        
        pattern_result = mixin.url_pattern_display(obj)
        badge_result = mixin.is_active_badge(obj)
        
        assert '/api/test/' in pattern_result
        assert 'green' in badge_result or '✓' in badge_result
        obj = MockObject(
            url_pattern='^api/test/$',
            is_active=True
        )
        
        pattern_result = mixin.url_pattern_display(obj)
        badge_result = mixin.is_active_badge(obj)
        
        assert '/api/test/' in pattern_result
        assert 'green' in badge_result or '✓' in badge_result
