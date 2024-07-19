from django.shortcuts import redirect, render

from common.utils import update_context_data


# def index_view(request):
#     return redirect('psat:base')


def index_view(request):
    info = {'menu': 'predict', 'view_type': 'predict'}
    context = update_context_data(info=info)
    return render(request, 'index.html', context)