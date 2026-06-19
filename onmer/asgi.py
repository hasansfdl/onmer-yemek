"""
ASGI config for onmer project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from load_env import bootstrap

bootstrap()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onmer.settings')

application = get_asgi_application()
