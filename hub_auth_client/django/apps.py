"""
Django app configuration for hub_auth_client.
"""

from django.apps import AppConfig


class HubAuthClientConfig(AppConfig):
    """App configuration for hub_auth_client Django integration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hub_auth_client.django'
    label = 'hub_auth_client'
    verbose_name = 'Hub Auth Client'
    
    def ready(self):
        """Initialize lazy imports after app is ready."""
        # Import the module to trigger lazy initialization functions
        from . import _init_rls, _init_config, _init_admin_sso
        _init_rls()
        _init_config()
        _init_admin_sso()
