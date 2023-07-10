from django.urls import path

from .views import create_request_log

app_name = 'log'

urlpatterns = [
    path('request/', create_request_log, name='request_log'),
]