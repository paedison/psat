from django.urls import path

from .views import DataListView, index, DataDetailView

app_name = 'analysis'

urlpatterns = [
    # path('', index),
    path('list/', DataListView.as_view(), name='list'),
    path('detail/<int:copy_id>/', DataDetailView.as_view(), name='detail')
    # path('list/<int:category>/', DataListView.as_view(), name='list_content'),
    # path('list/nav/', DataListNavigationView.as_view(), name='list_navigation'),
]