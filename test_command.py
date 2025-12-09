"""
Test calling the fetch_azure_scopes command directly with credentials.
This simulates what the Django admin does.
"""

import os
import sys
import django

# Add the hub_auth_client to the path
sys.path.insert(0, os.path.abspath('.'))

# Set up a minimal Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

# Configure Django settings inline
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'hub_auth_client.django',
        ],
        # Azure AD Configuration
        AZURE_AD_TENANT_ID='f03fc959-7ced-4f59-9cdc-cff28c052a9c',
        AZURE_AD_CLIENT_ID='1cc79b47-f087-4e09-8d9a-e31495e705bc',
        AZURE_AD_CLIENT_SECRET='SR08Q~ye3SmrcC~De1bEDDIcSBS9_5zqZeHfucPX',
    )

django.setup()

# Now test the command
from django.core.management import call_command
from io import StringIO

output = StringIO()

print("=" * 80)
print("TESTING FETCH_AZURE_SCOPES COMMAND")
print("=" * 80)
print()

try:
    # Call the command the same way the admin does (with --import flag)
    call_command('fetch_azure_scopes', '--import', stdout=output)
    
    result = output.getvalue()
    
    print("Command Output:")
    print("-" * 80)
    print(result)
    print("-" * 80)
    print()
    
    # Check what the admin would see
    if 'No scopes found' in result or 'Found 0 scopes' in result:
        print("❌ ADMIN WOULD SHOW: Warning - No scopes found")
    elif 'Created:' in result or 'Updated:' in result:
        print("✓ ADMIN WOULD SHOW: Success - Scopes synced")
    elif 'Found 1 scopes' in result or 'Found 1 OAuth2' in result:
        print("✓ COMMAND FOUND SCOPES")
    else:
        print("⚠ ADMIN WOULD SHOW: Info - Sync completed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
