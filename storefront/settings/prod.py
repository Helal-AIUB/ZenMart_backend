import os
from .common import *

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['zenmart-backend.onrender.com', 'localhost', '127.0.0.1']