from django.urls import path, include

urlpatterns = [
    path('', include('dashboard.urls.urls_v1')),
]
