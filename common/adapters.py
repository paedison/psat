from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from .emails import send_signup_verification_email


class AccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        user = emailconfirmation.email_address.user
        activate_url = f"{request.scheme}://{request.get_host()}{reverse('account_confirm_email', args=[emailconfirmation.key])}"
        send_signup_verification_email(request, user, activate_url)
