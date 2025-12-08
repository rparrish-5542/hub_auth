"""
Simple test script to verify hub_auth_client installation.

Usage:
    python verify_install.py
"""

import sys

def verify_installation():
    """Verify the hub_auth_client package is properly installed."""
    
    print("=" * 60)
    print("Hub Auth Client - Installation Verification")
    print("=" * 60)
    
    # Test 1: Import main package
    print("\n1. Testing package import...")
    try:
        import hub_auth_client
        print(f"   ✓ Package imported successfully")
        print(f"   ✓ Version: {hub_auth_client.__version__}")
    except ImportError as e:
        print(f"   ✗ Failed to import package: {e}")
        return False
    
    # Test 2: Import validator
    print("\n2. Testing validator import...")
    try:
        from hub_auth_client import MSALTokenValidator
        print(f"   ✓ MSALTokenValidator imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import validator: {e}")
        return False
    
    # Test 3: Import exceptions
    print("\n3. Testing exceptions import...")
    try:
        from hub_auth_client import (
            TokenValidationError,
            TokenExpiredError,
            InvalidTokenError,
            InsufficientScopesError,
        )
        print(f"   ✓ All exceptions imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import exceptions: {e}")
        return False
    
    # Test 4: Create validator instance
    print("\n4. Testing validator initialization...")
    try:
        validator = MSALTokenValidator(
            tenant_id="test-tenant-id",
            client_id="test-client-id"
        )
        print(f"   ✓ Validator created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create validator: {e}")
        return False
    
    # Test 5: Django integration (optional)
    print("\n5. Testing Django integration (optional)...")
    try:
        import django
        from django.conf import settings
        
        # Configure minimal Django settings if not configured
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django.contrib.contenttypes',
                    'django.contrib.auth',
                ],
                SECRET_KEY='test-secret-key',
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                }
            )
            django.setup()
        
        from hub_auth_client.django import (
            MSALAuthenticationMiddleware,
            MSALAuthentication,
            HasScopes,
            HasRoles,
            require_token,
            require_scopes,
        )
        print(f"   ✓ Django integration imported successfully")
    except ImportError as e:
        print(f"   ⚠ Django integration not available: {e}")
        print(f"   Note: Install with 'pip install hub-auth-client[django]' for Django support")
    except Exception as e:
        print(f"   ⚠ Django setup issue: {e}")
        print(f"   Note: This is expected in non-Django environments")
    
    print("\n" + "=" * 60)
    print("✓ Installation verification complete!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Configure Azure AD credentials in your .env file")
    print("2. Add to Django settings.py:")
    print("   AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')")
    print("   AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')")
    print("3. Use in your views with permission classes")
    print("\nSee README_PACKAGE.md for full documentation.")
    
    return True


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
