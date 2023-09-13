from django.urls import path

from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.list_view, name='list'),
    path('<int:copy_id>/', views.detail, name='detail')
]