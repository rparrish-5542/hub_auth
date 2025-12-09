"""
Reusable admin actions for RLS and permission management.
"""

from django.contrib import messages
from django.db import connection
from .admin_helpers import is_postgresql_database, execute_sql_safely, get_database_tables


def discover_tables_action(modeladmin, request, queryset, table_config_model):
    """
    Discover all user tables from PostgreSQL database and create config entries.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The queryset (not used for this action)
        table_config_model: The RLSTableConfig model class
    """
    if not is_postgresql_database():
        modeladmin.message_user(
            request,
            "RLS is only supported on PostgreSQL databases.",
            level=messages.ERROR
        )
        return
    
    discovered_count = 0
    existing_count = 0
    errors = []
    
    try:
        tables = get_database_tables(exclude_system_tables=True)
        
        for schema, table_name, rls_enabled, force_rls in tables:
            full_table_name = f"{schema}.{table_name}" if schema != 'public' else table_name
            
            # Check if config already exists
            if table_config_model.objects.filter(table_name=full_table_name).exists():
                existing_count += 1
                continue
            
            try:
                # Create new table config
                table_config_model.objects.create(
                    table_name=full_table_name,
                    description=f"Auto-discovered table from {schema} schema",
                    rls_enabled=rls_enabled or False,
                    force_rls=force_rls or False,
                    use_user_id=True,
                    use_scopes=False,
                    use_roles=False,
                    custom_session_vars={}
                )
                discovered_count += 1
            except Exception as e:
                errors.append(f"{full_table_name}: {str(e)}")
    
    except Exception as e:
        modeladmin.message_user(
            request,
            f"Error discovering tables: {str(e)}",
            level=messages.ERROR
        )
        return
    
    # Show results
    if discovered_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully discovered and added {discovered_count} new table(s)."
        )
    
    if existing_count > 0:
        modeladmin.message_user(
            request,
            f"Skipped {existing_count} table(s) - already configured.",
            level=messages.INFO
        )
    
    if errors:
        modeladmin.message_user(
            request,
            f"Errors: {'; '.join(errors[:5])}",
            level=messages.ERROR
        )
    
    if discovered_count == 0 and existing_count == 0:
        modeladmin.message_user(
            request,
            "No tables found in the database.",
            level=messages.WARNING
        )


def apply_policies_action(modeladmin, request, queryset):
    """
    Apply selected RLS policies to the database.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The selected policies queryset
    """
    if not is_postgresql_database():
        modeladmin.message_user(
            request,
            "RLS is only supported on PostgreSQL databases.",
            level=messages.ERROR
        )
        return
    
    applied_count = 0
    errors = []
    
    with connection.cursor() as cursor:
        for policy in queryset:
            if not policy.is_active:
                continue
            
            # Drop existing policy
            success, error = execute_sql_safely(
                policy.generate_drop_policy_sql(),
                error_message=f"Failed to drop policy {policy.name}"
            )
            
            if not success:
                errors.append(error)
                continue
            
            # Create new policy
            success, error = execute_sql_safely(
                policy.generate_create_policy_sql(),
                error_message=f"Failed to create policy {policy.name}"
            )
            
            if not success:
                errors.append(error)
                continue
            
            # Enable RLS on table
            success, error = execute_sql_safely(
                policy.generate_enable_rls_sql(),
                error_message=f"Failed to enable RLS on {policy.table_name}"
            )
            
            if success:
                applied_count += 1
            else:
                errors.append(error)
    
    if applied_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully applied {applied_count} RLS policies to database."
        )
    
    if errors:
        modeladmin.message_user(
            request,
            f"Errors: {'; '.join(errors[:5])}",
            level=messages.ERROR
        )


def remove_policies_action(modeladmin, request, queryset):
    """
    Remove selected RLS policies from the database.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The selected policies queryset
    """
    if not is_postgresql_database():
        modeladmin.message_user(
            request,
            "RLS is only supported on PostgreSQL databases.",
            level=messages.ERROR
        )
        return
    
    removed_count = 0
    errors = []
    
    for policy in queryset:
        success, error = execute_sql_safely(
            policy.generate_drop_policy_sql(),
            error_message=f"Failed to remove policy {policy.name}"
        )
        
        if success:
            removed_count += 1
        else:
            errors.append(error)
    
    if removed_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully removed {removed_count} RLS policies from database."
        )
    
    if errors:
        modeladmin.message_user(
            request,
            f"Errors: {'; '.join(errors[:5])}",
            level=messages.ERROR
        )


def enable_rls_action(modeladmin, request, queryset):
    """
    Enable RLS on selected tables.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The selected table configs queryset
    """
    if not is_postgresql_database():
        modeladmin.message_user(
            request,
            "RLS is only supported on PostgreSQL databases.",
            level=messages.ERROR
        )
        return
    
    enabled_count = 0
    errors = []
    
    for config in queryset:
        success, error = execute_sql_safely(
            config.generate_enable_rls_sql(),
            error_message=f"Failed to enable RLS on {config.table_name}"
        )
        
        if success:
            config.rls_enabled = True
            config.save()
            enabled_count += 1
        else:
            errors.append(error)
    
    if enabled_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully enabled RLS on {enabled_count} tables."
        )
    
    if errors:
        modeladmin.message_user(
            request,
            f"Errors: {'; '.join(errors[:5])}",
            level=messages.ERROR
        )


def disable_rls_action(modeladmin, request, queryset):
    """
    Disable RLS on selected tables.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The selected table configs queryset
    """
    if not is_postgresql_database():
        modeladmin.message_user(
            request,
            "RLS is only supported on PostgreSQL databases.",
            level=messages.ERROR
        )
        return
    
    disabled_count = 0
    errors = []
    
    for config in queryset:
        success, error = execute_sql_safely(
            config.generate_disable_rls_sql(),
            error_message=f"Failed to disable RLS on {config.table_name}"
        )
        
        if success:
            config.rls_enabled = False
            config.save()
            disabled_count += 1
        else:
            errors.append(error)
    
    if disabled_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully disabled RLS on {disabled_count} tables."
        )
    
    if errors:
        modeladmin.message_user(
            request,
            f"Errors: {'; '.join(errors[:5])}",
            level=messages.ERROR
        )


def activate_configuration_action(modeladmin, request, queryset, config_model, history_model):
    """
    Activate selected Azure AD configuration (deactivates others).
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The HttpRequest object
        queryset: The selected configs queryset
        config_model: The AzureADConfiguration model class
        history_model: The AzureADConfigurationHistory model class
    """
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Please select exactly one configuration to activate.",
            level=messages.ERROR
        )
        return
    
    config = queryset.first()
    
    # Deactivate all others
    config_model.objects.exclude(pk=config.pk).update(is_active=False)
    
    # Activate selected
    config.is_active = True
    config.save()
    
    # Log history
    history_model.objects.create(
        configuration=config,
        configuration_name=config.name,
        action='activated',
        tenant_id=config.tenant_id,
        client_id=config.client_id,
        changed_by=request.user.username if request.user.is_authenticated else 'unknown',
        details=f"Activated via admin action"
    )
    
    modeladmin.message_user(
        request,
        f"Configuration '{config.name}' is now active."
    )
