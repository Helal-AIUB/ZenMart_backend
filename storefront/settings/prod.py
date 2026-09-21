# import os
# from .common import *
# import dj_database_url

# DEBUG = False
# SECRET_KEY = os.environ['SECRET_KEY']

# ALLOWED_HOSTS = ['zenmart-backend.onrender.com', 'localhost', '127.0.0.1']

# DATABASES = {
#     'default': dj_database_url.config()
# }


import os
from .common import *
import dj_database_url

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key')

ALLOWED_HOSTS = ['zenmart-backend.onrender.com', 'localhost', '127.0.0.1']

DATABASES = {
    'default': dj_database_url.config()
}

# Add this code to clean up Dev Tools in Production
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'silk' in INSTALLED_APPS:
    INSTALLED_APPS.remove('silk')

MIDDLEWARE = [m for m in MIDDLEWARE if m not in [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'silk.middleware.SilkyMiddleware',
]]