from django.urls import path, include

from common.views import index_views

urlpatterns = [
    path('', index_views.index_view, name='index'),
    path('', include('common.urls_module.base')),
    path('account/', include('common.urls_module.account')),  # Login, Logout modal
]
