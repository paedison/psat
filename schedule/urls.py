# Django Core Import
from django.urls import path
from django.conf.urls import url

# Custom App Import
from schedule.views import CalendarView, event

app_name = 'schedule'

urlpatterns = [
    path('', CalendarView.as_view(), name='base'),
    url(r'^new/$', event, name='new'),
    url(r'^edit/(?P<event_id>\d+)/$', event, name='edit'),
]
