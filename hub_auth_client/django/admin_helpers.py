"""
Helper functions and utilities for Django admin customization.
"""

import re
from django.utils.html import format_html
from django.db import connection


def format_active_badge(is_active):
    """
    Format active/inactive status as colored badge.
    
    Args:
        is_active (bool): Whether the item is active
        
    Returns:
        SafeString: HTML formatted badge
    """
    if is_active:
        return format_html('<span style="color: green;">✓ Active</span>')
    return format_html('<span style="color: red;">✗ Inactive</span>')


def humanize_url_pattern(pattern):
    """
    Convert a regex URL pattern to a human-readable description.
    
    Args:
        pattern (str): The regex URL pattern
        
    Returns:
        str: Human-readable description
        
    Examples:
        '^api/employees/$' -> '/api/employees/ (exact match)'
        'admin/(?P<url>.*)$' -> '/admin/{url} (any path)'
        '^api/employees/(?P<pk>[^/.]+)/$' -> '/api/employees/{pk}/'
        '^api/employees\.(?P<format>[a-z0-9]+)/?$' -> '/api/employees.{format} (optional trailing slash)'
    """
    if not pattern:
        return ''
    
    # Make a copy to modify
    readable = pattern
    
    # Remove common regex anchors
    readable = readable.replace('^', '')
    readable = readable.replace('$', '')
    
    # Track what we removed for description
    descriptions = []
    
    # Handle named groups like (?P<name>pattern)
    named_groups = re.findall(r'\(\?P<(\w+)>([^)]+)\)', readable)
    for name, regex_pattern in named_groups:
        # Simplify common patterns
        if regex_pattern == '[^/.]+':
            replacement = f'{{{name}}}'
        elif regex_pattern == '[a-z0-9]+':
            replacement = f'{{{name}}}'
        elif regex_pattern == '.*':
            replacement = f'{{{name}}}'
        elif regex_pattern == r'\d+':
            replacement = f'{{{name}:number}}'
        else:
            replacement = f'{{{name}}}'
        
        readable = re.sub(r'\(\?P<' + name + r'>[^)]+\)', replacement, readable)
    
    # Handle optional trailing slash
    if readable.endswith('/?'):
        readable = readable[:-2]
        descriptions.append('optional trailing slash')
    
    # Handle wildcard patterns
    if '.*' in readable:
        readable = readable.replace('.*', '*')
        if 'any path' not in descriptions:
            descriptions.append('any path')
    
    # Clean up escaping
    readable = readable.replace(r'\.', '.')
    readable = readable.replace(r'\-', '-')
    
    # Add leading slash if not present
    if not readable.startswith('/'):
        readable = '/' + readable
    
    # Build final description
    if descriptions:
        return f"{readable} ({', '.join(descriptions)})"
    
    return readable


def format_masked_guid(value, visible_chars=12):
    """
    Format a GUID with masked characters, showing only the last portion.
    
    Args:
        value (str): The GUID to mask
        visible_chars (int): Number of characters to show at the end
        
    Returns:
        SafeString: HTML formatted masked GUID
    """
    if not value:
        return '-'
    
    return format_html(
        '<span class="masked-field">••••••••-••••-••••-••••-{}</span>',
        value[-visible_chars:]
    )


def format_sensitive_field_with_reveal(value, field_id, obj_pk, visible_chars=12):
    """
    Format a sensitive field with a reveal button.
    
    Args:
        value (str): The sensitive value to mask
        field_id (str): The field identifier (e.g., 'tenant_id', 'client_id')
        obj_pk: The primary key of the object
        visible_chars (int): Number of characters to show
        
    Returns:
        SafeString: HTML formatted field with reveal button
    """
    if not value or not obj_pk:
        return format_html('<span style="color: #999;">Will be set after saving</span>')
    
    # For GUIDs, show last portion
    if '-' in value and len(value) == 36:
        masked_value = f'••••••••-••••-••••-••••-{value[-visible_chars:]}'
    else:
        # For other values (like secrets), show dots
        masked_length = min(len(value), 40)
        masked_value = '•' * masked_length
    
    return format_html(
        '<div class="sensitive-field-wrapper">' 
        '<span class="sensitive-field masked" data-value="{}" id="{}_{}">' 
        '{}</span>' 
        '<button type="button" class="reveal-btn" data-field-id="{}_{}" '
        'title="Click to reveal">' 
        '<span class="eye-icon">👁</span>' 
        '</button>' 
        '</div>',
        value,
        field_id,
        obj_pk,
        masked_value,
        field_id,
        obj_pk
    )


def format_count_with_requirement(count, requirement=''):
    """
    Format a count with requirement type (e.g., "3 (ANY)").
    
    Args:
        count (int): The count value
        requirement (str): The requirement type (e.g., 'any', 'all')
        
    Returns:
        SafeString or str: Formatted count or '-' if zero
    """
    if count > 0:
        req_text = f' ({requirement.upper()})' if requirement else ''
        return format_html(f'<span>{count}{req_text}</span>')
    return '-'


def format_badge(text, color='#28a745'):
    """
    Format text as a colored badge.
    
    Args:
        text (str): The badge text
        color (str): Background color (hex)
        
    Returns:
        SafeString: HTML formatted badge
    """
    return format_html(
        '<span style="background-color: {}; color: white; padding: 2px 8px; '
        'border-radius: 3px; font-size: 11px;">{}</span>',
        color,
        text
    )


def format_validation_badges(validate_audience=False, validate_issuer=False, token_leeway=0):
    """
    Format validation settings as badges.
    
    Args:
        validate_audience (bool): Whether audience validation is enabled
        validate_issuer (bool): Whether issuer validation is enabled
        token_leeway (int): Token leeway in seconds
        
    Returns:
        SafeString: HTML formatted badges
    """
    badges = []
    if validate_audience:
        badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">AUD</span>')
    if validate_issuer:
        badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ISS</span>')
    if token_leeway > 0:
        badges.append(f'<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Leeway: {token_leeway}s</span>')
    
    return format_html(' '.join(badges)) if badges else '-'


def format_action_badge(action):
    """
    Format action type as colored badge.
    
    Args:
        action (str): The action type (e.g., 'created', 'updated', 'deleted')
        
    Returns:
        SafeString: HTML formatted badge
    """
    colors = {
        'created': '#28a745',
        'updated': '#17a2b8',
        'activated': '#28a745',
        'deactivated': '#6c757d',
        'deleted': '#dc3545',
    }
    color = colors.get(action, '#6c757d')
    return format_html(
        '<span style="background-color: {}; color: white; padding: 2px 8px; '
        'border-radius: 3px; font-size: 11px;">{}</span>',
        color,
        action.upper()
    )


def is_postgresql_database():
    """
    Check if the current database is PostgreSQL.
    
    Returns:
        bool: True if PostgreSQL, False otherwise
    """
    db_engine = connection.settings_dict.get('ENGINE', '')
    return 'postgresql' in db_engine or 'postgis' in db_engine


def get_database_tables(exclude_system_tables=True):
    """
    Get list of tables from PostgreSQL database.
    
    Args:
        exclude_system_tables (bool): Whether to exclude system tables
        
    Returns:
        list: List of tuples (schema, table_name, rls_enabled, force_rls)
        
    Raises:
        RuntimeError: If database is not PostgreSQL
    """
    if not is_postgresql_database():
        raise RuntimeError("This operation requires a PostgreSQL database.")
    
    with connection.cursor() as cursor:
        if exclude_system_tables:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    relrowsecurity,
                    relforcerowsecurity
                FROM pg_tables
                LEFT JOIN pg_class ON pg_class.relname = pg_tables.tablename
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                AND schemaname !~ '^pg_toast'
                ORDER BY schemaname, tablename
            """)
        else:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    relrowsecurity,
                    relforcerowsecurity
                FROM pg_tables
                LEFT JOIN pg_class ON pg_class.relname = pg_tables.tablename
                ORDER BY schemaname, tablename
            """)
        
        return cursor.fetchall()


def check_policy_exists(table_name, policy_name):
    """
    Check if an RLS policy exists in the database.
    
    Args:
        table_name (str): The table name
        policy_name (str): The policy name
        
    Returns:
        bool: True if policy exists, False otherwise
    """
    if not is_postgresql_database():
        return False
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = %s AND policyname = %s
            )
        """, [table_name, policy_name])
        
        return cursor.fetchone()[0]


def get_table_rls_status(table_name):
    """
    Get RLS status for a specific table.
    
    Args:
        table_name (str): The table name
        
    Returns:
        tuple or None: (rls_enabled, force_rls) or None if table not found
    """
    if not is_postgresql_database():
        return None
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT relrowsecurity, relforcerowsecurity
            FROM pg_class
            WHERE relname = %s
        """, [table_name])
        
        return cursor.fetchone()


def get_policy_count(table_name):
    """
    Count RLS policies for a specific table.
    
    Args:
        table_name (str): The table name
        
    Returns:
        int: Number of policies
    """
    if not is_postgresql_database():
        return 0
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_policies
            WHERE tablename = %s
        """, [table_name])
        
        return cursor.fetchone()[0]


def execute_sql_safely(sql, params=None, error_message="SQL execution failed"):
    """
    Execute SQL with error handling.
    
    Args:
        sql (str): SQL statement to execute
        params (list): Parameters for SQL statement
        error_message (str): Error message prefix
        
    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])
        return (True, None)
    except Exception as e:
        return (False, f"{error_message}: {str(e)}")


def format_sql_preview(sql):
    """
    Format SQL for preview in admin interface.
    
    Args:
        sql (str): SQL statement
        
    Returns:
        SafeString: HTML formatted SQL
    """
    return format_html(
        '<pre style="background: #f5f5f5; padding: 10px; '
        'border-radius: 4px; overflow-x: auto;">{}</pre>',
        sql
    )
