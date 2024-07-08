from django.urls import path, include

urlpatterns = [
    # path('psat/', include('score.urls_module.psat_v4')),  # Psat score current version

    path('prime/psat/', include('a_score.urls.urls_prime_psat')),  # Prime score current version
    path('prime/psat/admin/', include('a_score.urls.urls_prime_psat_admin')),  # Prime_admin score current version
    path('prime/police/', include('a_score.urls.urls_prime_police')),  # Prime score current version
]
