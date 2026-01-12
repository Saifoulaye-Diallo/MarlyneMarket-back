"""
DEPRECATED: Settings have been refactored to separate dev/prod configurations.

This file is kept for backward compatibility only.
New settings are in marketplace/settings/base.py, dev.py, and prod.py

To use different settings:
- Development: DJANGO_SETTINGS_MODULE=marketplace.settings.dev
- Production: DJANGO_SETTINGS_MODULE=marketplace.settings.prod

This file will be removed in a future version.
"""

# Import all from base for backward compatibility
from marketplace.settings.base import *  # noqa

# This ensures old references still work
__all__ = []

