# Generated migration for RLS models

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hub_auth_client', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RLSPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text="Policy name (e.g., 'employee_department_access')",
                    max_length=100,
                    unique=True,
                    validators=[django.core.validators.RegexValidator(
                        message='Policy name must be lowercase with underscores, start with letter',
                        regex='^[a-z_][a-z0-9_]*$'
                    )]
                )),
                ('table_name', models.CharField(
                    help_text="Database table name (e.g., 'employee_employee')",
                    max_length=100,
                    validators=[django.core.validators.RegexValidator(
                        message='Table name must be lowercase with underscores',
                        regex='^[a-z_][a-z0-9_]*$'
                    )]
                )),
                ('policy_command', models.CharField(
                    choices=[
                        ('ALL', 'ALL - All operations'),
                        ('SELECT', 'SELECT - Read operations'),
                        ('INSERT', 'INSERT - Create operations'),
                        ('UPDATE', 'UPDATE - Modify operations'),
                        ('DELETE', 'DELETE - Remove operations')
                    ],
                    default='ALL',
                    help_text='Which SQL commands this policy applies to',
                    max_length=10
                )),
                ('policy_type', models.CharField(
                    choices=[
                        ('PERMISSIVE', 'PERMISSIVE - Grant access if condition matches'),
                        ('RESTRICTIVE', 'RESTRICTIVE - Deny access unless condition matches')
                    ],
                    default='PERMISSIVE',
                    help_text='Whether policy grants or restricts access',
                    max_length=15
                )),
                ('scope_requirement', models.CharField(
                    choices=[('any', 'Any'), ('all', 'All')],
                    default='any',
                    help_text='Whether user needs ANY or ALL scopes',
                    max_length=10
                )),
                ('role_requirement', models.CharField(
                    choices=[('any', 'Any'), ('all', 'All')],
                    default='any',
                    help_text='Whether user needs ANY or ALL roles',
                    max_length=10
                )),
                ('using_expression', models.TextField(
                    blank=True,
                    help_text='SQL USING expression for row visibility. Leave blank to use scope/role-based expression.'
                )),
                ('with_check_expression', models.TextField(
                    blank=True,
                    help_text='SQL WITH CHECK expression for new/modified rows. Leave blank to use same as USING expression.'
                )),
                ('description', models.TextField(blank=True, help_text='What this policy controls')),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this policy should be applied to the database'
                )),
                ('applies_to_roles', models.CharField(
                    default='PUBLIC',
                    help_text='Database roles this policy applies to (comma-separated, default: PUBLIC)',
                    max_length=200
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('required_scopes', models.ManyToManyField(
                    blank=True,
                    help_text='Scopes required to access rows (checked via session variables)',
                    related_name='rls_policies',
                    to='hub_auth_client.scopedefinition'
                )),
                ('required_roles', models.ManyToManyField(
                    blank=True,
                    help_text='Roles required to access rows (checked via session variables)',
                    related_name='rls_policies',
                    to='hub_auth_client.roledefinition'
                )),
            ],
            options={
                'verbose_name': 'RLS Policy',
                'verbose_name_plural': 'RLS Policies',
                'ordering': ['table_name', 'name'],
                'unique_together': {('table_name', 'name')},
            },
        ),
        migrations.CreateModel(
            name='RLSTableConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table_name', models.CharField(
                    help_text='Database table name',
                    max_length=100,
                    unique=True,
                    validators=[django.core.validators.RegexValidator(
                        message='Table name must be lowercase with underscores',
                        regex='^[a-z_][a-z0-9_]*$'
                    )]
                )),
                ('rls_enabled', models.BooleanField(
                    default=False,
                    help_text='Whether RLS is enabled on this table'
                )),
                ('force_rls', models.BooleanField(
                    default=False,
                    help_text='Whether to apply RLS even to table owner (FORCE ROW LEVEL SECURITY)'
                )),
                ('description', models.TextField(blank=True, help_text='Description of what data this table contains')),
                ('use_user_id', models.BooleanField(
                    default=True,
                    help_text='Set app.user_id session variable from request.user'
                )),
                ('use_scopes', models.BooleanField(
                    default=True,
                    help_text='Set app.user_scopes session variable from token scopes'
                )),
                ('use_roles', models.BooleanField(
                    default=True,
                    help_text='Set app.user_roles session variable from token roles'
                )),
                ('custom_session_vars', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Custom session variables to set. Format: {"app.department_id": "user.department_id"}'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'RLS Table Configuration',
                'verbose_name_plural': 'RLS Table Configurations',
                'ordering': ['table_name'],
            },
        ),
    ]
