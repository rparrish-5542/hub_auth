"""
Example: Using database-driven Azure AD configuration.

This example shows how to use AzureADConfiguration model to store
credentials in database instead of environment variables.
"""

from django.conf import settings
from hub_auth_client.django import AzureADConfiguration


# ============================================================================
# EXAMPLE 1: Get Active Configuration
# ============================================================================

def get_current_config():
    """Get the currently active Azure AD configuration."""
    config = AzureADConfiguration.get_active_config()
    
    if config:
        print(f"Active Configuration: {config.name}")
        print(f"Tenant ID: {config.tenant_id}")
        print(f"Client ID: {config.client_id}")
        print(f"Token Version: {config.token_version}")
        print(f"Validate Audience: {config.validate_audience}")
        print(f"Validate Issuer: {config.validate_issuer}")
        print(f"Exempt Paths: {config.get_exempt_paths()}")
    else:
        print("No active configuration found")
        print("Either configure via admin or use environment variables")


# ============================================================================
# EXAMPLE 2: Create Configuration Programmatically
# ============================================================================

def create_production_config():
    """Create a production Azure AD configuration."""
    config = AzureADConfiguration.objects.create(
        name="Production",
        tenant_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        client_id="f9e8d7c6-b5a4-3210-fedc-ba9876543210",
        token_version="2.0",
        validate_audience=True,
        validate_issuer=True,
        token_leeway=0,
        exempt_paths=["/admin/", "/health/", "/api/docs/"],
        is_active=True,
        description="Production Azure AD configuration",
        created_by="admin"
    )
    
    print(f"Created configuration: {config.name}")
    return config


# ============================================================================
# EXAMPLE 3: Switch Between Environments
# ============================================================================

def switch_to_development():
    """Switch from production to development configuration."""
    # Deactivate all configs
    AzureADConfiguration.objects.all().update(is_active=False)
    
    # Activate development config
    dev_config = AzureADConfiguration.objects.get(name="Development")
    dev_config.is_active = True
    dev_config.save()
    
    print(f"Switched to: {dev_config.name}")


# ============================================================================
# EXAMPLE 4: Get Validator from Configuration
# ============================================================================

def validate_token_with_db_config(token):
    """Validate a token using database configuration."""
    config = AzureADConfiguration.get_active_config()
    
    if not config:
        print("No active configuration found")
        return
    
    # Get validator from config
    validator = config.get_validator()
    
    # Validate token
    is_valid, claims, error = validator.validate_token(token)
    
    if is_valid:
        print("✓ Token is valid!")
        print(f"User: {claims.get('upn')}")
        print(f"Scopes: {claims.get('scp', '').split()}")
        print(f"Roles: {claims.get('roles', [])}")
    else:
        print(f"✗ Token invalid: {error}")


# ============================================================================
# EXAMPLE 5: Test Configuration
# ============================================================================

def test_configuration(config_name):
    """Test if a configuration can connect to Azure AD."""
    try:
        config = AzureADConfiguration.objects.get(name=config_name)
        
        # Get validator
        validator = config.get_validator()
        
        # Try to get signing keys (verifies connectivity)
        if hasattr(validator, '_get_signing_keys'):
            keys = validator._get_signing_keys()
            if keys:
                print(f"✓ Configuration '{config_name}' tested successfully")
                print(f"  Found {len(keys)} signing keys from Azure AD")
                return True
            else:
                print(f"✗ No signing keys found for '{config_name}'")
                return False
        else:
            print(f"✓ Configuration '{config_name}' created successfully")
            return True
            
    except AzureADConfiguration.DoesNotExist:
        print(f"✗ Configuration '{config_name}' not found")
        return False
    except Exception as e:
        print(f"✗ Error testing '{config_name}': {str(e)}")
        return False


# ============================================================================
# EXAMPLE 6: View Configuration History
# ============================================================================

def view_config_history(config_name):
    """View change history for a configuration."""
    try:
        config = AzureADConfiguration.objects.get(name=config_name)
        
        print(f"Configuration History: {config_name}")
        print("=" * 60)
        
        for entry in config.history.all()[:10]:  # Last 10 changes
            print(f"{entry.changed_at:%Y-%m-%d %H:%M} | "
                  f"{entry.action:12} | "
                  f"{entry.changed_by:15} | "
                  f"{entry.details}")
            
    except AzureADConfiguration.DoesNotExist:
        print(f"Configuration '{config_name}' not found")


# ============================================================================
# EXAMPLE 7: Multi-Tenant Setup
# ============================================================================

def setup_multi_tenant_configs():
    """Create configurations for multiple tenants."""
    
    tenants = [
        {
            "name": "Tenant A - Customer Corp",
            "tenant_id": "tenant-a-guid-here",
            "client_id": "client-a-guid-here",
            "description": "Customer Corp Azure AD",
        },
        {
            "name": "Tenant B - Partner Inc",
            "tenant_id": "tenant-b-guid-here",
            "client_id": "client-b-guid-here",
            "description": "Partner Inc Azure AD",
        },
        {
            "name": "Tenant C - Client LLC",
            "tenant_id": "tenant-c-guid-here",
            "client_id": "client-c-guid-here",
            "description": "Client LLC Azure AD",
        },
    ]
    
    for tenant in tenants:
        config, created = AzureADConfiguration.objects.get_or_create(
            name=tenant["name"],
            defaults={
                "tenant_id": tenant["tenant_id"],
                "client_id": tenant["client_id"],
                "description": tenant["description"],
                "is_active": False,  # Manually activate one
            }
        )
        
        if created:
            print(f"✓ Created: {config.name}")
        else:
            print(f"  Exists: {config.name}")


# ============================================================================
# EXAMPLE 8: Get All Configurations
# ============================================================================

def list_all_configurations():
    """List all Azure AD configurations."""
    configs = AzureADConfiguration.objects.all()
    
    print("Azure AD Configurations")
    print("=" * 60)
    
    for config in configs:
        status = "✓ ACTIVE" if config.is_active else "○ Inactive"
        print(f"{status:12} | {config.name:30} | v{config.token_version}")
        print(f"             Tenant: {config.tenant_id[:8]}...{config.tenant_id[-8:]}")
        print(f"             Client: {config.client_id[:8]}...{config.client_id[-8:]}")
        print()


# ============================================================================
# EXAMPLE 9: Django Management Command
# ============================================================================

"""
Create a Django management command to manage configurations:

# management/commands/manage_azure_config.py

from django.core.management.base import BaseCommand
from hub_auth_client.django import AzureADConfiguration

class Command(BaseCommand):
    help = 'Manage Azure AD configurations'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['list', 'activate', 'test'])
        parser.add_argument('--name', help='Configuration name')

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            for config in AzureADConfiguration.objects.all():
                status = "ACTIVE" if config.is_active else "Inactive"
                self.stdout.write(f"{status:10} {config.name}")
        
        elif action == 'activate':
            config = AzureADConfiguration.objects.get(name=options['name'])
            AzureADConfiguration.objects.all().update(is_active=False)
            config.is_active = True
            config.save()
            self.stdout.write(self.style.SUCCESS(f"Activated: {config.name}"))
        
        elif action == 'test':
            config = AzureADConfiguration.objects.get(name=options['name'])
            validator = config.get_validator()
            self.stdout.write(self.style.SUCCESS(f"Config '{config.name}' is valid"))
"""


# ============================================================================
# EXAMPLE 10: Settings.py Configuration Check
# ============================================================================

def check_configuration_source():
    """Check if using database config or environment variables."""
    from hub_auth_client.django import CONFIG_AVAILABLE
    
    if not CONFIG_AVAILABLE:
        print("Database configuration not available")
        print("Using environment variables")
        return
    
    config = AzureADConfiguration.get_active_config()
    
    if config:
        print(f"✓ Using database configuration: {config.name}")
        print(f"  Tenant: {config.tenant_id}")
        print(f"  Client: {config.client_id}")
    else:
        print("No active database configuration found")
        
        # Check if environment variables are set
        tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
        client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
        
        if tenant_id and client_id:
            print("✓ Using environment variables")
            print(f"  Tenant: {tenant_id}")
            print(f"  Client: {client_id}")
        else:
            print("✗ No configuration found!")
            print("  Configure via admin or set environment variables")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Get current config
    get_current_config()
    
    # List all configs
    list_all_configurations()
    
    # Check configuration source
    check_configuration_source()
    
    # Test a configuration
    test_configuration("Production")
    
    # View history
    view_config_history("Production")
