from django.urls import path

from psat.views.v4 import update_views as v

# basic url: 'psat/update/'

urlpatterns = [
    path('<str:view_type>/<int:problem_id>/', v.CustomUpdateView.as_view(), name='custom'),
    path('rate/modal/', v.RateModalView.as_view(), name='rate_modal'),
    path('solve/modal/', v.SolveModalView.as_view(), name='solve_modal'),
]
