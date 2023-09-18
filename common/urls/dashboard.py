from django.urls import path

from ..views import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_views.base_view, name='base'),
    path('<str:view_type>/', dashboard_views.base_view, name='list'),
]
