"""
WSGI config for beyondTax project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

print("Python path:", sys.path)  # Print the Python path for debugging
print("Environment settings:", os.environ.get('DJANGO_SETTINGS_MODULE'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beyondTax.settings')

application = get_wsgi_application()
