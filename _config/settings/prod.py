import os
from .base import *  # noqa
import environ

env = environ.Env()
environ.Env.read_env()

DEBUG = False
ALLOWED_HOSTS = ['3.38.223.114', 'paedison.com']
STATIC_ROOT = BASE_DIR / 'static/'
STATICFILES_DIRS = []

DATABASES = {
    'default': {
        'ENGINE': env('SQL_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('SQL_DATABASE', default=os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': env('SQL_USER', default='user'),
        'PASSWORD': env('SQL_PASSWORD', default='password'),
        'HOST': env('SQL_HOST', default='localhost'),
        'PORT': env('SQL_PORT', default=''),
    }
}

# ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS').split()