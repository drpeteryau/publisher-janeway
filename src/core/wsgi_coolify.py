"""WSGI entrypoint for container deployments.

Static and media files are served by WhiteNoise *outside* Django's middleware
stack, so requests for them are never subject to Janeway's host/site lookup.
"""

from django.conf import settings
from whitenoise import WhiteNoise

from core.wsgi import application as django_application

application = WhiteNoise(django_application)
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL.strip("/"))
# Media is written at runtime, so re-scan the directory on each request.
application.autorefresh = True
application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL.strip("/"))
