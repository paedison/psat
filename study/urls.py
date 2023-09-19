from django.urls import path
from . import views

app_name = 'study'


urlpatterns = [
    path('', views.base_view, name='base'),
    path('<str:view_type>/', views.base_view, name='list')
]