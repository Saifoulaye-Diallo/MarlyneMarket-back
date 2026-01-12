"""
Settings module for african_back_end.

Load appropriate settings based on DJANGO_SETTINGS_MODULE environment variable.
- Development: african_back_end.settings.dev (default)
- Production: african_back_end.settings.prod

Usage in settings initialization:
export DJANGO_SETTINGS_MODULE=african_back_end.settings.dev  # for development
export DJANGO_SETTINGS_MODULE=african_back_end.settings.prod # for production
"""

import os

# Default to development
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'african_back_end.settings.dev'
