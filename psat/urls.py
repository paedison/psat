from django.urls import path, include

urlpatterns = [
    path('', include('psat.urls_module.urls_v3')),  # version 3.0 - current version
    # path('v2/', include('psat.urls_module.urls_v2')),  # version 2.0
    # path('v1/', include('psat.urls_module.urls_v1')),  # version 1.0
]
