from .common import *


DEBUG = True
SECRET_KEY = 'django-insecure-d%a#46#1z9miahk7nogor6nhvddqi4y+h8i-!5&n36h1*32=2t'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'test_storefront2',
#         'HOST': 'localhost',
#         'USER': 'root',
#         'PASSWORD': 'helalAIUB8009.@#'
#     }
# }

DATABASES = {
    'default': dj_database_url.parse("postgresql://neondb_owner:npg_Cel87mDsryIn@ep-super-term-ayqlo0ba-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
}