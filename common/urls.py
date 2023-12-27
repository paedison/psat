from django.urls import path, include

from common.views import base_views

urlpatterns = [
    path('', base_views.index, name='index'),
    path('', include('common.urls_module.base')),
    path('account/', include('common.urls_module.account')),  # Login, Logout modal
]
