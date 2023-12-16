from django.urls import path, include

urlpatterns = [
    path('psat/', include('score.urls_module.urls_psat')),  # PSAT score current version
    path('prime/', include('score.urls_module.urls_prime')),  # Prime score current version
    path('prime/admin/', include('score.urls_module.urls_prime_admin')),  # Prime_admin score current version

    # path('v1/', include('score.urls_module.urls_psat_v1')),  # Version 1.0
    # path('v2/', include('score.urls_module.urls_psat_v2')),  # Version 2.0
    # path('prime_v2/', include('score.urls_module.urls_prime_v2')),  # Prime score current version
    # path('prime_v2/admin/', include('score.urls_module.urls_prime_admin_v2')),  # Prime_admin score current version
]
