from django.urls import path

from common.views.dashboard_views import (
    DashboardMainView, LikeDashboardView, RateDashboardView, AnswerDashboardView
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardMainView.as_view(), name='base'),

    path('like/', LikeDashboardView.as_view(), name='like_all'),
    path('like/<int:is_liked>liked/', LikeDashboardView.as_view(), name='like'),

    path('rate/', RateDashboardView.as_view(), name='rate_all'),
    path('rate/<int:star_count>star/', RateDashboardView.as_view(), name='rate'),

    path('answer/', AnswerDashboardView.as_view(), name='answer_all'),
    path('answer/<int:is_correct>correct/', AnswerDashboardView.as_view(), name='answer'),
]