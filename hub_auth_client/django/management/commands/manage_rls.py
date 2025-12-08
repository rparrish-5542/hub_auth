"""
Django management command to manage RLS policies.

Usage:
    python manage.py manage_rls --help
    python manage.py manage_rls --apply-all
    python manage.py manage_rls --remove-all
    python manage.py manage_rls --preview
    python manage.py manage_rls --enable-table employee_employee
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Manage PostgreSQL Row-Level Security (RLS) policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply-all',
            action='store_true',
            help='Apply all active RLS policies to the database',
        )
        parser.add_argument(
            '--remove-all',
            action='store_true',
            help='Remove all RLS policies from the database',
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview SQL for all active RLS policies',
        )
        parser.add_argument(
            '--enable-table',
            type=str,
            help='Enable RLS on a specific table',
        )
        parser.add_argument(
            '--disable-table',
            type=str,
            help='Disable RLS on a specific table',
        )
        parser.add_argument(
            '--policy',
            type=str,
            help='Apply a specific policy by name',
        )
        parser.add_argument(
            '--table',
            type=str,
            help='Filter policies by table name',
        )

    def handle(self, *args, **options):
        """Handle the management command."""
        
        # Check if PostgreSQL
        db_engine = connection.settings_dict.get('ENGINE', '')
        if 'postgresql' not in db_engine and 'postgis' not in db_engine:
            raise CommandError('RLS is only supported on PostgreSQL databases.')
        
        # Import RLS models
        try:
            from hub_auth_client.django.rls_models import RLSPolicy, RLSTableConfig
        except ImportError:
            raise CommandError(
                'RLS models not found. Make sure hub_auth_client.django.rls_models '
                'is installed and migrations are run.'
            )
        
        if options['preview']:
            self.preview_policies(RLSPolicy, options.get('table'))
        
        elif options['apply_all']:
            self.apply_all_policies(RLSPolicy, options.get('table'))
        
        elif options['remove_all']:
            self.remove_all_policies(RLSPolicy, options.get('table'))
        
        elif options['enable_table']:
            self.enable_table_rls(RLSTableConfig, options['enable_table'])
        
        elif options['disable_table']:
            self.disable_table_rls(RLSTableConfig, options['disable_table'])
        
        elif options['policy']:
            self.apply_specific_policy(RLSPolicy, options['policy'])
        
        else:
            self.show_status(RLSPolicy, RLSTableConfig)
    
    def preview_policies(self, RLSPolicy, table_name=None):
        """Preview SQL for RLS policies."""
        
        policies = RLSPolicy.objects.filter(is_active=True)
        if table_name:
            policies = policies.filter(table_name=table_name)
        
        if not policies.exists():
            self.stdout.write(self.style.WARNING('No active policies found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nFound {policies.count()} active policies:\n'))
        
        for policy in policies:
            self.stdout.write(self.style.HTTP_INFO(f'\n--- {policy.name} on {policy.table_name} ---'))
            self.stdout.write(policy.generate_create_policy_sql())
            self.stdout.write('')
    
    def apply_all_policies(self, RLSPolicy, table_name=None):
        """Apply all active RLS policies to database."""
        
        policies = RLSPolicy.objects.filter(is_active=True)
        if table_name:
            policies = policies.filter(table_name=table_name)
        
        if not policies.exists():
            self.stdout.write(self.style.WARNING('No active policies found.'))
            return
        
        self.stdout.write(f'Applying {policies.count()} RLS policies...\n')
        
        applied_count = 0
        errors = []
        
        with connection.cursor() as cursor:
            for policy in policies:
                try:
                    self.stdout.write(f'  Applying {policy.name} on {policy.table_name}...', ending='')
                    
                    # Drop existing policy
                    cursor.execute(policy.generate_drop_policy_sql())
                    
                    # Enable RLS on table
                    cursor.execute(policy.generate_enable_rls_sql())
                    
                    # Create policy
                    cursor.execute(policy.generate_create_policy_sql())
                    
                    self.stdout.write(self.style.SUCCESS(' ✓'))
                    applied_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' ✗ Error: {str(e)}'))
                    errors.append(f"{policy.name}: {str(e)}")
        
        self.stdout.write('')
        if applied_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully applied {applied_count} policies.'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n✗ {len(errors)} errors occurred:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
    
    def remove_all_policies(self, RLSPolicy, table_name=None):
        """Remove all RLS policies from database."""
        
        policies = RLSPolicy.objects.all()
        if table_name:
            policies = policies.filter(table_name=table_name)
        
        if not policies.exists():
            self.stdout.write(self.style.WARNING('No policies found.'))
            return
        
        self.stdout.write(f'Removing {policies.count()} RLS policies...\n')
        
        removed_count = 0
        errors = []
        
        with connection.cursor() as cursor:
            for policy in policies:
                try:
                    self.stdout.write(f'  Removing {policy.name} from {policy.table_name}...', ending='')
                    cursor.execute(policy.generate_drop_policy_sql())
                    self.stdout.write(self.style.SUCCESS(' ✓'))
                    removed_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' ✗ Error: {str(e)}'))
                    errors.append(f"{policy.name}: {str(e)}")
        
        self.stdout.write('')
        if removed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully removed {removed_count} policies.'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n✗ {len(errors)} errors occurred:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
    
    def enable_table_rls(self, RLSTableConfig, table_name):
        """Enable RLS on a specific table."""
        
        config, created = RLSTableConfig.objects.get_or_create(
            table_name=table_name,
            defaults={'rls_enabled': True}
        )
        
        if not created and config.rls_enabled:
            self.stdout.write(self.style.WARNING(f'RLS already enabled on {table_name}'))
            return
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(config.generate_enable_rls_sql())
            
            config.rls_enabled = True
            config.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ RLS enabled on {table_name}'))
        
        except Exception as e:
            raise CommandError(f'Failed to enable RLS on {table_name}: {str(e)}')
    
    def disable_table_rls(self, RLSTableConfig, table_name):
        """Disable RLS on a specific table."""
        
        try:
            config = RLSTableConfig.objects.get(table_name=table_name)
        except RLSTableConfig.DoesNotExist:
            raise CommandError(f'No RLS config found for table {table_name}')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(config.generate_disable_rls_sql())
            
            config.rls_enabled = False
            config.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ RLS disabled on {table_name}'))
        
        except Exception as e:
            raise CommandError(f'Failed to disable RLS on {table_name}: {str(e)}')
    
    def apply_specific_policy(self, RLSPolicy, policy_name):
        """Apply a specific policy by name."""
        
        try:
            policy = RLSPolicy.objects.get(name=policy_name)
        except RLSPolicy.DoesNotExist:
            raise CommandError(f'Policy "{policy_name}" not found')
        
        try:
            with connection.cursor() as cursor:
                # Drop existing
                cursor.execute(policy.generate_drop_policy_sql())
                
                # Enable RLS
                cursor.execute(policy.generate_enable_rls_sql())
                
                # Create policy
                cursor.execute(policy.generate_create_policy_sql())
            
            self.stdout.write(self.style.SUCCESS(f'✓ Applied policy "{policy_name}" on {policy.table_name}'))
        
        except Exception as e:
            raise CommandError(f'Failed to apply policy "{policy_name}": {str(e)}')
    
    def show_status(self, RLSPolicy, RLSTableConfig):
        """Show current RLS status."""
        
        self.stdout.write(self.style.HTTP_INFO('\n=== RLS Status ===\n'))
        
        # Show table configs
        configs = RLSTableConfig.objects.all()
        if configs.exists():
            self.stdout.write(self.style.SUCCESS('Tables with RLS:'))
            for config in configs:
                status = '✓ Enabled' if config.rls_enabled else '✗ Disabled'
                force = ' (FORCE)' if config.force_rls else ''
                self.stdout.write(f'  {config.table_name}: {status}{force}')
        else:
            self.stdout.write(self.style.WARNING('No tables configured for RLS'))
        
        self.stdout.write('')
        
        # Show policies
        policies = RLSPolicy.objects.all()
        if policies.exists():
            active = policies.filter(is_active=True).count()
            inactive = policies.filter(is_active=False).count()
            
            self.stdout.write(self.style.SUCCESS(f'RLS Policies: {active} active, {inactive} inactive'))
            
            for policy in policies.filter(is_active=True):
                self.stdout.write(
                    f'  ✓ {policy.name} on {policy.table_name} '
                    f'({policy.policy_command}, {policy.policy_type})'
                )
            
            for policy in policies.filter(is_active=False):
                self.stdout.write(
                    f'  ✗ {policy.name} on {policy.table_name} '
                    f'({policy.policy_command}, {policy.policy_type}) - INACTIVE'
                )
        else:
            self.stdout.write(self.style.WARNING('No RLS policies defined'))
        
        self.stdout.write('')
