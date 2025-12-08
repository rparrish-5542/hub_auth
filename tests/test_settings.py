"""Minimal Django settings for testing."""

SECRET_KEY = 'test-secret-key'
DEBUG = True
ROOT_URLCONF = 'tests.test_urls'  # Required for Django views

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',  # Required for admin SSO tests
    'rest_framework',
    'hub_auth_client.django',  # Add the package app
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Azure AD settings for testing
AZURE_AD_TENANT_ID = 'test-tenant-id'
AZURE_AD_CLIENT_ID = 'test-client-id'

# MSAL settings
MSAL_VALIDATE_AUDIENCE = True
MSAL_VALIDATE_ISSUER = True
MSAL_TOKEN_LEEWAY = 0
MSAL_EXEMPT_PATHS = ['/health/']

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.authentication.MSALAuthentication',
    ],
}

# Middleware
MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

USE_TZ = True
