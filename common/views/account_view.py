# Django Core Import
from django.shortcuts import redirect
from django.urls import reverse_lazy

# Third Party Library Import
from allauth.account.views import LogoutView, LoginView
from allauth.socialaccount.models import SocialAccount

# Custom App Import
from common.models import User


class CustomLoginView(LoginView):
    extra_context = {}

    def form_invalid(self, form):
        email = form.cleaned_data['login']
        try:
            existing_user = User.objects.get(email=email)
            try:
                SocialAccount.objects.get(user=existing_user)
                self.extra_context['existing_social_user'] = True
            except SocialAccount.DoesNotExist:
                pass
        except User.DoesNotExist:
            pass
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    def get_next_page(self):
        next_page = self.request.GET.get('next')
        if next_page:
            return next_page
        else:
            return reverse_lazy('psat:base')

    def logout(self, *args, **kwargs):
        super().logout(*args, **kwargs)
        next_page = self.get_next_page()
        return redirect(next_page)
