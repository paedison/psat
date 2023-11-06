from django.urls import path, include

urlpatterns = [
    path('v1/', include('score.urls.urls_v1')),
    path('v2/', include('score.urls.urls_v2')),
]
