"""
Migration to remove allowed_audiences field from AzureADConfiguration.

The MSALTokenValidator now uses client_id as the audience automatically,
so this field is no longer needed.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hub_auth_client', '0004_rename_hub_auth_cl_url_pat_idx_hub_auth_cl_url_pat_6a85ac_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='azureadconfiguration',
            name='allowed_audiences',
        ),
    ]
