"""
Migration to safely remove allowed_audiences field from AzureADConfiguration.
"""

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('hub_auth_client', '0004_rename_hub_auth_cl_url_pat_idx_hub_auth_cl_url_pat_6a85ac_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE hub_auth_client_azureadconfiguration
                DROP COLUMN IF EXISTS allowed_audiences CASCADE;
            """,
            reverse_sql="""
                ALTER TABLE hub_auth_client_azureadconfiguration
                ADD COLUMN allowed_audiences JSONB DEFAULT '[]';
            """
        ),
    ]
