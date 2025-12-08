"""
Migration to add Azure AD configuration models.

This allows storing Azure AD credentials in database instead of environment variables.
"""

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('hub_auth_client', '0002_rls_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='AzureADConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Configuration name (e.g., 'Production', 'Development')", max_length=100, unique=True)),
                ('tenant_id', models.CharField(help_text='Azure AD Tenant ID (GUID)', max_length=100, validators=[django.core.validators.RegexValidator(flags=0, message='Must be a valid GUID format', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')])),
                ('client_id', models.CharField(help_text='Azure AD Application (Client) ID (GUID)', max_length=100, validators=[django.core.validators.RegexValidator(flags=0, message='Must be a valid GUID format', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')])),
                ('client_secret', models.CharField(blank=True, help_text='Azure AD Client Secret (optional, for service-to-service auth)', max_length=255)),
                ('allowed_audiences', models.JSONField(blank=True, default=list, help_text='List of allowed audience values (default: [client_id])')),
                ('token_version', models.CharField(choices=[('1.0', 'v1.0'), ('2.0', 'v2.0')], default='2.0', help_text='Azure AD token version', max_length=10)),
                ('validate_audience', models.BooleanField(default=True, help_text='Whether to validate the token audience (aud claim)')),
                ('validate_issuer', models.BooleanField(default=True, help_text='Whether to validate the token issuer (iss claim)')),
                ('token_leeway', models.IntegerField(default=0, help_text='Number of seconds of leeway for token expiration validation')),
                ('exempt_paths', models.JSONField(blank=True, default=list, help_text="URL patterns to exempt from authentication (e.g., ['/admin/', '/health/'])")),
                ('is_active', models.BooleanField(default=False, help_text='Whether this configuration is active (only one should be active)')),
                ('description', models.TextField(blank=True, help_text='Description of this configuration')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Azure AD Configuration',
                'verbose_name_plural': 'Azure AD Configurations',
                'ordering': ['-is_active', 'name'],
            },
        ),
        migrations.CreateModel(
            name='AzureADConfigurationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('configuration_name', models.CharField(help_text='Name of the configuration (stored for deleted configs)', max_length=100)),
                ('action', models.CharField(choices=[('created', 'Created'), ('updated', 'Updated'), ('activated', 'Activated'), ('deactivated', 'Deactivated'), ('deleted', 'Deleted')], max_length=20)),
                ('tenant_id', models.CharField(max_length=100)),
                ('client_id', models.CharField(max_length=100)),
                ('changed_by', models.CharField(blank=True, help_text='User who made the change', max_length=100)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('details', models.TextField(blank=True, help_text='Additional details about the change')),
                ('configuration', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='history', to='hub_auth_client.azureadconfiguration')),
            ],
            options={
                'verbose_name': 'Configuration History',
                'verbose_name_plural': 'Configuration History',
                'ordering': ['-changed_at'],
            },
        ),
    ]
