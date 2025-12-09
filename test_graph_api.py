"""
Test script to diagnose Azure AD scope fetching issues.
This will show you exactly what the Microsoft Graph API returns.

Usage:
    python test_graph_api.py
"""

import requests
import json
import sys

# Configuration - UPDATE THESE VALUES
TENANT_ID = "f03fc959-7ced-4f59-9cdc-cff28c052a9c"
CLIENT_ID = "1cc79b47-f087-4e09-8d9a-e31495e705bc"
CLIENT_SECRET = "SR08Q~ye3SmrcC~De1bEDDIcSBS9_5zqZeHfucPX"

def test_graph_api():
    """Test fetching scopes from Microsoft Graph API."""
    
    print("=" * 80)
    print("AZURE AD SCOPE DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Step 1: Get Access Token
    print("Step 1: Getting access token...")
    print(f"  Tenant ID: {TENANT_ID}")
    print(f"  Client ID: {CLIENT_ID}")
    print()
    
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        access_token = token_response.json()['access_token']
        print("✓ Successfully obtained access token")
        print()
    except Exception as e:
        print(f"✗ Error getting access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
    
    # Step 2: Get Application Details (v1.0)
    print("Step 2: Fetching application details (v1.0 endpoint)...")
    graph_url = f"https://graph.microsoft.com/v1.0/applications"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
        '$filter': f"appId eq '{CLIENT_ID}'"
    }
    
    try:
        app_response = requests.get(graph_url, headers=headers, params=params)
        app_response.raise_for_status()
        app_data = app_response.json()
        
        if not app_data.get('value'):
            print(f"✗ Application not found for Client ID: {CLIENT_ID}")
            sys.exit(1)
        
        app = app_data['value'][0]
        print(f"✓ Application found")
        print(f"  Display Name: {app.get('displayName', 'N/A')}")
        print(f"  App ID: {app.get('appId', 'N/A')}")
        print(f"  Object ID: {app.get('id', 'N/A')}")
        print()
        
        # Check identifier URIs
        identifier_uris = app.get('identifierUris', [])
        print(f"Identifier URIs: {identifier_uris if identifier_uris else 'None'}")
        print()
        
        # Check for API key
        print("Checking for 'api' key in response...")
        if 'api' in app:
            print("✓ 'api' key found!")
            print(f"  Keys in 'api': {list(app['api'].keys())}")
            print()
            
            if 'oauth2PermissionScopes' in app['api']:
                scopes = app['api']['oauth2PermissionScopes']
                print(f"✓ Found {len(scopes)} OAuth2 Permission Scopes:")
                print()
                
                for i, scope in enumerate(scopes, 1):
                    scope_value = scope.get('value', 'NO VALUE')
                    full_name = scope_value
                    if identifier_uris and scope_value:
                        full_name = f"{identifier_uris[0]}/{scope_value}"
                    
                    print(f"  Scope #{i}:")
                    print(f"    Value: {scope_value}")
                    print(f"    Full Name: {full_name}")
                    print(f"    Enabled: {scope.get('isEnabled', False)}")
                    print(f"    Type: {scope.get('type', 'N/A')}")
                    print(f"    Admin Consent: {scope.get('adminConsentDescription', 'N/A')}")
                    print(f"    User Consent: {scope.get('userConsentDescription', 'N/A')}")
                    print()
            else:
                print("✗ No 'oauth2PermissionScopes' in api object")
                print(f"  Available keys: {list(app['api'].keys())}")
        else:
            print("✗ No 'api' key found in response!")
            print(f"  Top-level keys: {list(app.keys())}")
            print()
            
            # Try beta endpoint
            print("Step 3: Trying beta endpoint...")
            beta_url = f"https://graph.microsoft.com/beta/applications/{app['id']}"
            beta_response = requests.get(beta_url, headers=headers)
            beta_response.raise_for_status()
            beta_app = beta_response.json()
            
            print(f"  Beta endpoint top-level keys: {list(beta_app.keys())}")
            
            if 'api' in beta_app:
                print("✓ 'api' key found in beta endpoint!")
                print(f"  Keys in 'api': {list(beta_app['api'].keys())}")
                
                if 'oauth2PermissionScopes' in beta_app['api']:
                    scopes = beta_app['api']['oauth2PermissionScopes']
                    print(f"✓ Found {len(scopes)} OAuth2 Permission Scopes in beta:")
                    
                    for i, scope in enumerate(scopes, 1):
                        scope_value = scope.get('value', 'NO VALUE')
                        print(f"  Scope #{i}: {scope_value} (enabled: {scope.get('isEnabled')})")
            print()
        
        # Show full JSON for debugging
        print("=" * 80)
        print("FULL RESPONSE JSON (v1.0 endpoint):")
        print("=" * 80)
        print(json.dumps(app, indent=2))
        
    except Exception as e:
        print(f"✗ Error fetching application: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if config is set
    if TENANT_ID == "your-tenant-id-here":
        print("ERROR: Please update TENANT_ID, CLIENT_ID, and CLIENT_SECRET in this script")
        print()
        print("Edit the top of the file and replace:")
        print('  TENANT_ID = "your-tenant-id-here"')
        print('  CLIENT_ID = "your-client-id-here"')
        print('  CLIENT_SECRET = "your-client-secret-here"')
        sys.exit(1)
    
    test_graph_api()
