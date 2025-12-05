# hub_auth/authentication/urls.py
"""URL configuration for authentication API."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'service-clients', views.ServiceClientViewSet, basename='serviceclient')
router.register(r'validation-logs', views.TokenValidationLogViewSet, basename='validationlog')

app_name = 'authentication'

urlpatterns = [
    # Token validation endpoints
    path('validate/', views.validate_token, name='validate-token'),
    path('validate-simple/', views.validate_token_simple, name='validate-token-simple'),
    
    # Admin endpoints
    path('', include(router.urls)),
]
