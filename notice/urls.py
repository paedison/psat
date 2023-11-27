from django.urls import path, include

urlpatterns = [
    path('', include('notice.urls_module.urls_default')),  # Current version
    # path('v1/', include('notice.urls_module.urls_v1')),  # Version 1.0
    # path('v2/', include('notice.urls_module.urls_v2')),  # Version 2.0
]
