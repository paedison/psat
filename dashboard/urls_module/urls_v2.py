from django.urls import path

from dashboard.views.v2 import psat_views as v

app_name = 'dashboard'

urlpatterns = [
    path('', v.MainView.as_view(), name='base'),
    path('list/<str:view_type>/', v.ListView.as_view(), name='list'),
]
