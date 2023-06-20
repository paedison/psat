from django.urls import path

from common.views.base_views import page_404

urlpatterns = [
    path('404/', page_404, name='404'),
]
