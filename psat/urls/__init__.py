from django.urls import path, include

urlpatterns = [
    path('v1/', include('psat.urls.urls_v1')),  # PSAT version 1.0
    path('v2/', include('psat.urls.urls_v2')),  # PSAT Version 2.0
]
