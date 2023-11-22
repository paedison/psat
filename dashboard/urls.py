from django.urls import path, include

urlpatterns = [
    path('', include('dashboard.urls_module.urls_v1')),  # Current version
    # path('v1/', include('dashboard.urls_module.urls_v1')),  # Version 1.0
]
