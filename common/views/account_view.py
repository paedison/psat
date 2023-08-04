# Django Core Import
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy

# Third Party Library Import
from allauth.account import views as all_auth
from allauth.socialaccount.models import SocialAccount
from django.views.generic import RedirectView

# Custom App Import
from ..models import User


class CustomLoginView(all_auth.LoginView):
    extra_context = {}

    def form_invalid(self, form):
        email = form.cleaned_data['login']
        print(email)
        try:
            existing_user = User.objects.get(email=email)
            try:
                SocialAccount.objects.get(user=existing_user)
                messages.error(self.request, '소셜로그인으로 등록된 이메일입니다.')
            except SocialAccount.DoesNotExist:
                pass
        except User.DoesNotExist:
            pass
        return super().form_invalid(form)


class DummyLoginView(RedirectView):
    url = reverse_lazy('psat:base')


class DummyLogoutView(RedirectView):
    url = reverse_lazy('psat:base')


class DummySignupView(RedirectView):
    url = reverse_lazy('psat:base')


class CustomLogoutView(all_auth.LogoutView):
    def get_next_page(self):
        next_page = self.request.GET.get('next')
        if next_page:
            return next_page
        else:
            return reverse_lazy('psat:base')

    def logout(self, *args, **kwargs):
        super().logout()
        next_page = self.get_next_page()
        return redirect(next_page)
