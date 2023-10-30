from django.urls import path, include

urlpatterns = [
    path('v1/', include('dashboard.urls.urls_v1')),
]
