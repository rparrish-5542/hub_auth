# hub_auth/authentication/permissions.py
"""Custom permissions for hub_auth."""
from rest_framework import permissions


class ServiceClientPermission(permissions.BasePermission):
    """Permission class for service client management endpoints."""
    
    def has_permission(self, request, view):
        """Only allow staff/superusers to access service client management."""
        return request.user and request.user.is_authenticated and request.user.is_staff
