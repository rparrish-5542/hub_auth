"""
Django management command to fetch available scopes from Azure AD App Registration.
Helps sync Azure AD scopes with Django ScopeDefinition model.

Usage:
    python manage.py fetch_azure_scopes
    python manage.py fetch_azure_scopes --import  # Import to database
    python manage.py fetch_azure_scopes --format=json
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json


class Command(BaseCommand):
    help = 'Fetch available scopes from Azure AD App Registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'json'],
            help='Output format (table, json)'
        )
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import_scopes',
            help='Import scopes into ScopeDefinition model'
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Azure AD Tenant ID (overrides settings)'
        )
        parser.add_argument(
            '--client-id',
            type=str,
            help='Azure AD Client/Application ID (overrides settings)'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Azure AD Client Secret (overrides settings)'
        )

    def handle(self, *args, **options):
        # Get Azure AD configuration
        config = self.get_azure_config(options)
        
        if not config:
            self.stderr.write(
                self.style.ERROR(
                    'Azure AD configuration not found. Please provide:\n'
                    '  - Settings: AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET\n'
                    '  - Or use: --tenant-id, --client-id, --client-secret\n'
                    '  - Or configure via database: AzureADConfiguration model'
                )
            )
            return
        
        # Fetch scopes from Azure AD
        scopes = self.fetch_scopes_from_azure(config)
        
        if not scopes:
            self.stdout.write(self.style.WARNING('No scopes found in Azure AD App Registration.'))
            return
        
        # Output scopes
        if options['format'] == 'json':
            self.output_json(scopes)
        else:
            self.output_table(scopes)
        
        # Import to database if requested
        if options['import_scopes']:
            self.import_scopes(scopes)

    def get_azure_config(self, options):
        """Get Azure AD configuration from various sources."""
        tenant_id = options.get('tenant_id')
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')
        
        # Try command line arguments first
        if tenant_id and client_id and client_secret:
            return {
                'tenant_id': tenant_id,
                'client_id': client_id,
                'client_secret': client_secret
            }
        
        # Try database configuration
        try:
            from hub_auth_client.django.config_models import AzureADConfiguration
            active_config = AzureADConfiguration.objects.filter(is_active=True).first()
            if active_config:
                return {
                    'tenant_id': active_config.tenant_id,
                    'client_id': active_config.client_id,
                    'client_secret': active_config.client_secret
                }
        except:
            pass
        
        # Try settings
        if hasattr(settings, 'AZURE_AD_TENANT_ID'):
            return {
                'tenant_id': settings.AZURE_AD_TENANT_ID,
                'client_id': settings.AZURE_AD_CLIENT_ID,
                'client_secret': getattr(settings, 'AZURE_AD_CLIENT_SECRET', None)
            }
        
        return None

    def fetch_scopes_from_azure(self, config):
        """Fetch scopes from Azure AD using Microsoft Graph API."""
        tenant_id = config['tenant_id']
        client_id = config['client_id']
        client_secret = config['client_secret']
        
        # Get access token for Microsoft Graph
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            self.stdout.write('Authenticating with Azure AD...')
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            access_token = token_response.json()['access_token']
            
            # Get application details from Microsoft Graph
            graph_url = f"https://graph.microsoft.com/v1.0/applications"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Filter by client ID
            params = {
                '$filter': f"appId eq '{client_id}'"
            }
            
            self.stdout.write('Fetching application details from Microsoft Graph...')
            app_response = requests.get(graph_url, headers=headers, params=params)
            app_response.raise_for_status()
            
            app_data = app_response.json()
            
            if not app_data.get('value'):
                self.stderr.write(
                    self.style.ERROR(f'Application not found for Client ID: {client_id}')
                )
                return []
            
            app = app_data['value'][0]
            
            # Debug: Show what we found
            self.stdout.write(f"Application ID: {app.get('id', 'N/A')}")
            self.stdout.write(f"Display Name: {app.get('displayName', 'N/A')}")
            self.stdout.write(f"App ID: {app.get('appId', 'N/A')}")
            
            # Debug: Show full app structure keys
            self.stdout.write(self.style.WARNING(f"DEBUG: Top-level app keys: {list(app.keys())}"))
            
            # Get identifier URIs
            identifier_uris = app.get('identifierUris', [])
            if identifier_uris:
                self.stdout.write(f"Identifier URIs: {', '.join(identifier_uris)}")
            else:
                self.stdout.write(self.style.WARNING("No identifier URIs found"))
            
            # Extract scopes from API permissions
            scopes = []
            
            # OAuth2 Permission Scopes (delegated permissions) - This is where exposed API scopes are
            if 'api' in app:
                self.stdout.write(self.style.SUCCESS(f"✓ Found 'api' key in app object"))
                self.stdout.write(self.style.WARNING(f"DEBUG: app['api'] keys: {list(app['api'].keys())}"))
                
                if 'oauth2PermissionScopes' in app['api']:
                    oauth_scopes = app['api']['oauth2PermissionScopes']
                    self.stdout.write(self.style.SUCCESS(f"✓ Found {len(oauth_scopes)} OAuth2 permission scopes"))
                    
                    for scope in oauth_scopes:
                        scope_value = scope.get('value', '')
                        
                        # Build full scope name with identifier URI if available
                        full_scope_name = scope_value
                        if identifier_uris and scope_value:
                            # Use first identifier URI as base
                            full_scope_name = f"{identifier_uris[0]}/{scope_value}"
                        
                        self.stdout.write(f"  - {full_scope_name} (enabled: {scope.get('isEnabled', True)})")
                        
                        scopes.append({
                            'name': full_scope_name,
                            'short_name': scope_value,
                            'description': scope.get('adminConsentDescription', scope.get('userConsentDescription', '')),
                            'category': 'delegated',
                            'type': 'oauth2',
                            'enabled': scope.get('isEnabled', True),
                            'admin_consent_required': scope.get('type', '') == 'Admin',
                            'id': scope.get('id', ''),
                            'identifier_uri': identifier_uris[0] if identifier_uris else None
                        })
                else:
                    self.stdout.write(self.style.ERROR("✗ No oauth2PermissionScopes found in app['api']"))
            else:
                self.stdout.write(self.style.ERROR("✗ No 'api' key found in app object"))
                self.stdout.write(self.style.WARNING(f"DEBUG: Available top-level keys: {list(app.keys())}"))
                self.stdout.write(self.style.WARNING(f"DEBUG: Keys containing 'api', 'scope', or 'permission': {[k for k in app.keys() if 'api' in k.lower() or 'scope' in k.lower() or 'permission' in k.lower()]}"))
                
                # Try alternative: use beta endpoint which has more details
                self.stdout.write(self.style.WARNING("\nTrying Microsoft Graph beta endpoint for more details..."))
                try:
                    beta_url = f"https://graph.microsoft.com/beta/applications/{app['id']}"
                    beta_response = requests.get(beta_url, headers=headers)
                    beta_response.raise_for_status()
                    beta_app = beta_response.json()
                    
                    self.stdout.write(self.style.WARNING(f"DEBUG: Beta endpoint keys: {list(beta_app.keys())}"))
                    
                    if 'api' in beta_app:
                        self.stdout.write(self.style.SUCCESS("✓ Found 'api' key in beta endpoint"))
                        self.stdout.write(self.style.WARNING(f"DEBUG: beta_app['api'] keys: {list(beta_app['api'].keys())}"))
                        
                        if 'oauth2PermissionScopes' in beta_app['api']:
                            oauth_scopes = beta_app['api']['oauth2PermissionScopes']
                            self.stdout.write(self.style.SUCCESS(f"✓ Found {len(oauth_scopes)} OAuth2 permission scopes in beta endpoint"))
                            
                            for scope in oauth_scopes:
                                scope_value = scope.get('value', '')
                                
                                # Build full scope name with identifier URI if available
                                full_scope_name = scope_value
                                if identifier_uris and scope_value:
                                    full_scope_name = f"{identifier_uris[0]}/{scope_value}"
                                
                                self.stdout.write(f"  - {full_scope_name} (enabled: {scope.get('isEnabled', True)})")
                                
                                scopes.append({
                                    'name': full_scope_name,
                                    'short_name': scope_value,
                                    'description': scope.get('adminConsentDescription', scope.get('userConsentDescription', '')),
                                    'category': 'delegated',
                                    'type': 'oauth2',
                                    'enabled': scope.get('isEnabled', True),
                                    'admin_consent_required': scope.get('type', '') == 'Admin',
                                    'id': scope.get('id', ''),
                                    'identifier_uri': identifier_uris[0] if identifier_uris else None
                                })
                        else:
                            self.stdout.write(self.style.ERROR("✗ No oauth2PermissionScopes in beta endpoint either"))
                            # Dump full beta app JSON for debugging
                            self.stdout.write(self.style.WARNING("\nDEBUG: Full beta app JSON:"))
                            self.stdout.write(json.dumps(beta_app, indent=2)[:2000])  # First 2000 chars
                    else:
                        self.stdout.write(self.style.ERROR("✗ No 'api' key in beta endpoint either"))
                        self.stdout.write(self.style.WARNING(f"DEBUG: Beta keys: {[k for k in beta_app.keys() if 'api' in k.lower() or 'scope' in k.lower() or 'permission' in k.lower()]}"))
                except Exception as beta_error:
                    self.stdout.write(self.style.ERROR(f"Error trying beta endpoint: {beta_error}"))

            
            # App Roles (application permissions)
            if 'appRoles' in app:
                for role in app['appRoles']:
                    if role.get('value'):  # Only include roles with values
                        scopes.append({
                            'name': role.get('value', ''),
                            'description': role.get('description', ''),
                            'category': 'application',
                            'type': 'app_role',
                            'enabled': role.get('isEnabled', True),
                            'allowed_member_types': role.get('allowedMemberTypes', []),
                            'id': role.get('id', '')
                        })
            
            # Required Resource Access (API permissions)
            if 'requiredResourceAccess' in app:
                for resource in app['requiredResourceAccess']:
                    resource_id = resource.get('resourceAppId', '')
                    for access in resource.get('resourceAccess', []):
                        scopes.append({
                            'name': f"{resource_id}:{access.get('id', '')}",
                            'description': f"Required permission: {access.get('type', '')}",
                            'category': 'required',
                            'type': access.get('type', ''),
                            'enabled': True,  # Required permissions are always enabled
                            'resource_app_id': resource_id,
                            'id': access.get('id', '')
                        })
            
            return scopes
            
        except requests.exceptions.RequestException as e:
            self.stderr.write(
                self.style.ERROR(f'Error fetching scopes from Azure AD: {e}')
            )
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    self.stderr.write(
                        self.style.ERROR(f'Response: {json.dumps(error_data, indent=2)}')
                    )
                except:
                    self.stderr.write(
                        self.style.ERROR(f'Response: {e.response.text}')
                    )
            return []

    def output_table(self, scopes):
        """Output scopes as a formatted table."""
        self.stdout.write(self.style.SUCCESS(f'\nFound {len(scopes)} scopes in Azure AD:\n'))
        
        # Header
        header = f"{'Scope Name':<40} {'Category':<15} {'Type':<15} {'Enabled':<10}"
        self.stdout.write(self.style.HTTP_INFO(header))
        self.stdout.write(self.style.HTTP_INFO('-' * len(header)))
        
        # Sort by category then name
        scopes.sort(key=lambda x: (x['category'], x['name']))
        
        # Rows
        for scope in scopes:
            name = scope['name'][:38]
            category = scope['category'][:13]
            scope_type = scope['type'][:13]
            enabled = '✓' if scope['enabled'] else '✗'
            
            row = f"{name:<40} {category:<15} {scope_type:<15} {enabled:<10}"
            self.stdout.write(row)
            
            # Show description
            if scope['description']:
                self.stdout.write(f"  → {scope['description'][:100]}")
        
        # Summary by category
        self.stdout.write('\n' + self.style.SUCCESS('Summary:'))
        categories = {}
        for scope in scopes:
            cat = scope['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            self.stdout.write(f"  {cat}: {count}")

    def output_json(self, scopes):
        """Output scopes as JSON."""
        self.stdout.write(json.dumps(scopes, indent=2))

    def import_scopes(self, scopes):
        """Import scopes into ScopeDefinition model."""
        try:
            from hub_auth_client.django.models import ScopeDefinition
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for scope_data in scopes:
                name = scope_data['name']
                
                if not name:
                    skipped_count += 1
                    continue
                
                # Check if scope exists
                scope, created = ScopeDefinition.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': scope_data.get('description', ''),
                        'category': scope_data.get('category', 'api'),
                        'is_active': scope_data.get('enabled', True)
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created scope: {name}')
                    )
                else:
                    # Update description if changed
                    if scope.description != scope_data.get('description', ''):
                        scope.description = scope_data.get('description', '')
                        scope.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'↻ Updated scope: {name}')
                        )
                    else:
                        skipped_count += 1
            
            # Summary
            self.stdout.write('\n' + self.style.SUCCESS('Import Summary:'))
            self.stdout.write(f'  Created: {created_count}')
            self.stdout.write(f'  Updated: {updated_count}')
            self.stdout.write(f'  Skipped: {skipped_count}')
            
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    'ScopeDefinition model not found. '
                    'Make sure hub_auth_client.django is in INSTALLED_APPS.'
                )
            )
