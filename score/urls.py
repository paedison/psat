from django.urls import path

from score.views import TemporaryAnswerListView, TemporaryAnswerCreateView

app_name = 'score'

urlpatterns = [
    path('list/', TemporaryAnswerListView.as_view(), name='list'),
    path('list/<str:sub>/', TemporaryAnswerListView.as_view(), name='list_content'),
    path('answer/', TemporaryAnswerCreateView.as_view(), name='list_content'),
    # path('', index),
    # path('list/', DataListView.as_view(), name='list'),
    # path('detail/<int:copy_id>/', DataDetailView.as_view(), name='detail')
    # path('list/<int:category>/', DataListView.as_view(), name='list_content'),
    # path('list/nav/', DataListNavigationView.as_view(), name='list_navigation'),
]