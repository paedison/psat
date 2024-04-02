import vanilla
from allauth.account import views as allauth_views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from common import forms as common_forms
from common.constants.icon_set import ConstantIconSet
from common.models import User


class LoginModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#login'


class LogoutModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#logout'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {'next': self.request.GET.get('next', '')}
        )
        return context


class ProfileView(
    ConstantIconSet,
    vanilla.TemplateView,
):
    template_name = 'profile/v1/profile.html'

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
        if username == user.username:
            messages.error(self.request, _('Same as current username.'))
            return self.form_invalid(form)
        if not user.check_password(password):
            messages.error(self.request, _('Incorrect password.'))
            return self.form_invalid(form)
        messages.success(self.request, _('Username successfully updated.'))
        return super().form_valid(form)


class PasswordChangeView(allauth_views.PasswordChangeView):
    success_url = reverse_lazy('account_profile')


class ChangePasswordModalView(vanilla.TemplateView):
    template_name = 'profile/v1/modal.html#change_password'


login_modal = LoginModalView.as_view()
logout_modal = LogoutModalView.as_view()
profile_view = ProfileView.as_view()
username_change = UsernameChangeView.as_view()
password_change = PasswordChangeView.as_view()
change_password_modal = ChangePasswordModalView.as_view()
