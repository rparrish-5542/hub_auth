"""
Example Django views using hub_auth_client.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from hub_auth_client.django import (
    HasScopes,
    HasRoles,
    HasAllScopes,
    require_token,
    require_scopes,
    require_roles,
)


# ============================================================================
# CLASS-BASED VIEWS (DRF)
# ============================================================================

class PublicView(APIView):
    """Public endpoint - no authentication required."""
    
    permission_classes = []  # Override default auth requirement
    
    def get(self, request):
        return Response({
            'message': 'This is a public endpoint',
            'authenticated': request.user.is_authenticated,
        })


class ProtectedView(APIView):
    """Protected endpoint - requires valid token."""
    
    # Uses default authentication from REST_FRAMEWORK settings
    
    def get(self, request):
        return Response({
            'message': 'You are authenticated!',
            'user': {
                'username': request.user.username,
                'email': request.user.email,
                'scopes': request.user.scopes,
                'roles': request.user.roles,
            }
        })


class UserReadView(APIView):
    """Requires User.Read scope."""
    
    permission_classes = [HasScopes(['User.Read'])]
    
    def get(self, request):
        return Response({
            'message': 'You have User.Read scope',
            'user': {
                'object_id': request.user.object_id,
                'username': request.user.username,
                'email': request.user.email,
            }
        })


class FileManagementView(APIView):
    """Requires either Files.Read or Files.Write scope."""
    
    permission_classes = [HasScopes(['Files.Read', 'Files.Write'])]
    
    def get(self, request):
        """User needs at least one of the scopes."""
        return Response({
            'message': 'You can read files',
            'scopes': request.user.scopes,
        })


class FileWriteView(APIView):
    """Requires BOTH Files.Read AND Files.Write scopes."""
    
    permission_classes = [HasAllScopes(['Files.Read', 'Files.Write'])]
    
    def post(self, request):
        """User must have both scopes."""
        return Response({
            'message': 'File created',
            'scopes': request.user.scopes,
        })


class AdminView(APIView):
    """Requires Admin role."""
    
    permission_classes = [HasRoles(['Admin'])]
    
    def get(self, request):
        return Response({
            'message': 'Admin access granted',
            'roles': request.user.roles,
        })


class ManagerOrAdminView(APIView):
    """Requires either Manager or Admin role."""
    
    permission_classes = [HasRoles(['Manager', 'Admin'])]
    
    def get(self, request):
        return Response({
            'message': 'Management access granted',
            'roles': request.user.roles,
        })


# ============================================================================
# FUNCTION-BASED VIEWS
# ============================================================================

@require_token
def simple_protected_view(request):
    """Function-based view requiring authentication."""
    return JsonResponse({
        'message': 'Authenticated',
        'user_id': request.msal_user['object_id'],
        'username': request.msal_user['user_principal_name'],
    })


@require_scopes(['User.Read'])
def user_profile_view(request):
    """Requires User.Read scope."""
    return JsonResponse({
        'message': 'User profile',
        'user': request.msal_user,
    })


@require_scopes(['Files.Read', 'Files.Write'], require_all=True)
def file_management_view(request):
    """Requires BOTH scopes."""
    return JsonResponse({
        'message': 'File management access',
        'scopes': request.msal_user['scopes'],
    })


@require_roles(['Admin'])
def admin_dashboard_view(request):
    """Requires Admin role."""
    return JsonResponse({
        'message': 'Admin dashboard',
        'roles': request.msal_user['roles'],
    })


# ============================================================================
# ADVANCED EXAMPLES
# ============================================================================

class ConditionalAccessView(APIView):
    """Example of conditional access based on scopes."""
    
    def get(self, request):
        user = request.user
        
        # Check different access levels
        can_read = user.has_scope('Files.Read')
        can_write = user.has_scope('Files.Write')
        can_delete = user.has_scope('Files.Delete')
        is_admin = user.has_role('Admin')
        
        return Response({
            'permissions': {
                'read': can_read,
                'write': can_write,
                'delete': can_delete or is_admin,  # Admins can always delete
            },
            'user': {
                'scopes': user.scopes,
                'roles': user.roles,
            }
        })


class MultiplePermissionsView(APIView):
    """Example using multiple permission classes."""
    
    permission_classes = [
        HasScopes(['User.Read']),
        HasRoles(['Employee']),
    ]
    
    def get(self, request):
        """User must pass ALL permission classes."""
        return Response({
            'message': 'You have both User.Read scope and Employee role',
        })


# ============================================================================
# ERROR HANDLING EXAMPLE
# ============================================================================

class CustomErrorHandlingView(APIView):
    """Example with custom error handling."""
    
    permission_classes = [HasScopes(['User.Read'])]
    
    def get(self, request):
        try:
            # Your business logic here
            return Response({'data': 'success'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
