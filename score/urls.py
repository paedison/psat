from django.urls import path, include

urlpatterns = [
    path('psat/', include('score.urls_module.urls_psat')),  # PSAT score current version
    path('prime/', include('score.urls_module.urls_prime')),  # Prime score current version
    # path('v1/', include('score.urls_module.urls_psat_v1')),  # Version 1.0
    # path('v2/', include('score.urls_module.urls_psat_v2')),  # Version 2.0
]
