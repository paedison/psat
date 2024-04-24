from django.urls import path, include

urlpatterns = [
    path('', include('dashboard.urls_module.urls_v2')),  # Current version
    # path('v1/', include('dashboard.urls_module.urls_v1')),  # Ver 1.0
]
