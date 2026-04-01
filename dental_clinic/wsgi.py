"""
WSGI config for dental clinic project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dental_clinic.settings")

application = get_wsgi_application()
