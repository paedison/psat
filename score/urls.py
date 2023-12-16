from django.urls import path, include

urlpatterns = [
    path('psat/', include('score.urls_module.urls_psat')),  # Psat score current version
    path('prime/', include('score.urls_module.urls_prime')),  # Prime score current version
    path('prime/admin/', include('score.urls_module.urls_prime_admin')),  # Prime_admin score current version

    # path('psat_v1/', include('score.urls_module.urls_psat_v1')),  # Psat score version 1.0
    # path('psat_v2/', include('score.urls_module.urls_psat_v2')),  # Psat score version 2.0
    # path('prime_v1/', include('score.urls_module.urls_prime_v1')),  # Prime score version 1.0
    # path('prime_v2/', include('score.urls_module.urls_prime_v2')),  # Prime score version 2.0
    # path('prime_v1/admin/', include('score.urls_module.urls_prime_admin_v1')),  # Prime_admin score version 1.0
    # path('prime_v2/admin/', include('score.urls_module.urls_prime_admin_v2')),  # Prime_admin score version 2.0
]
