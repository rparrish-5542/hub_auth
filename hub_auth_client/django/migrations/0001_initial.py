"""
Initial migration for hub_auth_client dynamic permissions.

To use this in your Django project:
1. Copy this file to your project's migrations folder
2. Run: python manage.py migrate
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScopeDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Scope name (e.g., 'User.Read', 'Employee.Write')", max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='What this scope allows')),
                ('category', models.CharField(blank=True, help_text="Category for grouping (e.g., 'User', 'Employee', 'Files')", max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this scope is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Scope Definition',
                'verbose_name_plural': 'Scope Definitions',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='RoleDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Role name (e.g., 'Admin', 'Manager', 'User')", max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='What this role represents')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this role is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Role Definition',
                'verbose_name_plural': 'Role Definitions',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EndpointPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Descriptive name for this endpoint', max_length=200, unique=True)),
                ('url_pattern', models.CharField(help_text="URL pattern (regex) - e.g., '^/api/employees/$', '/api/employees/.*'", max_length=500)),
                ('http_methods', models.CharField(default='GET,POST,PUT,PATCH,DELETE', help_text="Comma-separated HTTP methods (e.g., 'GET,POST'). Use '*' for all.", max_length=100)),
                ('scope_requirement', models.CharField(choices=[('any', 'Any (at least one)'), ('all', 'All (must have all)')], default='any', help_text='Whether user needs ANY or ALL of the required scopes', max_length=10)),
                ('role_requirement', models.CharField(choices=[('any', 'Any (at least one)'), ('all', 'All (must have all)')], default='any', help_text='Whether user needs ANY or ALL of the required roles', max_length=10)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this permission check is active')),
                ('priority', models.IntegerField(default=0, help_text='Priority for matching (higher = checked first)')),
                ('description', models.TextField(blank=True, help_text='Description of what this endpoint does')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('required_roles', models.ManyToManyField(blank=True, help_text='Roles required for this endpoint', related_name='endpoints', to='hub_auth_client.RoleDefinition')),
                ('required_scopes', models.ManyToManyField(blank=True, help_text='Scopes required for this endpoint', related_name='endpoints', to='hub_auth_client.ScopeDefinition')),
            ],
            options={
                'verbose_name': 'Endpoint Permission',
                'verbose_name_plural': 'Endpoint Permissions',
                'ordering': ['-priority', 'url_pattern'],
                'indexes': [
                    models.Index(fields=['url_pattern', 'is_active'], name='hub_auth_cl_url_pat_idx'),
                    models.Index(fields=['-priority'], name='hub_auth_cl_priorit_idx'),
                ],
            },
        ),
    ]
