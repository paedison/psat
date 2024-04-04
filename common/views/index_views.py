import vanilla
from django.urls import reverse_lazy


class IndexView(vanilla.RedirectView):
    url = reverse_lazy('psat:base')


index_view = IndexView.as_view()
