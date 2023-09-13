from django.urls import path

from ..views import account_view

urlpatterns = [
    path('login/modal/', account_view.login_modal, name='account_login_modal'),
    path('logout/modal/', account_view.logout_modal, name='account_logout_modal'),
]
