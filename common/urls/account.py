# Python Standard Function Import
from importlib import import_module

# Third Party Library Import
from allauth import app_settings
from allauth.account import views as allauth_views
from allauth.socialaccount import providers

# Django Core Import
from django.urls import path, re_path, include

# Custom App Import
from common.views.account_view import CustomLoginView, CustomLogoutView
from common.views.base_views import ProfileView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),

    path("signup/", allauth_views.signup, name="account_signup"),
    path("login/", CustomLoginView.as_view(), name="account_login"),
    path("logout/", CustomLogoutView.as_view(), name="account_logout"),
    path("password/change/", allauth_views.password_change, name="account_change_password"),
    path("password/set/", allauth_views.password_set, name="account_set_password"),
    path("inactive/", allauth_views.account_inactive, name="account_inactive"),

    # E-mail
    path("email/", allauth_views.email, name="account_email"),
    path("confirm-email/", allauth_views.email_verification_sent,
         name="account_email_verification_sent"),
    re_path(r"^confirm-email/(?P<key>[-:\w]+)/$", allauth_views.confirm_email,
            name="account_confirm_email"),

    # password reset
    path("password/reset/", allauth_views.password_reset, name="account_reset_password"),
    path("password/reset/done/", allauth_views.password_reset_done,
         name="account_reset_password_done"),
    re_path(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
            allauth_views.password_reset_from_key, name="account_reset_password_from_key"),
    path("password/reset/key/done/", allauth_views.password_reset_from_key_done,
         name="account_reset_password_from_key_done"),
]

if app_settings.SOCIALACCOUNT_ENABLED:
    urlpatterns += [path("social/", include("allauth.socialaccount.urls"))]

# Provider urlpatterns, as separate attribute (for reusability).
provider_urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + ".urls")
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns
urlpatterns += provider_urlpatterns
