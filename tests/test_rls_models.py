"""
Tests for hub_auth_client.django.rls_models module.

Tests the RLS policy models for PostgreSQL integration.
"""

import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestRLSPolicy:
    """Test the RLSPolicy model."""
    
    def test_create_rls_policy(self):
        """Test creating an RLS policy."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy.objects.create(
            name='test_policy',
            table_name='test_table',
            policy_command='SELECT',
            policy_type='PERMISSIVE',
            description='Test policy'
        )
        
        assert policy.name == 'test_policy'
        assert policy.table_name == 'test_table'
        assert policy.policy_command == 'SELECT'
        assert policy.is_active is True
    
    def test_str_representation(self):
        """Test string representation of RLS policy."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='employee_access',
            table_name='employee_employee'
        )
        
        assert str(policy) == 'employee_access on employee_employee'
    
    def test_policy_name_validation(self):
        """Test policy name validation (lowercase, underscores)."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        # Valid names
        valid_policy = RLSPolicy(
            name='valid_policy_name',
            table_name='test_table'
        )
        valid_policy.full_clean()  # Should not raise
        
        # Invalid names should raise validation error
        invalid_policy = RLSPolicy(
            name='Invalid-Name',  # Hyphens not allowed
            table_name='test_table'
        )
        
        with pytest.raises(ValidationError):
            invalid_policy.full_clean()
    
    def test_get_using_expression_with_custom_expression(self):
        """Test get_using_expression returns custom expression when provided."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='custom_policy',
            table_name='test_table',
            using_expression="department_id = current_setting('app.user_department')::int"
        )
        
        result = policy.get_using_expression()
        
        assert result == "department_id = current_setting('app.user_department')::int"
    
    def test_get_using_expression_no_conditions_returns_true(self):
        """Test get_using_expression returns 'true' when no scopes/roles."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy.objects.create(
            name='open_policy',
            table_name='test_table'
        )
        
        result = policy.get_using_expression()
        
        assert result == 'true'
    
    def test_get_with_check_expression_with_custom(self):
        """Test get_with_check_expression returns custom when provided."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='check_policy',
            table_name='test_table',
            with_check_expression="status = 'active'"
        )
        
        result = policy.get_with_check_expression()
        
        assert result == "status = 'active'"
    
    def test_get_with_check_expression_defaults_to_using(self):
        """Test get_with_check_expression defaults to using expression."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='default_policy',
            table_name='test_table',
            using_expression="user_id = current_setting('app.user_id')"
        )
        
        result = policy.get_with_check_expression()
        
        assert result == "user_id = current_setting('app.user_id')"
    
    def test_generate_create_policy_sql_basic(self):
        """Test generating CREATE POLICY SQL."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='test_policy',
            table_name='test_table',
            policy_command='SELECT',
            policy_type='PERMISSIVE',
            using_expression='true'
        )
        
        sql = policy.generate_create_policy_sql()
        
        assert 'CREATE POLICY test_policy' in sql
        assert 'ON test_table' in sql
        assert 'AS PERMISSIVE' in sql
        assert 'FOR SELECT' in sql
        assert 'TO PUBLIC' in sql
        assert 'USING (true)' in sql
    
    def test_generate_create_policy_sql_with_check(self):
        """Test generating CREATE POLICY SQL with WITH CHECK."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='insert_policy',
            table_name='test_table',
            policy_command='INSERT',
            policy_type='PERMISSIVE',
            using_expression='true',
            with_check_expression="status = 'active'"
        )
        
        sql = policy.generate_create_policy_sql()
        
        assert 'USING (true)' in sql
        assert "WITH CHECK (status = 'active')" in sql
    
    def test_generate_drop_policy_sql(self):
        """Test generating DROP POLICY SQL."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='test_policy',
            table_name='test_table'
        )
        
        sql = policy.generate_drop_policy_sql()
        
        assert sql == 'DROP POLICY IF EXISTS test_policy ON test_table;'
    
    def test_generate_enable_rls_sql(self):
        """Test generating ENABLE RLS SQL."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        policy = RLSPolicy(
            name='test_policy',
            table_name='test_table'
        )
        
        sql = policy.generate_enable_rls_sql()
        
        assert sql == 'ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;'
    
    def test_policy_command_choices(self):
        """Test that policy_command has correct choices."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        commands = ['ALL', 'SELECT', 'INSERT', 'UPDATE', 'DELETE']
        
        for cmd in commands:
            policy = RLSPolicy(
                name=f'policy_{cmd.lower()}',
                table_name='test_table',
                policy_command=cmd
            )
            assert policy.policy_command == cmd
    
    def test_policy_type_choices(self):
        """Test that policy_type has correct choices."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        for policy_type in ['PERMISSIVE', 'RESTRICTIVE']:
            policy = RLSPolicy(
                name=f'policy_{policy_type.lower()}',
                table_name='test_table',
                policy_type=policy_type
            )
            assert policy.policy_type == policy_type
    
    def test_scope_requirement_choices(self):
        """Test that scope_requirement has correct choices."""
        from hub_auth_client.django.rls_models import RLSPolicy
        
        for req in ['any', 'all']:
            policy = RLSPolicy(
                name=f'policy_{req}',
                table_name='test_table',
                scope_requirement=req
            )
            assert policy.scope_requirement == req
    
    def test_unique_together_constraint(self):
        """Test that table_name + name must be unique."""
        from hub_auth_client.django.rls_models import RLSPolicy
        from django.db import IntegrityError
        
        # Create first policy
        RLSPolicy.objects.create(
            name='duplicate_test',
            table_name='test_table'
        )
        
        # Try to create duplicate
        with pytest.raises(IntegrityError):
            RLSPolicy.objects.create(
                name='duplicate_test',
                table_name='test_table'
            )


@pytest.mark.django_db
class TestRLSTableConfig:
    """Test the RLSTableConfig model."""
    
    def test_create_rls_table_config(self):
        """Test creating an RLS table configuration."""
        from hub_auth_client.django.rls_models import RLSTableConfig
        
        config = RLSTableConfig.objects.create(
            table_name='employee_employee',
            rls_enabled=True,
            force_rls=False,
            description='Employee table RLS'
        )
        
        assert config.table_name == 'employee_employee'
        assert config.rls_enabled is True
        assert config.force_rls is False
    
    def test_str_representation(self):
        """Test string representation of RLS table config."""
        from hub_auth_client.django.rls_models import RLSTableConfig
        
        config = RLSTableConfig(
            table_name='employee_employee'
        )
        
        # String representation includes RLS status
        assert 'employee_employee' in str(config)
    
    def test_table_name_validation(self):
        """Test table name validation."""
        from hub_auth_client.django.rls_models import RLSTableConfig
        
        # Valid name
        valid_config = RLSTableConfig(
            table_name='valid_table_name'
        )
        valid_config.full_clean()
        
        # Invalid name
        invalid_config = RLSTableConfig(
            table_name='Invalid-Table'
        )
        
        with pytest.raises(ValidationError):
            invalid_config.full_clean()
    
    def test_generate_enable_rls_sql(self):
        """Test generating ENABLE RLS SQL."""
        from hub_auth_client.django.rls_models import RLSTableConfig
        
        config = RLSTableConfig(
            table_name='test_table',
            rls_enabled=True
        )
        
        sql = config.generate_enable_rls_sql()
        
        assert sql == 'ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;'
    
    def test_generate_disable_rls_sql(self):
        """Test generating DISABLE RLS SQL."""
        from hub_auth_client.django.rls_models import RLSTableConfig
        
        config = RLSTableConfig(
            table_name='test_table',
            rls_enabled=False
        )
        
        sql = config.generate_disable_rls_sql()
        
        assert sql == 'ALTER TABLE test_table DISABLE ROW LEVEL SECURITY;'
