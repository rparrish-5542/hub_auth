"""
Example Django views using RLS (Row-Level Security).

Shows how RLS works transparently with Django ORM queries.
"""

from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from hub_auth_client.django import DynamicPermission, DynamicScopePermission


# Example models (you would define these in your models.py)
# from employee.models import Employee, Department


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee CRUD with RLS.
    
    RLS automatically filters queries based on the user's scopes/roles.
    No additional query filtering needed!
    
    Example RLS Policy in admin:
    - Name: employee_read_access
    - Table: employee_employee
    - Command: SELECT
    - Required Scopes: Employee.Read
    
    This means users without Employee.Read scope see 0 employees,
    even if they call this API.
    """
    
    # queryset is automatically filtered by RLS
    # queryset = Employee.objects.all()
    
    # serializer_class = EmployeeSerializer
    
    # Use dynamic permissions to check scopes at API level too
    permission_classes = [DynamicScopePermission]
    
    def get_queryset(self):
        """
        No filtering needed! RLS handles it.
        
        PostgreSQL applies RLS policies before returning rows.
        """
        # return Employee.objects.all()
        
        # Optional: You can still add application-level filters
        # queryset = Employee.objects.all()
        # 
        # if not self.request.user.has_scope('Employee.ReadAll'):
        #     # Non-admin users might have additional restrictions
        #     queryset = queryset.filter(department=self.request.user.department)
        # 
        # return queryset
        pass
    
    @action(detail=False, methods=['get'])
    def my_department(self, request):
        """
        Get employees in my department.
        
        With RLS configured for department-based access, this
        automatically returns only employees in the user's department.
        """
        # With RLS policy:
        # USING (department_id = current_setting('app.user_department_id')::int)
        
        # employees = Employee.objects.all()  # RLS filters this!
        
        # return Response({
        #     'employees': EmployeeSerializer(employees, many=True).data
        # })
        pass


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Department CRUD with role-based RLS.
    
    Example RLS Policy:
    - Name: department_manager_access
    - Table: employee_department
    - Command: ALL
    - Required Roles: Manager, Admin
    - Role Requirement: any
    
    Only users with Manager or Admin role can see/modify departments.
    """
    
    # queryset = Department.objects.all()  # RLS filters by role
    # serializer_class = DepartmentSerializer
    permission_classes = [DynamicPermission]


class SalaryView(views.APIView):
    """
    Salary data with restrictive RLS.
    
    Example RLS Policies:
    1. PERMISSIVE policy: Allow if user has Employee.Read scope
    2. RESTRICTIVE policy: Deny if salary > 0 unless user has HR role
    
    Result: Regular users see employee records but salary field is NULL.
    HR users see actual salaries.
    """
    
    permission_classes = [DynamicScopePermission]
    
    def get(self, request, employee_id=None):
        """Get salary information."""
        
        # With RESTRICTIVE RLS policy on salary column:
        # USING (
        #   salary IS NULL 
        #   OR current_setting('app.user_roles', true) ~* 'HR'
        # )
        
        # employee = Employee.objects.get(id=employee_id)
        
        # Regular users: employee.salary = None
        # HR users: employee.salary = actual value
        
        # return Response({
        #     'id': employee.id,
        #     'name': employee.name,
        #     'salary': employee.salary,  # RLS filters this
        # })
        pass


class MultiTenantDataView(views.APIView):
    """
    Multi-tenant data access with RLS tenant isolation.
    
    Example RLS Policy:
    - Name: tenant_isolation
    - Table: app_data
    - Command: ALL
    - Custom SQL: tenant_id = current_setting('app.tenant_id')::uuid
    
    Users can only access data for their Azure AD tenant.
    """
    
    permission_classes = [DynamicPermission]
    
    def get(self, request):
        """List data for current tenant."""
        
        # With RLS policy:
        # USING (tenant_id = current_setting('app.tenant_id')::uuid)
        
        # All queries are automatically scoped to user's tenant
        # data = AppData.objects.all()  # Only returns current tenant's data
        
        # return Response({
        #     'tenant_id': request.user.tid,
        #     'data': DataSerializer(data, many=True).data
        # })
        pass


class CombinedPolicyView(views.APIView):
    """
    View with multiple RLS policies.
    
    Example: Employee data with:
    1. Scope requirement: Must have Employee.Read
    2. Department restriction: Can only see own department
    3. Salary restriction: Need HR role for salary
    
    Multiple PERMISSIVE policies are OR'd.
    Multiple RESTRICTIVE policies are AND'd.
    """
    
    permission_classes = [DynamicScopePermission]
    
    def get(self, request):
        """
        Get employees with multiple RLS policies active.
        
        RLS Policies applied:
        1. employee_scope_check (PERMISSIVE, SELECT)
           - USING: app.user_scopes ~* 'Employee.Read'
        
        2. employee_department_filter (PERMISSIVE, SELECT)
           - USING: department_id = app.user_department_id::int
        
        3. employee_salary_restrict (RESTRICTIVE, SELECT)
           - USING: salary IS NULL OR app.user_roles ~* 'HR'
        
        Result: User sees employees in their department (with Employee.Read scope),
        but salary is NULL unless they have HR role.
        """
        
        # employees = Employee.objects.all()
        
        # Django ORM query:
        # SELECT * FROM employee_employee;
        
        # PostgreSQL executes:
        # SELECT * FROM employee_employee
        # WHERE (
        #   -- PERMISSIVE policies (OR'd)
        #   (current_setting('app.user_scopes') ~* 'Employee.Read')
        #   OR
        #   (department_id = current_setting('app.user_department_id')::int)
        # )
        # AND (
        #   -- RESTRICTIVE policies (AND'd)
        #   (salary IS NULL OR current_setting('app.user_roles') ~* 'HR')
        # );
        
        # return Response({
        #     'employees': EmployeeSerializer(employees, many=True).data
        # })
        pass


# ============================================================================
# Admin Actions
# ============================================================================

class RLSManagementView(views.APIView):
    """
    API view for managing RLS policies (admin only).
    
    This would typically be restricted to superusers.
    """
    
    # permission_classes = [IsSuperUser]  # Custom permission
    
    def get(self, request):
        """List all RLS policies and their status."""
        from hub_auth_client.django import RLSPolicy, RLSTableConfig
        
        policies = RLSPolicy.objects.all()
        tables = RLSTableConfig.objects.all()
        
        return Response({
            'policies': [
                {
                    'name': p.name,
                    'table': p.table_name,
                    'command': p.policy_command,
                    'active': p.is_active,
                    'scopes': list(p.required_scopes.values_list('name', flat=True)),
                    'roles': list(p.required_roles.values_list('name', flat=True)),
                }
                for p in policies
            ],
            'tables': [
                {
                    'name': t.table_name,
                    'rls_enabled': t.rls_enabled,
                    'force_rls': t.force_rls,
                    'policy_count': RLSPolicy.objects.filter(
                        table_name=t.table_name,
                        is_active=True
                    ).count()
                }
                for t in tables
            ]
        })
    
    def post(self, request):
        """Apply RLS policies to database."""
        from hub_auth_client.django import RLSPolicy
        from django.db import connection
        
        policy_name = request.data.get('policy_name')
        
        try:
            policy = RLSPolicy.objects.get(name=policy_name, is_active=True)
            
            with connection.cursor() as cursor:
                # Drop existing
                cursor.execute(policy.generate_drop_policy_sql())
                
                # Enable RLS
                cursor.execute(policy.generate_enable_rls_sql())
                
                # Create policy
                cursor.execute(policy.generate_create_policy_sql())
            
            return Response({
                'success': True,
                'message': f'Applied policy {policy_name}',
                'sql': policy.generate_create_policy_sql()
            })
        
        except RLSPolicy.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Policy {policy_name} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Testing RLS
# ============================================================================

class RLSTestView(views.APIView):
    """
    View for testing RLS functionality.
    
    Shows current user's session variables and what they can access.
    """
    
    def get(self, request):
        """Test RLS by showing what the current user can see."""
        from django.db import connection
        
        # Get current session variables
        session_vars = {}
        var_names = [
            'app.user_id',
            'app.user_email',
            'app.user_scopes',
            'app.user_roles',
            'app.tenant_id',
        ]
        
        with connection.cursor() as cursor:
            for var_name in var_names:
                try:
                    cursor.execute(f"SELECT current_setting('{var_name}', true);")
                    result = cursor.fetchone()
                    session_vars[var_name] = result[0] if result and result[0] else None
                except Exception:
                    session_vars[var_name] = None
        
        # Get what user can access
        # employee_count = Employee.objects.count()
        # department_count = Department.objects.count()
        
        return Response({
            'user': {
                'oid': request.user.oid if hasattr(request.user, 'oid') else None,
                'email': request.user.email if hasattr(request.user, 'email') else None,
                'scopes': request.user.scopes if hasattr(request.user, 'scopes') else [],
                'roles': request.user.roles if hasattr(request.user, 'roles') else [],
            },
            'session_variables': session_vars,
            'access': {
                # 'employees': employee_count,
                # 'departments': department_count,
            },
            'note': 'Counts reflect RLS-filtered results'
        })


# ============================================================================
# Usage Notes
# ============================================================================

"""
To use these views:

1. Configure RLS in Django admin:
   - Go to RLS Table Configurations
   - Enable RLS for your tables
   - Define RLS Policies with scope/role requirements

2. Apply policies:
   python manage.py manage_rls --apply-all

3. Test with different users:
   - Users with different scopes see different data
   - No application code changes needed
   - All filtering happens at database level

4. Monitor performance:
   - Add indexes on columns used in RLS policies
   - Check PostgreSQL query plans
   - Use EXPLAIN ANALYZE to verify RLS is working

5. Debug:
   - Enable RLSDebugMiddleware
   - Check logs for session variables
   - Query pg_policies to see active policies
"""
