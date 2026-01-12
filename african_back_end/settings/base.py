"""
Base Django settings for marketplace project.

This is shared by both development and production.
Environment-specific settings are in dev.py and prod.py.
"""

import os
from pathlib import Path
import environ
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

# Environment setup
env = environ.Env(
    DEBUG=(bool, False),
    JWT_ALGORITHM=(str, 'HS256'),
    JWT_ACCESS_TOKEN_LIFETIME=(int, 3600),
    JWT_REFRESH_TOKEN_LIFETIME=(int, 604800),
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root
environ.Env.read_env(BASE_DIR / '.env')

# Core settings (overridable via env)
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production!')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'apps.accounts',
    'apps.catalog',
    'apps.customers',
    'apps.orders',
    'apps.payments',
    'apps.returns',
    'apps.reviews',
    'apps.promotions',
    'apps.wishlist',
    'apps.cart',
    'apps.testimonial',
    'apps.brand',
    'apps.dashboard',
    'apps.userprofile',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'african_back_end.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'african_back_end.wsgi.application'

# Database configuration - Can be overridden in dev/prod
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': env('DB_USER', default=''),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default=''),
        'PORT': env('DB_PORT', default=''),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = env('DEFAULT_LANGUAGE', default='en')
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Supported languages - Expandable to 8+
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Static and Media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Storage Configuration
import cloudinary
from cloudinary import config

# Configuration Cloudinary depuis les variables d'environnement
CLOUDINARY_URL = env('CLOUDINARY_URL', default='')
if CLOUDINARY_URL:
    # Parse Cloudinary URL for detailed config
    cloudinary.config(cloudinary_url=CLOUDINARY_URL)
    
    # Storage configuration
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': cloudinary.config().cloud_name,
        'API_KEY': cloudinary.config().api_key,
        'API_SECRET': cloudinary.config().api_secret,
        'SECURE': True,  # Use HTTPS
        'MEDIA_TAG': 'media',
        'INVALID_VIDEO_ERROR_MESSAGE': 'Please upload a valid video file.',
        'EXCLUDE_DELETE_ORPHANED_MEDIA_PATHS': (),
        'STATIC_TAG': 'static',
    }
else:
    # Fallback to local storage if Cloudinary is not configured
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = env(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# drf-spectacular Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Marketplace API',
    'DESCRIPTION': 'Multi-vendor marketplace API with orders, payments, reviews, returns and promotions.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },
    'TAGS': [
        {'name': 'Auth', 'description': 'Authentication endpoints'},
        {'name': 'Catalog', 'description': 'Products and categories'},
        {'name': 'Customers', 'description': 'Customer profiles and addresses'},
        {'name': 'Orders', 'description': 'Order management'},
        {'name': 'Payments', 'description': 'Payment processing'},
        {'name': 'Returns', 'description': 'Return requests'},
        {'name': 'Reviews', 'description': 'Product reviews'},
        {'name': 'Promotions', 'description': 'Coupons and promotions'},
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    'ALGORITHM': env('JWT_ALGORITHM'),
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=env('JWT_ACCESS_TOKEN_LIFETIME')),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=env('JWT_REFRESH_TOKEN_LIFETIME')),
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ROTATE_REFRESH_TOKENS': True,
    'CHECK_REVOKE_TOKEN': True,
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'
# Unfold Admin Theme Configuration
UNFOLD = {
    "SITE_HEADER": "Marketplace Admin",
    "SITE_TITLE": "Marketplace",
    "SITE_URL": "/",
    "SITE_LOGO": None,  # Optional: URL to logo image
    "SITE_ICON": None,  # Optional: URL to favicon
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "development" if DEBUG else "production",
    "DASHBOARD": {
        "WIDGETS": [
            "unfold.contrib.widgets.UnfoldAdminDashboardWidget",
        ],
    },
    "COLORS": {
        "primary": {
            "50": "#f0f9ff",
            "100": "#e0f2fe",
            "200": "#bae6fd",
            "300": "#7dd3fc",
            "400": "#38bdf8",
            "500": "#0ea5e9",
            "600": "#0284c7",
            "700": "#0369a1",
            "800": "#075985",
            "900": "#0c3d66",
        },
    },
    "STYLES": {
        "sidebar": {
            "width": "250px",
        },
    },
}

# Django Filter settings
FILTERS_HELP_TEXT_EXCLUDE = True

# Stripe Configuration
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@marketplace.com')
ADMIN_EMAIL = env('ADMIN_EMAIL', default='admin@marketplace.com')
