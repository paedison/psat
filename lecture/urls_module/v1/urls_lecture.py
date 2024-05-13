from django.urls import path

from psat.views.v4 import problem_views as v

# basic url: 'psat/'

urlpatterns = [
    path('', v.ListView.as_view(), name='base'),
    path('list/', v.ProblemListView.as_view(), name='list'),
    path('detail/<int:problem_id>/', v.DetailView.as_view(), name='detail'),
    path('detail/<int:problem_id>/img/', v.DetailImageView.as_view(), name='detail_image'),
    path('detail/list/<str:view_type>/', v.DetailNavigationView.as_view(), name='detail_list'),
]
