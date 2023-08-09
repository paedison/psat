# Django Core Import
from django import forms

# Third Party Library Import
from searchview import forms as search_view

# Custom App Import
from psat.models import ProblemMemo, ProblemTag


class ProblemSearchForm(search_view.SearchForm):
    data__contains = forms.CharField(
        label='Data',
        required=False,
        max_length=50,
    )


# class ProblemTagForm(forms.ModelForm):
#     class Meta:
#         model = Problem
#         fields = ['tags']
#         widgets = {
#             'tags': forms.TextInput(attrs={'data-role': 'tagsinput'})
#         }


class ProblemMemoForm(forms.ModelForm):
    class Meta:
        model = ProblemMemo
        fields = ['user', 'problem', 'content']


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = ProblemTag
        fields = ['user', 'problem']
