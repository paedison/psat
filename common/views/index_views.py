import vanilla
from django.urls import reverse_lazy


class IndexView(vanilla.RedirectView):
    url = reverse_lazy('predict_test:index')


index_view = IndexView.as_view()