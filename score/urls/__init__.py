from django.urls import path, include

urlpatterns = [
    path('v1/', include('score.urls.urls_v1')),
    path('psat/', include('score.urls.urls_v2')),
    path('prime/', include('score.urls.urls_prime')),
]
