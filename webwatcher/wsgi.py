"""
WSGI config for webwatcher project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import sys
import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('/home/juan/webwatcher/venv/lib/python3.6/site-packages')

# Add the app's directory to the PYTHONPATH
sys.path.append('/home/juan/webwatcher')
sys.path.append('/home/juan/webwatcher/webwatcher')


from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webwatcher.settings")

application = get_wsgi_application()
