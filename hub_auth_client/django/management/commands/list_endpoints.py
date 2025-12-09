"""
Django management command to list all available endpoints (views, URLs, serializers).
Helps identify which endpoints need to be secured with scopes/roles.

Usage:
    python manage.py list_endpoints
    python manage.py list_endpoints --format=json
    python manage.py list_endpoints --app=employees
    python manage.py list_endpoints --unsecured-only
"""

from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from django.conf import settings
import json
import re


class Command(BaseCommand):
    help = 'List all available endpoints, views, URLs, and serializers to help identify what needs securing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'json', 'csv'],
            help='Output format (table, json, csv)'
        )
        parser.add_argument(
            '--app',
            type=str,
            default=None,
            help='Filter by app name'
        )
        parser.add_argument(
            '--unsecured-only',
            action='store_true',
            help='Show only endpoints without permission classes'
        )
        parser.add_argument(
            '--show-serializers',
            action='store_true',
            help='Show serializer information for each endpoint'
        )

    def handle(self, *args, **options):
        endpoints = self.collect_endpoints()
        
        # Filter by app if specified
        if options['app']:
            endpoints = [e for e in endpoints if options['app'] in e['module']]
        
        # Filter unsecured only
        if options['unsecured_only']:
            endpoints = [e for e in endpoints if not e['permission_classes']]
        
        # Add serializer info if requested
        if options['show_serializers']:
            endpoints = self.add_serializer_info(endpoints)
        
        # Output in requested format
        if options['format'] == 'json':
            self.output_json(endpoints)
        elif options['format'] == 'csv':
            self.output_csv(endpoints)
        else:
            self.output_table(endpoints, options['show_serializers'])

    def collect_endpoints(self):
        """Collect all URL patterns and their views."""
        endpoints = []
        
        def extract_endpoints(patterns, prefix=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    # Recursively extract from included URL configs
                    new_prefix = prefix + str(pattern.pattern)
                    extract_endpoints(pattern.url_patterns, new_prefix)
                elif isinstance(pattern, URLPattern):
                    # Extract endpoint information
                    endpoint_info = self.extract_endpoint_info(pattern, prefix)
                    if endpoint_info:
                        endpoints.append(endpoint_info)
        
        resolver = get_resolver()
        extract_endpoints(resolver.url_patterns)
        
        return endpoints

    def extract_endpoint_info(self, pattern, prefix):
        """Extract detailed information about an endpoint."""
        try:
            # Get the view
            callback = pattern.callback
            if not callback:
                return None
            
            # Get view class or function
            view_class = None
            view_func = callback
            
            # Handle class-based views
            if hasattr(callback, 'view_class'):
                view_class = callback.view_class
            elif hasattr(callback, 'cls'):
                view_class = callback.cls
            
            # Get module and name
            module = callback.__module__
            if view_class:
                name = view_class.__name__
            else:
                name = callback.__name__
            
            # Get URL pattern
            url_pattern = prefix + str(pattern.pattern)
            
            # Get HTTP methods
            methods = []
            if view_class:
                if hasattr(view_class, 'http_method_names'):
                    methods = [m.upper() for m in view_class.http_method_names 
                              if hasattr(view_class, m)]
                else:
                    methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
            else:
                methods = ['GET']  # Function-based views default to GET
            
            # Get permission classes
            permission_classes = []
            if view_class and hasattr(view_class, 'permission_classes'):
                permission_classes = [
                    p.__name__ for p in view_class.permission_classes
                ]
            
            # Get authentication classes
            authentication_classes = []
            if view_class and hasattr(view_class, 'authentication_classes'):
                authentication_classes = [
                    a.__name__ for a in view_class.authentication_classes
                ]
            
            # Get view name/description
            description = ''
            if view_class and hasattr(view_class, '__doc__'):
                description = (view_class.__doc__ or '').strip().split('\n')[0]
            elif hasattr(view_func, '__doc__'):
                description = (view_func.__doc__ or '').strip().split('\n')[0]
            
            return {
                'url_pattern': url_pattern,
                'name': pattern.name or '',
                'view_name': name,
                'module': module,
                'methods': methods,
                'permission_classes': permission_classes,
                'authentication_classes': authentication_classes,
                'description': description,
                'view_class': view_class,
            }
        
        except Exception as e:
            self.stderr.write(f"Error extracting endpoint info: {e}")
            return None

    def add_serializer_info(self, endpoints):
        """Add serializer information to endpoints."""
        for endpoint in endpoints:
            view_class = endpoint.get('view_class')
            if view_class:
                # Get serializer class
                serializer_class = None
                if hasattr(view_class, 'serializer_class'):
                    serializer_class = view_class.serializer_class
                elif hasattr(view_class, 'get_serializer_class'):
                    try:
                        # Try to get serializer class without instantiating
                        serializer_class = view_class().get_serializer_class()
                    except:
                        pass
                
                if serializer_class:
                    endpoint['serializer'] = serializer_class.__name__
                    endpoint['serializer_module'] = serializer_class.__module__
                    
                    # Get serializer fields
                    try:
                        serializer_fields = list(serializer_class().fields.keys())
                        endpoint['serializer_fields'] = serializer_fields
                    except:
                        endpoint['serializer_fields'] = []
                else:
                    endpoint['serializer'] = None
                    endpoint['serializer_module'] = None
                    endpoint['serializer_fields'] = []
        
        return endpoints

    def output_table(self, endpoints, show_serializers=False):
        """Output endpoints as a formatted table."""
        if not endpoints:
            self.stdout.write(self.style.WARNING('No endpoints found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nFound {len(endpoints)} endpoints:\n'))
        
        # Header
        header = f"{'URL Pattern':<50} {'Methods':<20} {'View':<30} {'Permissions':<30}"
        if show_serializers:
            header += f" {'Serializer':<30}"
        
        self.stdout.write(self.style.HTTP_INFO(header))
        self.stdout.write(self.style.HTTP_INFO('-' * len(header)))
        
        # Sort by URL pattern
        endpoints.sort(key=lambda x: x['url_pattern'])
        
        # Rows
        for endpoint in endpoints:
            url = endpoint['url_pattern'][:48]
            methods = ','.join(endpoint['methods'][:3])[:18]
            view = endpoint['view_name'][:28]
            
            # Highlight unsecured endpoints
            perms = ','.join(endpoint['permission_classes'][:2])[:28] if endpoint['permission_classes'] else 'NONE'
            if not endpoint['permission_classes']:
                perms_display = self.style.ERROR(f'{perms:<30}')
            else:
                perms_display = f'{perms:<30}'
            
            row = f"{url:<50} {methods:<20} {view:<30} {perms_display}"
            
            if show_serializers:
                serializer = endpoint.get('serializer', 'N/A')[:28]
                row += f" {serializer:<30}"
            
            self.stdout.write(row)
            
            # Show description if available
            if endpoint['description']:
                self.stdout.write(f"  → {endpoint['description'][:100]}")
        
        # Summary
        unsecured_count = len([e for e in endpoints if not e['permission_classes']])
        self.stdout.write(f"\n{self.style.WARNING(f'Unsecured endpoints: {unsecured_count}/{len(endpoints)}')}")
        
        if unsecured_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'\n⚠ Warning: {unsecured_count} endpoints have no permission classes!\n'
                    'Consider securing them with scopes/roles using EndpointPermission.'
                )
            )

    def output_json(self, endpoints):
        """Output endpoints as JSON."""
        # Remove view_class from output (not JSON serializable)
        clean_endpoints = []
        for e in endpoints:
            clean_e = {k: v for k, v in e.items() if k != 'view_class'}
            clean_endpoints.append(clean_e)
        
        self.stdout.write(json.dumps(clean_endpoints, indent=2))

    def output_csv(self, endpoints):
        """Output endpoints as CSV."""
        import csv
        import sys
        
        writer = csv.writer(sys.stdout)
        
        # Header
        writer.writerow([
            'URL Pattern',
            'Methods',
            'View Name',
            'Module',
            'Permission Classes',
            'Authentication Classes',
            'Description'
        ])
        
        # Rows
        for endpoint in endpoints:
            writer.writerow([
                endpoint['url_pattern'],
                ','.join(endpoint['methods']),
                endpoint['view_name'],
                endpoint['module'],
                ','.join(endpoint['permission_classes']),
                ','.join(endpoint['authentication_classes']),
                endpoint['description']
            ])
