from django.urls import path, include


urlpatterns = [
    path('', include('study.urls_module.urls_v0')),  # version 1.0 - current version
]