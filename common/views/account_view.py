from django.shortcuts import render


def login_modal(request):
    return render(request, 'snippets/modal.html#login', {})


def logout_modal(request):
    return render(request, 'snippets/modal.html#logout', {})
