from django.urls import path

from ..views import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_views.main, name='base'),

    path('like/', dashboard_views.like, name='like_all'),
    path('like/<int:is_liked>liked/', dashboard_views.like, name='like'),

    path('rate/', dashboard_views.rate, name='rate_all'),
    path('rate/<int:star_count>star/', dashboard_views.rate, name='rate'),

    path('answer/', dashboard_views.answer, name='answer_all'),
    path('answer/<int:is_correct>correct/', dashboard_views.answer, name='answer'),
]
