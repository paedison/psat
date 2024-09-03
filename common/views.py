import vanilla
from allauth.account import views as allauth_views
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from . import forms as common_forms
from .constants.icon_set import ConstantIconSet
from .models import User
from .utils import HtmxHttpRequest, update_context_data


@login_not_required
def index_view(_):
    return redirect('psat:base')


@login_not_required
def page_not_found(request, exception):
    if exception is None:
        return render(request, '404.html', {})
    else:
        return render(request, '404.html', {})


@login_not_required
def page_404(request):
    return render(request, '404.html', {})


@login_not_required
def ads(request):
    if request:
        return HttpResponse("google.com, pub-3543306443016219, DIRECT, f08c47fec0942fa0")


@login_not_required
def privacy(request):
    info = {'menu': 'privacy'}
    context = update_context_data(site_name='<PAEDISON>', info=info)
    return render(request, 'privacy.html', context)


def add_current_url_to_context(
        context: dict, request: HtmxHttpRequest, redirect_field_value='redirect_field_value'):
    if request.htmx:
        current_url = request.htmx.current_url
        context[redirect_field_value] = current_url
    return context


@method_decorator(login_not_required, name='dispatch')
class LoginModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#login'

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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_current_url_to_context(context, self.request)


@method_decorator(login_not_required, name='dispatch')
class SignupView(allauth_views.SignupView):
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


class UsernameChangeView(vanilla.UpdateView):
    template_name = 'account/username_change.html'
    form_class = common_forms.ChangeUsernameForm
    success_url = reverse_lazy('account_profile')

    def get_object(self):
        return User.objects.get(id=self.request.user.id)

    def form_valid(self, form):
        user = User.objects.get(id=self.request.user.id)
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        if not user.check_password(password):
            messages.error(self.request, _('Incorrect password.'))
            return self.form_invalid(form)
        if username == user.username:
            messages.error(self.request, _('Same as current username.'))
            return self.form_invalid(form)
        messages.success(self.request, _('Username successfully updated.'))
        return super().form_valid(form)


class PasswordChangeView(allauth_views.PasswordChangeView):
    success_url = reverse_lazy('account_profile')


login_modal = LoginModalView.as_view()
logout_modal = LogoutModalView.as_view()
profile_view = ProfileView.as_view()
username_change = UsernameChangeView.as_view()
password_change = PasswordChangeView.as_view()
