from crispy_forms.helper import FormHelper
from django import forms
from searchview import forms as search_view

from .models import ProblemMemo, ProblemTag


class ProblemSearchForm(search_view.SearchForm):
    data__contains = forms.CharField(
        label='Data',
        required=False,
        max_length=50,
    )


class ProblemMemoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)

    class Meta:
        model = ProblemMemo
        fields = ['user', 'problem', 'content']


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = ProblemTag
        fields = ['user', 'problem']
