# Django Core Import
from django import forms

# Third Party Library Import
from searchview import forms as search_view


class ProblemSearchForm(search_view.SearchForm):
    data__contains = forms.CharField(
        label='Data',
        required=False,
        max_length=50,
    )
