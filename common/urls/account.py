from django.urls import path

from ..views import account_views

urlpatterns = [
    path('login/modal/', account_views.login_modal, name='account_login_modal'),
    path('logout/modal/', account_views.logout_modal, name='account_logout_modal'),
]
