# Django Core Import
from django.urls import path

# Custom App Import
from common.views.dashboard_view import (
    MainView, DashboardLikeView, DashboardRateView, DashboardAnswerView
)

app_name = 'dashboard'

urlpatterns = [
    path('', MainView.as_view(), name='main'),

    path('like/', DashboardLikeView.as_view(), name='like'),
    path('like/<int:is_liked>liked/', DashboardLikeView.as_view(), name='like'),

    path('rate/', DashboardRateView.as_view(), name='rate'),
    path('rate/<int:star_count>star/', DashboardRateView.as_view(), name='rate'),

    path('answer/', DashboardAnswerView.as_view(), name='answer'),
    path('answer/<int:is_correct>correct/', DashboardAnswerView.as_view(), name='answer'),
]