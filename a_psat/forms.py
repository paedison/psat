from django import forms
from django.utils.translation import gettext_lazy as _

from .models import *


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = ProblemTag
        fields = []


class ProblemCommentForm(forms.ModelForm):
    class Meta:
        model = ProblemComment
        fields = ['content', 'parent']


class ProblemMemoForm(forms.ModelForm):
    class Meta:
        model = ProblemMemo
        fields = ['content']


class ProblemCollectionForm(forms.ModelForm):
    title = forms.CharField(
        label='', label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': _('Input new collection name')}
        )
    )

    class Meta:
        model = ProblemCollection
        fields = ['title']
