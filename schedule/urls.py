from django.urls import path, re_path

from schedule.views import CalendarView, event

app_name = 'schedule'

urlpatterns = [
    path('', CalendarView.as_view(), name='base'),
    re_path(r'^new/$', event, name='new'),
    re_path(r'^edit/(?P<event_id>\d+)/$', event, name='edit'),
]
