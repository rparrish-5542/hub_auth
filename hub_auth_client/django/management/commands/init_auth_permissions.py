"""
Django management command to initialize common scopes and roles.

Usage:
    python manage.py init_auth_permissions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from hub_auth_client.django.models import ScopeDefinition, RoleDefinition


class Command(BaseCommand):
    help = 'Initialize common scopes and roles for authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing scopes and roles before initializing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing scopes and roles...')
            ScopeDefinition.objects.all().delete()
            RoleDefinition.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))

        self.stdout.write('Initializing scopes and roles...')

        with transaction.atomic():
            # Common scopes
            scopes = [
                # User scopes
                ('User.Read', 'User', 'Read user profile information'),
                ('User.Write', 'User', 'Update user profile'),
                ('User.ReadAll', 'User', 'Read all users'),
                
                # Employee scopes
                ('Employee.Read', 'Employee', 'Read employee information'),
                ('Employee.Write', 'Employee', 'Create and update employees'),
                ('Employee.Delete', 'Employee', 'Delete employees'),
                ('Employee.ReadAll', 'Employee', 'Read all employees'),
                
                # Files scopes
                ('Files.Read', 'Files', 'Read files'),
                ('Files.Write', 'Files', 'Create and update files'),
                ('Files.Delete', 'Files', 'Delete files'),
                ('Files.Share', 'Files', 'Share files with others'),
                
                # Department scopes
                ('Department.Read', 'Department', 'Read department information'),
                ('Department.Write', 'Department', 'Manage departments'),
                
                # Admin scopes
                ('Admin.Read', 'Admin', 'Read admin data'),
                ('Admin.Write', 'Admin', 'Manage admin settings'),
            ]

            for name, category, description in scopes:
                scope, created = ScopeDefinition.objects.get_or_create(
                    name=name,
                    defaults={
                        'category': category,
                        'description': description,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(f'  Created scope: {name}')
                else:
                    self.stdout.write(f'  Scope exists: {name}')

            # Common roles
            roles = [
                ('Admin', 'Administrator with full access'),
                ('Manager', 'Manager with elevated permissions'),
                ('HR', 'Human Resources staff'),
                ('User', 'Regular user'),
                ('ReadOnly', 'Read-only access'),
                ('Guest', 'Guest user with limited access'),
            ]

            for name, description in roles:
                role, created = RoleDefinition.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(f'  Created role: {name}')
                else:
                    self.stdout.write(f'  Role exists: {name}')

        self.stdout.write(self.style.SUCCESS('\nInitialization complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Go to Django admin (/admin/)')
        self.stdout.write('2. Configure endpoint permissions')
        self.stdout.write('3. Map URL patterns to required scopes/roles')
        self.stdout.write('\nSee DYNAMIC_PERMISSIONS.md for detailed instructions.')
