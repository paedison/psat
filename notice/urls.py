from django.urls import path, include

urlpatterns = [
    # path('', include('notice.urls_module.urls_default')),  # current version
    path('', include('notice.urls_module.urls_v3')),  # version 3.0
    # path('v2/', include('notice.urls_module.urls_v2')),  # version 2.0
    # path('v1/', include('notice.urls_module.urls_v1')),  # version 1.0
]
