"""
WSGI config for african_back_end project.
"""
import os
from django.core.wsgi import get_wsgi_application

# Use production settings for deployment; override with DJANGO_SETTINGS_MODULE env var
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'african_back_end.settings.prod')

application = get_wsgi_application()
