from django.urls import path

from dashboard.views.v1 import psat_views

app_name = 'dashboard'

urlpatterns = [
    path('', psat_views.main_view, name='base'),
    path('list/<str:view_type>/', psat_views.like_view, name='list'),
    # path('', psat_views.dashboard_main_view, name='base'),
]
