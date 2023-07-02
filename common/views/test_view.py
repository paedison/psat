from django.core.mail import EmailMessage
from django.http import HttpResponse


def test1(request):
    email = EmailMessage('test', 'test', to=['paedison.com@gmail.com'])
    result = email.send()
    return HttpResponse()
