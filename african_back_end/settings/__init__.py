"""
Settings module for marketplace.

Load appropriate settings based on DJANGO_SETTINGS_MODULE environment variable.
- Development: marketplace.settings.dev (default)
- Production: marketplace.settings.prod

Usage in settings initialization:
export DJANGO_SETTINGS_MODULE=marketplace.settings.dev  # for development
export DJANGO_SETTINGS_MODULE=marketplace.settings.prod # for production
"""

import os

# Default to development
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'marketplace.settings.dev'
