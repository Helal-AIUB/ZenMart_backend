import os
from .common import *
import dj_database_url

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['zenmart-backend.onrender.com', 'localhost', '127.0.0.1']

DATABASES = {
    'default': dj_database_url.config()
}