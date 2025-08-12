from .base import *

DEBUG = True
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'a_boardgame_set' / 'static',
]

# DJANGO-Debug-Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]
