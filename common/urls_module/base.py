from django.urls import path

from common.views import base_views

urlpatterns = [
    path('', base_views.index, name='index'),
    path('404/', base_views.page_404, name='404'),
    path('ads.txt', base_views.ads, name='ads'),
    path('privacy/', base_views.privacy, name='privacy_policy'),  # Privacy Policy
]
