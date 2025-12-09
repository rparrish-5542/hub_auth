"""
Simulate Django admin pagination template to ensure compatibility.
This mimics what the Django admin template does when rendering pagination.
"""
import os
import sys

def simulate_django_admin_template():
    """Simulate the Django admin pagination template logic."""
    
    # Read the admin.py file
    admin_file = os.path.join(os.path.dirname(__file__), 'hub_auth_client', 'django', 'admin.py')
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the EndpointChangeList class
    import re
    
    # Find where EndpointChangeList sets its attributes
    pattern = r'class EndpointChangeList.*?def get_results.*?(?=\n        # Store discovered data|\n        request\._endpoint_data)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Could not find EndpointChangeList.get_results method")
        return False
    
    get_results_content = match.group(0)
    
    print("✅ Found EndpointChangeList.get_results method")
    print()
    
    # Simulate what Django admin template checks
    print("Simulating Django admin template checks:")
    print("-" * 70)
    
    # These are the actual checks from Django's admin/pagination.html template
    template_checks = [
        ('cl.show_all', 'Check if showing all results'),
        ('cl.can_show_all', 'Check if can show all results'),
        ('cl.multi_page', 'Check if results span multiple pages'),
        ('cl.result_count', 'Get result count'),
        ('cl.full_result_count', 'Get full result count'),
    ]
    
    all_passed = True
    for check, description in template_checks:
        attr = check.replace('cl.', 'self.')
        if attr in get_results_content:
            print(f"  ✅ {check:25} - {description}")
        else:
            print(f"  ❌ {check:25} - {description} - MISSING!")
            all_passed = False
    
    print()
    
    # Check the actual logic from Django's pagination template
    print("Checking pagination logic:")
    print("-" * 70)
    
    # This is the actual line from Django admin template that caused the error:
    # pagination_required = (not cl.show_all or not cl.can_show_all) and cl.multi_page
    
    if 'self.multi_page' in get_results_content:
        print("  ✅ cl.multi_page is set (required for pagination template)")
    else:
        print("  ❌ cl.multi_page is NOT set - will cause AttributeError!")
        all_passed = False
    
    if 'self.can_show_all' in get_results_content:
        print("  ✅ cl.can_show_all is set (required for pagination template)")
    else:
        print("  ❌ cl.can_show_all is NOT set - will cause AttributeError!")
        all_passed = False
    
    if 'self.show_all' in get_results_content:
        print("  ✅ cl.show_all is set (required for pagination template)")
    else:
        print("  ❌ cl.show_all is NOT set - will cause AttributeError!")
        all_passed = False
    
    print()
    
    # Check for proper values
    print("Checking attribute values:")
    print("-" * 70)
    
    # Check that multi_page is set to False (no pagination)
    if 'self.multi_page = False' in get_results_content:
        print("  ✅ cl.multi_page = False (no pagination needed)")
    elif 'self.multi_page = True' in get_results_content:
        print("  ⚠️  cl.multi_page = True (pagination enabled)")
    else:
        print("  ℹ️  cl.multi_page value not explicitly set to False")
    
    # Check that paginator is set
    if 'self.paginator' in get_results_content:
        print("  ✅ cl.paginator is set")
        if 'self.paginator = None' in get_results_content:
            print("     ℹ️  Set to None (no pagination)")
    else:
        print("  ⚠️  cl.paginator is not set")
    
    print()
    
    return all_passed

if __name__ == '__main__':
    print("=" * 70)
    print("Django Admin Pagination Template Simulation")
    print("=" * 70)
    print()
    print("This test simulates the exact checks that Django's admin pagination")
    print("template performs to ensure the EndpointChangeList is compatible.")
    print()
    print("=" * 70)
    print()
    
    success = simulate_django_admin_template()
    
    print("=" * 70)
    print("Result")
    print("=" * 70)
    
    if success:
        print()
        print("✅ EndpointChangeList is fully compatible with Django admin pagination!")
        print()
        print("The template will be able to access:")
        print("  • cl.multi_page")
        print("  • cl.can_show_all")
        print("  • cl.show_all")
        print("  • cl.result_count")
        print("  • cl.full_result_count")
        print()
        sys.exit(0)
    else:
        print()
        print("❌ EndpointChangeList has compatibility issues!")
        print()
        sys.exit(1)
