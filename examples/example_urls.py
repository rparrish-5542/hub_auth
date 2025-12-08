"""
Example URL configuration using hub_auth_client views.
"""

from django.urls import path
from . import example_views

urlpatterns = [
    # Public endpoints
    path('public/', example_views.PublicView.as_view(), name='public'),
    
    # Basic authentication
    path('protected/', example_views.ProtectedView.as_view(), name='protected'),
    
    # Scope-based access
    path('user/', example_views.UserReadView.as_view(), name='user-read'),
    path('files/', example_views.FileManagementView.as_view(), name='files'),
    path('files/write/', example_views.FileWriteView.as_view(), name='files-write'),
    
    # Role-based access
    path('admin/', example_views.AdminView.as_view(), name='admin'),
    path('management/', example_views.ManagerOrAdminView.as_view(), name='management'),
    
    # Function-based views
    path('simple/', example_views.simple_protected_view, name='simple'),
    path('profile/', example_views.user_profile_view, name='profile'),
    path('file-mgmt/', example_views.file_management_view, name='file-mgmt'),
    path('admin-dashboard/', example_views.admin_dashboard_view, name='admin-dashboard'),
    
    # Advanced examples
    path('conditional/', example_views.ConditionalAccessView.as_view(), name='conditional'),
    path('multi-perm/', example_views.MultiplePermissionsView.as_view(), name='multi-perm'),
    path('custom-error/', example_views.CustomErrorHandlingView.as_view(), name='custom-error'),
]
