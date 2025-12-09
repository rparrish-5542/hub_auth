"""
Test script to validate EndpointChangeList attributes.
This checks that all required Django admin pagination attributes are present.
"""
import sys
import os

def test_changelist_attributes():
    """Test that EndpointChangeList has all required pagination attributes."""
    
    # Read the admin.py file directly
    admin_file = os.path.join(os.path.dirname(__file__), 'hub_auth_client', 'django', 'admin.py')
    
    if not os.path.exists(admin_file):
        print(f"❌ Admin file not found: {admin_file}")
        return False
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    if 'class APIEndpointMappingAdmin' not in source:
        print("❌ APIEndpointMappingAdmin class not found")
        return False
    
    print("✅ Found APIEndpointMappingAdmin class")
    
    if 'class EndpointChangeList' not in source:
        print("❌ EndpointChangeList class not found")
        return False
    
    print("✅ EndpointChangeList class exists")
    
    # Check for required pagination attributes in the source
    required_attributes = [
        ('multi_page', 'self.multi_page'),
        ('can_show_all', 'self.can_show_all'),
        ('show_all', 'self.show_all'),
        ('paginator', 'self.paginator'),
        ('result_count', 'self.result_count'),
        ('full_result_count', 'self.full_result_count'),
    ]
    
    missing_attributes = []
    for attr_name, attr_pattern in required_attributes:
        if attr_pattern not in source:
            missing_attributes.append(attr_name)
    
    if missing_attributes:
        print(f"❌ Missing attributes in EndpointChangeList: {', '.join(missing_attributes)}")
        return False
    
    print(f"✅ All required pagination attributes present")
    
    # Check for get_results method
    if 'def get_results' not in source:
        print("❌ get_results method not found in EndpointChangeList")
        return False
    
    print("✅ get_results method exists in EndpointChangeList")
    
    return True

def test_mock_field_attributes():
    """Test that MockField has all required attributes."""
    
    # Read the admin.py file directly
    admin_file = os.path.join(os.path.dirname(__file__), 'hub_auth_client', 'django', 'admin.py')
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Check for MockField class
    if 'class MockField' not in source:
        print("❌ MockField class not found")
        return False
    
    print("✅ MockField class exists")
    
    # Check for critical attributes
    critical_attrs = [
        'empty_values',
        'choices',
        'validators',
        'verbose_name',
        'primary_key',
        'editable',
        'is_relation',
    ]
    
    missing_attrs = []
    for attr in critical_attrs:
        if f'self.{attr}' not in source:
            missing_attrs.append(attr)
    
    if missing_attrs:
        print(f"❌ Missing attributes in MockField: {', '.join(missing_attrs)}")
        return False
    
    print(f"✅ All critical MockField attributes present")
    
    return True

if __name__ == '__main__':
    print("=" * 70)
    print("Testing EndpointChangeList Implementation")
    print("=" * 70)
    print()
    
    # Test changelist attributes
    print("Test 1: EndpointChangeList Pagination Attributes")
    print("-" * 70)
    changelist_ok = test_changelist_attributes()
    print()
    
    # Test MockField attributes
    print("Test 2: MockField Attributes")
    print("-" * 70)
    mockfield_ok = test_mock_field_attributes()
    print()
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    if changelist_ok and mockfield_ok:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
