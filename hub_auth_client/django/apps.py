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
        self._heal_migration_history()
        from . import _init_admin_sso, _init_config, _init_rls
        _init_rls()
        _init_config()
        _init_admin_sso()

    def _heal_migration_history(self):
        # 0004_apiendpointmapping has no SQL operations (managed=False model)
        # but some environments have 0006_merge applied without 0004 recorded,
        # causing check_consistent_history to abort before --fake can help.
        # This insert is a no-op when the row already exists.
        from django.db import OperationalError, ProgrammingError, connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) "
                    "SELECT 'hub_auth_client', '0004_apiendpointmapping', NOW() "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM django_migrations "
                    "  WHERE app = 'hub_auth_client' AND name = '0004_apiendpointmapping'"
                    ")"
                )
        except (OperationalError, ProgrammingError):
            pass  # Table doesn't exist yet on a fresh install
