from django.urls import path, include

urlpatterns = [
    path('psat/', include('score.urls_module.psat_v3')),  # Psat score current version
    # path('psat_v2/', include('score.urls_module.psat_v2')),  # Psat score version 2.0
    # path('psat_v1/', include('score.urls_module.psat_v1')),  # Psat score version 1.0

    path('prime/', include('score.urls_module.prime_v2')),  # Prime score version 2.0
    # path('prime_v1/', include('score.urls_module.prime_v1')),  # Prime score version 1.0

    path('prime/admin/', include('score.urls_module.prime_admin_v2')),  # Prime_admin score version 2.0
    # path('prime_v1/admin/', include('score.urls_module.prime_admin_v1')),  # Prime_admin score version 1.0
]
