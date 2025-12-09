"""
Comprehensive test to check for potential Django admin compatibility issues.
"""
import os
import re

def check_django_admin_compatibility():
    """Check for common Django admin compatibility issues."""
    
    admin_file = os.path.join(os.path.dirname(__file__), 'hub_auth_client', 'django', 'admin.py')
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    warnings = []
    
    # Check 1: ChangeList subclasses should have all required attributes
    changelist_classes = re.findall(r'class\s+(\w+)\(ChangeList\):', content)
    print(f"Found {len(changelist_classes)} ChangeList subclass(es): {', '.join(changelist_classes)}")
    
    for cls_name in changelist_classes:
        # Extract the class definition
        class_pattern = rf'class\s+{cls_name}\(ChangeList\):.*?(?=\n    class |\n    def [a-z_]+\(|\nclass |\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if class_match:
            class_content = class_match.group(0)
            
            # Required ChangeList attributes for pagination
            required_attrs = {
                'result_count': 'Number of results',
                'full_result_count': 'Full result count without pagination',
                'multi_page': 'Whether results span multiple pages',
                'can_show_all': 'Whether "show all" is allowed',
                'show_all': 'Whether currently showing all results',
            }
            
            for attr, desc in required_attrs.items():
                if f'self.{attr}' not in class_content:
                    issues.append(f"{cls_name}: Missing '{attr}' attribute ({desc})")
    
    # Check 2: Look for ModelAdmin subclasses with custom changeListView
    modeladmin_classes = re.findall(r'class\s+(\w+)\(.*?ModelAdmin.*?\):', content)
    print(f"Found {len(modeladmin_classes)} ModelAdmin subclass(es): {', '.join(modeladmin_classes)}")
    
    for cls_name in modeladmin_classes:
        # Check if they override changelist_view
        if re.search(rf'class\s+{cls_name}.*?def changelist_view', content, re.DOTALL):
            print(f"  ✓ {cls_name} overrides changelist_view")
    
    # Check 3: Mock field classes should have critical Django field attributes
    mock_field_classes = re.findall(r'class\s+(Mock\w*Field).*?:', content)
    print(f"Found {len(mock_field_classes)} mock field class(es): {', '.join(mock_field_classes)}")
    
    for cls_name in mock_field_classes:
        class_pattern = rf'class\s+{cls_name}.*?(?=\n            class |\n        class |\n            def |\n        def |\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if class_match:
            class_content = class_match.group(0)
            
            # Critical field attributes used by Django admin
            critical_attrs = {
                'verbose_name': 'Field display name',
                'empty_values': 'Values considered empty',
                'is_relation': 'Whether field is a relation',
                'editable': 'Whether field is editable',
                'choices': 'Field choices (if any)',
            }
            
            for attr, desc in critical_attrs.items():
                if f'self.{attr}' not in class_content:
                    issues.append(f"{cls_name}: Missing '{attr}' attribute ({desc})")
    
    # Check 4: Look for uses of Django admin template tags
    template_tags = ['admin_list', 'admin_actions', 'pagination']
    for tag in template_tags:
        if tag in content.lower():
            print(f"  ℹ Uses template tag/function related to '{tag}'")
    
    # Check 5: Check for CSP-related inline script issues
    inline_script_pattern = r'<script[^>]*>(?!</script>)'
    inline_scripts = re.findall(inline_script_pattern, content)
    if inline_scripts:
        warnings.append(f"Found {len(inline_scripts)} potential inline script(s) - may cause CSP violations")
    
    # Check 6: Check for inline event handlers
    inline_handlers = re.findall(r'on\w+\s*=\s*["\']', content)
    if inline_handlers:
        warnings.append(f"Found {len(inline_handlers)} potential inline event handler(s) - may cause CSP violations")
    
    return issues, warnings

def check_template_files():
    """Check admin template files for potential issues."""
    
    template_dir = os.path.join(os.path.dirname(__file__), 'hub_auth_client', 'django', 'templates')
    
    if not os.path.exists(template_dir):
        print("No template directory found")
        return [], []
    
    issues = []
    warnings = []
    
    # Walk through template files
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, os.path.dirname(__file__))
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for inline scripts
                inline_scripts = re.findall(r'<script[^>]*>(?!</script>)', content)
                if inline_scripts:
                    warnings.append(f"{rel_path}: Contains {len(inline_scripts)} inline script(s)")
                
                # Check for inline event handlers
                inline_handlers = re.findall(r'\son\w+\s*=\s*["\']', content)
                if inline_handlers:
                    warnings.append(f"{rel_path}: Contains {len(inline_handlers)} inline event handler(s)")
                
                # Check for uses of cl.multi_page or other pagination attributes
                if 'cl.multi_page' in content:
                    print(f"  ✓ {rel_path} uses cl.multi_page")
                if 'cl.can_show_all' in content:
                    print(f"  ✓ {rel_path} uses cl.can_show_all")
    
    return issues, warnings

if __name__ == '__main__':
    print("=" * 70)
    print("Django Admin Compatibility Check")
    print("=" * 70)
    print()
    
    print("Checking admin.py...")
    print("-" * 70)
    admin_issues, admin_warnings = check_django_admin_compatibility()
    print()
    
    print("Checking template files...")
    print("-" * 70)
    template_issues, template_warnings = check_template_files()
    print()
    
    # Combine results
    all_issues = admin_issues + template_issues
    all_warnings = admin_warnings + template_warnings
    
    print("=" * 70)
    print("Results")
    print("=" * 70)
    
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} issue(s):")
        for issue in all_issues:
            print(f"  • {issue}")
    else:
        print("\n✅ No critical issues found!")
    
    if all_warnings:
        print(f"\n⚠️  Found {len(all_warnings)} warning(s):")
        for warning in all_warnings:
            print(f"  • {warning}")
    else:
        print("\n✅ No warnings!")
    
    print()
    
    if all_issues:
        exit(1)
    else:
        exit(0)
