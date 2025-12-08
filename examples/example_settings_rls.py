"""
Example Django settings.py configuration for RLS (Row-Level Security).

This shows how to configure hub_auth_client with PostgreSQL RLS support.
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Hub Auth Client - provides RLS models and admin
    'hub_auth_client.django',
    
    # Your apps
    'employee',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Hub Auth Client - MSAL token validation
    'hub_auth_client.django.MSALAuthenticationMiddleware',
    
    # RLS Middleware - sets PostgreSQL session variables
    'hub_auth_client.django.rls_middleware.RLSMiddleware',
    
    # Optional: Debug RLS session variables (development only)
    # 'hub_auth_client.django.rls_middleware.RLSDebugMiddleware',
]

ROOT_URLCONF = 'your_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'your_project.wsgi.application'

# Database - PostgreSQL required for RLS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'your_database'),
        'USER': os.getenv('DB_USER', 'your_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'your_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# Azure AD / MSAL Configuration
# ============================================================================

AZURE_AD_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID')
AZURE_AD_CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
AZURE_AD_CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET', '')  # Optional

# MSAL Token Validator Settings
MSAL_TOKEN_VALIDATOR = {
    'TENANT_ID': AZURE_AD_TENANT_ID,
    'CLIENT_ID': AZURE_AD_CLIENT_ID,
    'ALLOWED_AUDIENCES': [AZURE_AD_CLIENT_ID],  # Add your API audiences
    'TOKEN_VERSION': '2.0',  # or '1.0'
}

# ============================================================================
# Django REST Framework Configuration
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'hub_auth_client.django.MSALAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Use dynamic permissions for admin-configurable scope/role checks
        'hub_auth_client.django.DynamicPermission',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# ============================================================================
# RLS (Row-Level Security) Configuration
# ============================================================================

# RLS Debug Logging (development only)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'hub_auth.rls': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# ============================================================================
# Custom User Attributes for RLS
# ============================================================================

# Example: If your MSALUser has custom attributes like department_id,
# these will be available to RLS policies via session variables

# You can configure custom session variable mapping in RLSTableConfig through admin:
# {
#   "app.user_department_id": "user.department.id",
#   "app.user_office_id": "user.office.id"
# }
