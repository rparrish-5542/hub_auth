"""
View decorators for MSAL token validation.

Usage:
    from hub_auth_client.django import require_token, require_scopes
    
    @require_token
    def my_view(request):
        # Token is validated, user info in request.msal_user
        ...
    
    @require_scopes(['User.Read', 'Files.ReadWrite'])
    def my_view(request):
        # User has at least one of the required scopes
        ...
"""

import functools
from typing import List, Callable
from django.conf import settings
from django.http import JsonResponse

from ..validator import MSALTokenValidator


def get_validator():
    """Get or create MSALTokenValidator instance."""
    tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', None)
    client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', None)
    
    if not tenant_id or not client_id:
        raise ValueError(
            "AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID must be set in Django settings"
        )
    
    return MSALTokenValidator(
        tenant_id=tenant_id,
        client_id=client_id,
        validate_audience=getattr(settings, 'MSAL_VALIDATE_AUDIENCE', True),
        validate_issuer=getattr(settings, 'MSAL_VALIDATE_ISSUER', True),
        leeway=getattr(settings, 'MSAL_TOKEN_LEEWAY', 0),
    )


def require_token(view_func: Callable) -> Callable:
    """
    Decorator that requires a valid MSAL token.
    
    Attaches token claims to request.msal_token and user info to request.msal_user.
    
    Usage:
        @require_token
        def my_view(request):
            user_id = request.msal_user['object_id']
            ...
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return JsonResponse(
                {'error': 'Missing Authorization header'},
                status=401
            )
        
        # Validate token
        validator = get_validator()
        is_valid, claims, error = validator.validate_token(auth_header)
        
        if not is_valid:
            return JsonResponse(
                {'error': 'Invalid token', 'message': error},
                status=401
            )
        
        # Attach to request
        request.msal_token = claims
        request.msal_user = validator.extract_user_info(claims)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_scopes(required_scopes: List[str], require_all: bool = False) -> Callable:
    """
    Decorator that requires specific scopes.
    
    Args:
        required_scopes: List of required scopes
        require_all: If True, all scopes required; if False, at least one (default: False)
    
    Usage:
        @require_scopes(['User.Read', 'Files.ReadWrite'])
        def my_view(request):
            # User has at least one of the required scopes
            ...
        
        @require_scopes(['User.Read', 'Files.ReadWrite'], require_all=True)
        def my_view(request):
            # User has both scopes
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if not auth_header:
                return JsonResponse(
                    {'error': 'Missing Authorization header'},
                    status=401
                )
            
            # Validate token with scope requirements
            validator = get_validator()
            is_valid, claims, error = validator.validate_token(
                auth_header,
                required_scopes=required_scopes,
                require_all_scopes=require_all,
            )
            
            if not is_valid:
                return JsonResponse(
                    {'error': 'Insufficient scopes', 'message': error},
                    status=403
                )
            
            # Attach to request
            request.msal_token = claims
            request.msal_user = validator.extract_user_info(claims)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_roles(required_roles: List[str], require_all: bool = False) -> Callable:
    """
    Decorator that requires specific roles.
    
    Args:
        required_roles: List of required roles
        require_all: If True, all roles required; if False, at least one (default: False)
    
    Usage:
        @require_roles(['Admin', 'Manager'])
        def my_view(request):
            # User has at least one of the required roles
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if not auth_header:
                return JsonResponse(
                    {'error': 'Missing Authorization header'},
                    status=401
                )
            
            # Validate token with role requirements
            validator = get_validator()
            is_valid, claims, error = validator.validate_token(
                auth_header,
                required_roles=required_roles,
                require_all_roles=require_all,
            )
            
            if not is_valid:
                return JsonResponse(
                    {'error': 'Insufficient roles', 'message': error},
                    status=403
                )
            
            # Attach to request
            request.msal_token = claims
            request.msal_user = validator.extract_user_info(claims)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
