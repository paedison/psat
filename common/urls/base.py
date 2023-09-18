from django.urls import path

from ..views import base_views

urlpatterns = [
    path('404/', base_views.page_404, name='404'),
]
