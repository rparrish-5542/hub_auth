"""
RLS (Row-Level Security) middleware for setting PostgreSQL session variables.

This middleware extracts user information from the MSAL token and sets
PostgreSQL session variables that can be used in RLS policies.
"""

from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class RLSMiddleware(MiddlewareMixin):
    """
    Middleware to set PostgreSQL session variables for RLS policies.
    
    This extracts information from the authenticated user (MSALUser)
    and sets session variables that RLS policies can reference.
    
    Usage in settings.py:
        MIDDLEWARE = [
            ...
            'hub_auth_client.django.rls_middleware.RLSMiddleware',
            ...
        ]
    
    Session variables set:
        - app.user_id: User's unique identifier (oid or email)
        - app.user_email: User's email address
        - app.user_scopes: Comma-separated list of scopes
        - app.user_roles: Comma-separated list of roles
        - app.tenant_id: Azure AD tenant ID
        - Custom variables from RLSTableConfig.custom_session_vars
    """
    
    def process_request(self, request):
        """
        Set PostgreSQL session variables based on the authenticated user.
        
        This is called for every request after authentication middleware.
        """
        # Only process if user is authenticated and we're using PostgreSQL
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return None
        
        # Check if we're using PostgreSQL
        db_engine = connection.settings_dict.get('ENGINE', '')
        if 'postgresql' not in db_engine and 'postgis' not in db_engine:
            return None
        
        # Get the MSALUser from request
        user = request.user
        
        # Prepare session variables
        session_vars = {}
        
        # Standard variables
        if hasattr(user, 'oid'):
            session_vars['app.user_id'] = user.oid
        elif hasattr(user, 'email'):
            session_vars['app.user_id'] = user.email
        
        if hasattr(user, 'email'):
            session_vars['app.user_email'] = user.email
        
        if hasattr(user, 'name'):
            session_vars['app.user_name'] = user.name
        
        # Scopes
        if hasattr(user, 'scopes') and user.scopes:
            session_vars['app.user_scopes'] = ','.join(user.scopes)
        else:
            session_vars['app.user_scopes'] = ''
        
        # Roles
        if hasattr(user, 'roles') and user.roles:
            session_vars['app.user_roles'] = ','.join(user.roles)
        else:
            session_vars['app.user_roles'] = ''
        
        # Tenant ID
        if hasattr(user, 'tid'):
            session_vars['app.tenant_id'] = user.tid
        
        # Check for table-specific custom session variables
        try:
            from .rls_models import RLSTableConfig
            
            configs = RLSTableConfig.objects.filter(
                rls_enabled=True
            ).values_list('custom_session_vars', flat=True)
            
            for config_vars in configs:
                if config_vars:
                    for var_name, user_attr in config_vars.items():
                        # Support nested attributes like "user.department.id"
                        value = self._get_nested_attr(user, user_attr)
                        if value is not None:
                            session_vars[var_name] = str(value)
        
        except Exception:
            # RLS models might not be installed or DB not ready
            pass
        
        # Set the session variables in PostgreSQL
        if session_vars:
            self._set_session_variables(session_vars)
        
        return None
    
    def _get_nested_attr(self, obj, attr_path):
        """
        Get a nested attribute from an object.
        
        Example: _get_nested_attr(user, "department.id") 
                 -> user.department.id
        """
        parts = attr_path.split('.')
        current = obj
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current
    
    def _set_session_variables(self, variables):
        """
        Set PostgreSQL session variables using SET LOCAL.
        
        Args:
            variables: Dict of variable_name -> value
        """
        try:
            with connection.cursor() as cursor:
                for var_name, value in variables.items():
                    # Escape single quotes in value
                    escaped_value = str(value).replace("'", "''")
                    
                    # Use SET LOCAL so it only applies to current transaction
                    sql = f"SET LOCAL {var_name} = '{escaped_value}';"
                    cursor.execute(sql)
        
        except Exception as e:
            # Log the error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to set RLS session variables: {e}")
    
    def process_response(self, request, response):
        """
        Clear session variables after response (optional).
        
        PostgreSQL SET LOCAL automatically clears at transaction end,
        so this is mostly for cleanup/safety.
        """
        return response


class RLSDebugMiddleware(MiddlewareMixin):
    """
    Debug middleware to log RLS session variables.
    
    Usage in settings.py (only in development):
        MIDDLEWARE = [
            ...
            'hub_auth_client.django.rls_middleware.RLSDebugMiddleware',
            ...
        ]
    """
    
    def process_request(self, request):
        """Log current RLS session variables."""
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return None
        
        # Check if PostgreSQL
        db_engine = connection.settings_dict.get('ENGINE', '')
        if 'postgresql' not in db_engine and 'postgis' not in db_engine:
            return None
        
        try:
            import logging
            logger = logging.getLogger('hub_auth.rls')
            
            with connection.cursor() as cursor:
                # Query current session variables
                vars_to_check = [
                    'app.user_id',
                    'app.user_email',
                    'app.user_scopes',
                    'app.user_roles',
                    'app.tenant_id',
                ]
                
                logger.debug(f"RLS Session Variables for {request.path}:")
                
                for var_name in vars_to_check:
                    try:
                        cursor.execute(f"SELECT current_setting('{var_name}', true);")
                        result = cursor.fetchone()
                        value = result[0] if result and result[0] else '<not set>'
                        logger.debug(f"  {var_name}: {value}")
                    except Exception:
                        logger.debug(f"  {var_name}: <not set>")
        
        except Exception as e:
            pass
        
        return None
