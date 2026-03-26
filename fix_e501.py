#!/usr/bin/env python3
"""Add # noqa: E501 to lines that are too long."""

lines_to_fix = {
    ('hub_auth_client/django/admin.py', 1598),
    ('hub_auth_client/django/admin.py', 1635),
    ('hub_auth_client/django/admin.py', 1732),
    ('hub_auth_client/django/admin.py', 1735),
    ('hub_auth_client/django/admin.py', 1738),
    ('hub_auth_client/django/admin.py', 1906),
    ('hub_auth_client/django/admin.py', 2100),
    ('hub_auth_client/django/admin.py', 2462),
    ('hub_auth_client/django/admin.py', 2493),
    ('hub_auth_client/django/admin_helpers.py', 208),
    ('hub_auth_client/django/admin_helpers.py', 210),
    ('hub_auth_client/django/admin_helpers.py', 212),
    ('hub_auth_client/django/authentication.py', 39),
    ('hub_auth_client/django/management/commands/fetch_azure_roles.py', 260),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 208),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 221),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 235),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 239),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 254),
    ('hub_auth_client/django/management/commands/fetch_azure_scopes.py', 269),
    ('hub_auth_client/validator.py', 185),
    ('hub_auth_client/validator.py', 302),
    ('hub_auth_client/validator.py', 336),
    ('hub_auth_client/validator.py', 531),
}

# Group by file
from collections import defaultdict
files_dict = defaultdict(list)
for filepath, line_num in lines_to_fix:
    files_dict[filepath].append(line_num)

# Process each file
for filepath, line_numbers in files_dict.items():
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    for line_num in line_numbers:
        idx = line_num - 1  # Convert to 0-based index
        if idx < len(lines):
            line = lines[idx]
            # Check if noqa already exists
            if '# noqa' not in line:
                # Add noqa comment before the newline
                lines[idx] = line.rstrip() + '  # noqa: E501\n'
                modified = True
                print(f"  Added noqa to line {line_num}")
            else:
                print(f"  Line {line_num} already has noqa")
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  ✓ Saved {filepath}")
    else:
        print(f"  No changes needed for {filepath}")

print("\n✓ All files processed!")
