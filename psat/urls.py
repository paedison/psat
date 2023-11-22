from django.urls import path, include

urlpatterns = [
    path('', include('psat.urls_module.urls_default')),  # Current version
    # path('v1/', include('psat.urls_module.urls_v1')),  # Version 1.0
    # path('v2/', include('psat.urls_module.urls_v1')),  # Version 2.0
]
