"""
Example URL configuration for admin SSO.

Copy this configuration to your project's urls.py file.
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from hub_auth_client.django.admin_views import MSALAdminLoginView, MSALAdminCallbackView


# Basic SSO URL Configuration
# This provides SSO as an additional login option alongside regular admin login
basic_urlpatterns = [
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    path('admin/', admin.site.urls),
]


# SSO as Default Login
# This makes SSO the default admin login, redirecting users to Microsoft
default_sso_urlpatterns = [
    # Redirect default admin login to SSO
    path('admin/login/', RedirectView.as_view(pattern_name='admin_msal_login', permanent=False)),
    
    # SSO URLs
    path('admin/login/msal/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/msal/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    
    # Standard admin fallback (access via /admin/login/local/)
    path('admin/login/local/', admin.site.login, name='admin_local_login'),
    
    path('admin/', admin.site.urls),
]


# Custom Paths
# Use custom URL paths for your SSO endpoints
custom_paths_urlpatterns = [
    path('admin/sso/', MSALAdminLoginView.as_view(), name='admin_sso_login'),
    path('admin/sso/callback/', MSALAdminCallbackView.as_view(), name='admin_sso_callback'),
    path('admin/', admin.site.urls),
]


# Complete Example with Multiple Options
urlpatterns = [
    # SSO login (primary method)
    path('admin/login/sso/', MSALAdminLoginView.as_view(), name='admin_msal_login'),
    path('admin/login/sso/callback/', MSALAdminCallbackView.as_view(), name='admin_msal_callback'),
    
    # Local login fallback (for emergency access)
    path('admin/login/local/', admin.site.login, name='admin_local_login'),
    
    # Admin site
    path('admin/', admin.site.urls),
    
    # Your other URLs
    # path('api/', include('myapp.urls')),
]


# Example: Custom Login Page with Both Options
"""
Create templates/admin/login.html:

{% extends "admin/login.html" %}

{% block content %}
<div class="login-options">
    <div class="sso-login">
        <a href="{% url 'admin_msal_login' %}" class="button primary">
            <img src="/static/microsoft-icon.svg" alt="Microsoft">
            Sign in with Microsoft
        </a>
    </div>
    
    <div class="divider">
        <span>OR</span>
    </div>
    
    <div class="local-login">
        {{ block.super }}
    </div>
</div>

<style>
.login-options {
    max-width: 400px;
    margin: 0 auto;
}

.sso-login {
    margin-bottom: 20px;
}

.sso-login .button {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 24px;
    background-color: #0078d4;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 500;
    transition: background-color 0.2s;
}

.sso-login .button:hover {
    background-color: #106ebe;
}

.sso-login img {
    width: 20px;
    height: 20px;
    margin-right: 10px;
}

.divider {
    text-align: center;
    margin: 30px 0;
    position: relative;
}

.divider::before,
.divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background-color: #ccc;
}

.divider::before {
    left: 0;
}

.divider::after {
    right: 0;
}

.divider span {
    background-color: white;
    padding: 0 10px;
    color: #666;
}
</style>
{% endblock %}
"""


# Important Notes for URL Configuration:
"""
1. Redirect URI in Azure AD MUST match your callback URL exactly:
   - Azure AD: https://yourdomain.com/admin/login/msal/callback/
   - Django: path('admin/login/msal/callback/', ...)
   - Include protocol (https://), domain, and trailing slash

2. For development, Azure AD allows http://localhost:8000/...
   But production MUST use HTTPS

3. If you change the callback URL path, update:
   - Azure AD app registration > Redirect URIs
   - MSAL_ADMIN_REDIRECT_URI setting (if using custom redirect)
   - This urls.py configuration

4. State parameter is automatically managed by the views for CSRF protection
   Don't remove or modify state handling

5. Session middleware is required for SSO to work:
   MIDDLEWARE = [
       'django.contrib.sessions.middleware.SessionMiddleware',
       ...
   ]
"""
