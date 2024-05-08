from django.urls import path, include


urlpatterns = [
    path('', include('lecture.urls_module.urls_v1')),  # version 1.0 - current version
    # path('', include('study.urls_module.urls_v0')),  # version 0.0
]