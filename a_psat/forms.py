from django import forms
from django.utils.translation import gettext_lazy as _

from . import models


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = models.ProblemTag
        fields = []


class ProblemCommentForm(forms.ModelForm):
    class Meta:
        model = models.ProblemComment
        fields = ['content', 'parent']


class ProblemMemoForm(forms.ModelForm):
    class Meta:
        model = models.ProblemMemo
        fields = ['content']


class ProblemCollectionForm(forms.ModelForm):
    title = forms.CharField(
        label='', label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': _('Input new collection name')}
        )
    )

    class Meta:
        model = models.ProblemCollection
        fields = ['title']


class LectureMemoForm(forms.ModelForm):
    class Meta:
        model = models.LectureMemo
        fields = ['content']
