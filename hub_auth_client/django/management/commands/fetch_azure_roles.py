"""
Django management command to fetch App Roles from Azure AD App Registration.
Helps sync Azure AD App Roles with Django RoleDefinition model.

App Roles are used for role-based access control in Azure AD applications.
They can be assigned to users, groups, or applications.

Usage:
    python manage.py fetch_azure_roles
    python manage.py fetch_azure_roles --import  # Import to database
    python manage.py fetch_azure_roles --format=json
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json


class Command(BaseCommand):
    help = 'Fetch App Roles from Azure AD App Registration'

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
            dest='import_roles',
            help='Import roles into RoleDefinition model'
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
        parser.add_argument(
            '--include-microsoft',
            action='store_true',
            help='Include Microsoft Graph roles (e.g., User.Read, Mail.Send)'
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
        
        # Fetch roles from Azure AD
        roles = self.fetch_roles_from_azure(config, options.get('include_microsoft', False))
        
        if not roles:
            self.stdout.write(self.style.WARNING('No App Roles found in Azure AD App Registration.'))
            return
        
        # Output roles
        if options['format'] == 'json':
            self.output_json(roles)
        else:
            self.output_table(roles)
        
        # Import to database if requested
        if options['import_roles']:
            self.import_roles(roles)

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

    def fetch_roles_from_azure(self, config, include_microsoft=False):
        """Fetch App Roles from Azure AD using Microsoft Graph API."""
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
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            roles = []
            
            # Get application details from Microsoft Graph
            graph_url = f"https://graph.microsoft.com/v1.0/applications"
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
            
            # Display app info
            self.stdout.write(self.style.SUCCESS(f"\n✓ Found Application:"))
            self.stdout.write(f"  Display Name: {app.get('displayName', 'N/A')}")
            self.stdout.write(f"  App ID: {app.get('appId', 'N/A')}")
            self.stdout.write(f"  Object ID: {app.get('id', 'N/A')}")
            
            # Extract App Roles
            if 'appRoles' in app and app['appRoles']:
                app_roles = app['appRoles']
                self.stdout.write(self.style.SUCCESS(f"\n✓ Found {len(app_roles)} App Roles"))
                
                for role in app_roles:
                    if not role.get('isEnabled', True):
                        self.stdout.write(self.style.WARNING(f"  ⚠ Skipping disabled role: {role.get('value', 'N/A')}"))
                        continue
                    
                    role_value = role.get('value', '')
                    if not role_value:
                        continue
                    
                    self.stdout.write(f"  - {role_value}")
                    
                    roles.append({
                        'name': role_value,
                        'description': role.get('description', role.get('displayName', '')),
                        'display_name': role.get('displayName', role_value),
                        'is_enabled': role.get('isEnabled', True),
                        'allowed_member_types': role.get('allowedMemberTypes', []),
                        'id': role.get('id', ''),
                        'source': 'app_registration',
                        'category': self.get_role_category(role)
                    })
            else:
                self.stdout.write(self.style.WARNING("\n⚠ No App Roles defined in this application"))
                self.stdout.write(self.style.HTTP_INFO(
                    "\nTo add App Roles:\n"
                    "1. Go to Azure Portal > App Registrations > Your App\n"
                    "2. Select 'App roles' in the left menu\n"
                    "3. Click '+ Create app role'\n"
                    "4. Define role name, value, description, and who can be assigned\n"
                ))
            
            # Optionally fetch Microsoft Graph roles
            if include_microsoft:
                self.stdout.write('\nFetching Microsoft Graph API roles...')
                ms_roles = self.fetch_microsoft_graph_roles(headers)
                roles.extend(ms_roles)
            
            return roles
            
        except requests.exceptions.RequestException as e:
            self.stderr.write(
                self.style.ERROR(f'Error fetching roles from Azure AD: {e}')
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

    def fetch_microsoft_graph_roles(self, headers):
        """Fetch available Microsoft Graph App Roles."""
        roles = []
        try:
            # Microsoft Graph Service Principal ID
            ms_graph_sp_url = "https://graph.microsoft.com/v1.0/servicePrincipals"
            params = {
                '$filter': "appId eq '00000003-0000-0000-c000-000000000000'"  # Microsoft Graph
            }
            
            response = requests.get(ms_graph_sp_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('value'):
                ms_graph = data['value'][0]
                
                if 'appRoles' in ms_graph:
                    self.stdout.write(self.style.SUCCESS(f"\n✓ Found {len(ms_graph['appRoles'])} Microsoft Graph roles"))
                    
                    for role in ms_graph['appRoles']:
                        if role.get('isEnabled', True) and role.get('value'):
                            roles.append({
                                'name': role.get('value', ''),
                                'description': role.get('description', role.get('displayName', '')),
                                'display_name': role.get('displayName', role.get('value', '')),
                                'is_enabled': role.get('isEnabled', True),
                                'allowed_member_types': role.get('allowedMemberTypes', []),
                                'id': role.get('id', ''),
                                'source': 'microsoft_graph',
                                'category': 'microsoft_graph'
                            })
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not fetch Microsoft Graph roles: {e}"))
        
        return roles

    def get_role_category(self, role):
        """Determine role category based on allowed member types."""
        member_types = role.get('allowedMemberTypes', [])
        
        if 'User' in member_types and 'Application' in member_types:
            return 'user_and_application'
        elif 'User' in member_types:
            return 'user'
        elif 'Application' in member_types:
            return 'application'
        else:
            return 'unknown'

    def output_table(self, roles):
        """Output roles as a formatted table."""
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS(f'Found {len(roles)} App Roles'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))
        
        # Header
        header = f"{'Role Name':<30} {'Category':<20} {'Source':<20} {'Enabled':<10}"
        self.stdout.write(self.style.HTTP_INFO(header))
        self.stdout.write(self.style.HTTP_INFO('─' * 80))
        
        # Sort by source then name
        roles.sort(key=lambda x: (x.get('source', ''), x['name']))
        
        # Rows
        for role in roles:
            name = role['name'][:28]
            category = role.get('category', 'N/A')[:18]
            source = role.get('source', 'N/A')[:18]
            enabled = '✓' if role.get('is_enabled', True) else '✗'
            
            row = f"{name:<30} {category:<20} {source:<20} {enabled:<10}"
            
            if role.get('is_enabled', True):
                self.stdout.write(self.style.SUCCESS(row))
            else:
                self.stdout.write(self.style.WARNING(row))
            
            # Show description
            if role.get('description'):
                desc = role['description'][:100]
                self.stdout.write(f"  → {desc}")
            
            # Show allowed member types
            if role.get('allowed_member_types'):
                members = ', '.join(role['allowed_member_types'])
                self.stdout.write(self.style.HTTP_INFO(f"  ↳ Assignable to: {members}"))
        
        # Summary by category
        self.stdout.write('\n' + self.style.SUCCESS('─' * 80))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        categories = {}
        for role in roles:
            cat = role.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            self.stdout.write(f"  {cat}: {count}")
        
        self.stdout.write(self.style.SUCCESS('─' * 80))

    def output_json(self, roles):
        """Output roles as JSON."""
        self.stdout.write(json.dumps(roles, indent=2))

    def import_roles(self, roles):
        """Import roles into RoleDefinition model."""
        try:
            from hub_auth_client.django.models import RoleDefinition
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for role_data in roles:
                name = role_data['name']
                
                if not name:
                    skipped_count += 1
                    continue
                
                # Check if role exists
                role, created = RoleDefinition.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': role_data.get('description', ''),
                        'category': role_data.get('category', 'custom'),
                        'is_active': role_data.get('is_enabled', True)
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created role: {name}')
                    )
                else:
                    # Update description if changed
                    changed = False
                    if role.description != role_data.get('description', ''):
                        role.description = role_data.get('description', '')
                        changed = True
                    
                    if role.category != role_data.get('category', 'custom'):
                        role.category = role_data.get('category', 'custom')
                        changed = True
                    
                    if changed:
                        role.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'↻ Updated role: {name}')
                        )
                    else:
                        skipped_count += 1
            
            # Summary
            self.stdout.write('\n' + self.style.SUCCESS('═' * 80))
            self.stdout.write(self.style.SUCCESS('Import Summary:'))
            self.stdout.write(self.style.SUCCESS('═' * 80))
            self.stdout.write(f'  ✓ Created: {created_count}')
            self.stdout.write(f'  ↻ Updated: {updated_count}')
            self.stdout.write(f'  ─ Skipped: {skipped_count}')
            self.stdout.write(self.style.SUCCESS('═' * 80))
            
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    'RoleDefinition model not found. '
                    'Make sure hub_auth_client.django is in INSTALLED_APPS.'
                )
            )
