from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_signup_verification_email(request, user, activate_url):
    # Load the HTML template
    html_content = render_to_string('account/email/email_confirmation_message.html', {
        'request': request,
        'user': user,
        'activate_url': activate_url,
    })
    text_content = strip_tags(html_content)  # For plain text fallback

    # Create the email
    email = EmailMultiAlternatives(
        subject='[paedison.com] 회원가입을 환영합니다.',
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
