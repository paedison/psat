import vanilla
from allauth.account import views as allauth_views
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from .. import forms as common_forms
from ..constants.icon_set import ConstantIconSet
from ..utils import HtmxHttpRequest, update_context_data


def add_current_url_to_context(
        context: dict, request: HtmxHttpRequest, redirect_field_value='redirect_field_value'):
    if request.htmx:
        current_url = request.htmx.current_url
        context[redirect_field_value] = current_url
    return context


@method_decorator(login_not_required, name='dispatch')
class LoginModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#login'
    request: HtmxHttpRequest

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request, 'next')


class LogoutModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#logout'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = update_context_data(context, next=self.request.GET.get('next', ''))
        return context


@method_decorator(login_not_required, name='dispatch')
class LoginView(allauth_views.LoginView):
    request: HtmxHttpRequest

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request)


@method_decorator(login_not_required, name='dispatch')
class SignupView(allauth_views.SignupView):
    request: HtmxHttpRequest

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request)


class ProfileView(ConstantIconSet, vanilla.TemplateView):
    template_name = 'account/profile.html'

    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        additional = {
            'icon_menu': self.ICON_MENU['profile']
        }
        context.update(additional)
        return context


class UsernameChangeView(vanilla.FormView):
    template_name = 'account/username_change.html'
    form_class = common_forms.ChangeUsernameForm
    success_url = reverse_lazy('account_profile')

    def form_valid(self, form):
        user = self.request.user
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        has_error = False
        if not user.check_password(password):
            has_error = True
            messages.error(self.request, _('Incorrect password.'))
        if username == user.username:
            has_error = True
            messages.error(self.request, _('Same as current username.'))
        else:
            user.username = form.cleaned_data['username']
            user.save()
            messages.success(self.request, _('Username successfully updated.'))

        if has_error:
            return self.form_invalid(form)
        else:
            return super().form_valid(form)


class PasswordChangeView(allauth_views.PasswordChangeView):
    success_url = reverse_lazy('account_profile')


@method_decorator(login_not_required, name='dispatch')
class PasswordResetDoneView(vanilla.TemplateView):
    template_name = 'account/password_reset_done.html'


login_modal = LoginModalView.as_view()
logout_modal = LogoutModalView.as_view()
profile_view = ProfileView.as_view()
username_change = UsernameChangeView.as_view()
password_change = PasswordChangeView.as_view()
password_reset_done = PasswordResetDoneView.as_view()
