from django.shortcuts import render


def login_modal_view(request):
    return render(request, 'snippets/modal.html#login', {})


def logout_modal_view(request):
    return render(request, 'snippets/modal.html#logout', {})
