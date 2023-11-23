from django.urls import path, include

urlpatterns = [
    path('', include('community.urls_module.urls_v1')),  # Current version
]
