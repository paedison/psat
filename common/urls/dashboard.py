# Django Core Import
from django.urls import path

# Custom App Import
from common.views.dashboard_views import (
    DashboardMainView, LikeDashboardView, RateDashboardView, AnswerDashboardView
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardMainView.as_view(), name='main'),

    path('like/', LikeDashboardView.as_view(), name='like'),
    path('like/<int:is_liked>liked/', LikeDashboardView.as_view(), name='like'),

    path('rate/', RateDashboardView.as_view(), name='rate'),
    path('rate/<int:star_count>star/', RateDashboardView.as_view(), name='rate'),

    path('answer/', AnswerDashboardView.as_view(), name='answer'),
    path('answer/<int:is_correct>correct/', AnswerDashboardView.as_view(), name='answer'),
]