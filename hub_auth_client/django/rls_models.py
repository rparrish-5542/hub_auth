"""
Row-Level Security (RLS) models for PostgreSQL integration.

Allows defining RLS policies through Django admin that can be enforced at the database level.
"""

from django.db import models
from django.core.validators import RegexValidator


class RLSPolicy(models.Model):
    """
    Define a Row-Level Security policy for a database table.
    
    This model stores the configuration for PostgreSQL RLS policies
    that can be generated and applied to your database tables.
    """
    
    POLICY_COMMAND_CHOICES = [
        ('ALL', 'ALL - All operations'),
        ('SELECT', 'SELECT - Read operations'),
        ('INSERT', 'INSERT - Create operations'),
        ('UPDATE', 'UPDATE - Modify operations'),
        ('DELETE', 'DELETE - Remove operations'),
    ]
    
    POLICY_TYPE_CHOICES = [
        ('PERMISSIVE', 'PERMISSIVE - Grant access if condition matches'),
        ('RESTRICTIVE', 'RESTRICTIVE - Deny access unless condition matches'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Policy name (e.g., 'employee_department_access')",
        validators=[
            RegexValidator(
                regex=r'^[a-z_][a-z0-9_]*$',
                message='Policy name must be lowercase with underscores, start with letter'
            )
        ]
    )
    
    table_name = models.CharField(
        max_length=100,
        help_text="Database table name (e.g., 'employee_employee')",
        validators=[
            RegexValidator(
                regex=r'^[a-z_][a-z0-9_]*$',
                message='Table name must be lowercase with underscores'
            )
        ]
    )
    
    policy_command = models.CharField(
        max_length=10,
        choices=POLICY_COMMAND_CHOICES,
        default='ALL',
        help_text="Which SQL commands this policy applies to"
    )
    
    policy_type = models.CharField(
        max_length=15,
        choices=POLICY_TYPE_CHOICES,
        default='PERMISSIVE',
        help_text="Whether policy grants or restricts access"
    )
    
    # Scope-based RLS
    required_scopes = models.ManyToManyField(
        'ScopeDefinition',  # String reference to avoid circular import
        blank=True,
        related_name='rls_policies',
        help_text="Scopes required to access rows (checked via session variables)"
    )
    scope_requirement = models.CharField(
        max_length=10,
        choices=[('any', 'Any'), ('all', 'All')],
        default='any',
        help_text="Whether user needs ANY or ALL scopes"
    )
    
    # Role-based RLS
    required_roles = models.ManyToManyField(
        'RoleDefinition',  # String reference to avoid circular import
        blank=True,
        related_name='rls_policies',
        help_text="Roles required to access rows (checked via session variables)"
    )
    role_requirement = models.CharField(
        max_length=10,
        choices=[('any', 'Any'), ('all', 'All')],
        default='any',
        help_text="Whether user needs ANY or ALL roles"
    )
    
    # Custom SQL conditions
    using_expression = models.TextField(
        blank=True,
        help_text=(
            "SQL USING expression for row visibility. "
            "Example: department_id = current_setting('app.user_department')::int "
            "Leave blank to use scope/role-based expression."
        )
    )
    
    with_check_expression = models.TextField(
        blank=True,
        help_text=(
            "SQL WITH CHECK expression for new/modified rows. "
            "Leave blank to use same as USING expression."
        )
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="What this policy controls"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this policy should be applied to the database"
    )
    
    applies_to_roles = models.CharField(
        max_length=200,
        default='PUBLIC',
        help_text="Database roles this policy applies to (comma-separated, default: PUBLIC)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "RLS Policy"
        verbose_name_plural = "RLS Policies"
        ordering = ['table_name', 'name']
        unique_together = [['table_name', 'name']]
    
    def __str__(self):
        return f"{self.name} on {self.table_name}"
    
    def get_using_expression(self):
        """
        Generate the USING expression for this policy.
        
        Returns the custom expression if provided, otherwise generates
        from scope/role requirements.
        """
        if self.using_expression:
            return self.using_expression
        
        conditions = []
        
        # Scope-based condition
        scopes = list(self.required_scopes.filter(is_active=True).values_list('name', flat=True))
        if scopes:
            scope_list = "', '".join(scopes)
            if self.scope_requirement == 'all':
                # User must have ALL scopes
                scope_checks = [
                    f"current_setting('app.user_scopes', true) LIKE '%{scope}%'"
                    for scope in scopes
                ]
                conditions.append(f"({' AND '.join(scope_checks)})")
            else:
                # User must have ANY scope
                conditions.append(
                    f"current_setting('app.user_scopes', true) ~* '({scope_list})'"
                )
        
        # Role-based condition
        roles = list(self.required_roles.filter(is_active=True).values_list('name', flat=True))
        if roles:
            role_list = "', '".join(roles)
            if self.role_requirement == 'all':
                # User must have ALL roles
                role_checks = [
                    f"current_setting('app.user_roles', true) LIKE '%{role}%'"
                    for role in roles
                ]
                conditions.append(f"({' AND '.join(role_checks)})")
            else:
                # User must have ANY role
                conditions.append(
                    f"current_setting('app.user_roles', true) ~* '({role_list})'"
                )
        
        if not conditions:
            # No conditions = allow all (or you could return 'true' or 'false')
            return "true"
        
        return " AND ".join(conditions)
    
    def get_with_check_expression(self):
        """
        Generate the WITH CHECK expression for this policy.
        
        Returns the custom expression if provided, otherwise uses USING expression.
        """
        if self.with_check_expression:
            return self.with_check_expression
        
        return self.get_using_expression()
    
    def generate_create_policy_sql(self):
        """
        Generate the SQL statement to create this RLS policy.
        
        Returns:
            str: SQL CREATE POLICY statement
        """
        using_expr = self.get_using_expression()
        with_check_expr = self.get_with_check_expression()
        
        sql_parts = [
            f"CREATE POLICY {self.name}",
            f"ON {self.table_name}",
            f"AS {self.policy_type}",
            f"FOR {self.policy_command}",
            f"TO {self.applies_to_roles}",
            f"USING ({using_expr})",
        ]
        
        # Only add WITH CHECK if it's different from USING or for INSERT/UPDATE
        if self.policy_command in ['INSERT', 'UPDATE', 'ALL'] and with_check_expr:
            sql_parts.append(f"WITH CHECK ({with_check_expr})")
        
        return "\n".join(sql_parts) + ";"
    
    def generate_drop_policy_sql(self):
        """
        Generate the SQL statement to drop this RLS policy.
        
        Returns:
            str: SQL DROP POLICY statement
        """
        return f"DROP POLICY IF EXISTS {self.name} ON {self.table_name};"
    
    def generate_enable_rls_sql(self):
        """
        Generate the SQL statement to enable RLS on the table.
        
        Returns:
            str: SQL ALTER TABLE statement
        """
        return f"ALTER TABLE {self.table_name} ENABLE ROW LEVEL SECURITY;"


class RLSTableConfig(models.Model):
    """
    Configuration for RLS on a specific table.
    
    Controls whether RLS is enabled and how it behaves.
    """
    
    table_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Database table name",
        validators=[
            RegexValidator(
                regex=r'^[a-z_][a-z0-9_]*$',
                message='Table name must be lowercase with underscores'
            )
        ]
    )
    
    rls_enabled = models.BooleanField(
        default=False,
        help_text="Whether RLS is enabled on this table"
    )
    
    force_rls = models.BooleanField(
        default=False,
        help_text="Whether to apply RLS even to table owner (FORCE ROW LEVEL SECURITY)"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description of what data this table contains"
    )
    
    # Session variable configuration
    use_user_id = models.BooleanField(
        default=True,
        help_text="Set app.user_id session variable from request.user"
    )
    
    use_scopes = models.BooleanField(
        default=True,
        help_text="Set app.user_scopes session variable from token scopes"
    )
    
    use_roles = models.BooleanField(
        default=True,
        help_text="Set app.user_roles session variable from token roles"
    )
    
    custom_session_vars = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Custom session variables to set. "
            "Format: {\"app.department_id\": \"user.department_id\"}"
        )
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "RLS Table Configuration"
        verbose_name_plural = "RLS Table Configurations"
        ordering = ['table_name']
    
    def __str__(self):
        status = "✓ Enabled" if self.rls_enabled else "✗ Disabled"
        return f"{self.table_name} ({status})"
    
    def generate_enable_rls_sql(self):
        """Generate SQL to enable RLS on this table."""
        sql_parts = [f"ALTER TABLE {self.table_name} ENABLE ROW LEVEL SECURITY;"]
        
        if self.force_rls:
            sql_parts.append(f"ALTER TABLE {self.table_name} FORCE ROW LEVEL SECURITY;")
        
        return "\n".join(sql_parts)
    
    def generate_disable_rls_sql(self):
        """Generate SQL to disable RLS on this table."""
        sql_parts = []
        
        if self.force_rls:
            sql_parts.append(f"ALTER TABLE {self.table_name} NO FORCE ROW LEVEL SECURITY;")
        
        sql_parts.append(f"ALTER TABLE {self.table_name} DISABLE ROW LEVEL SECURITY;")
        
        return "\n".join(sql_parts)
