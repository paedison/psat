from django import forms
from django.utils.translation import gettext_lazy as _

from . import models


class PsatForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = ['year', 'exam', 'order', 'is_active']
        widgets = {
            'year': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PsatActiveForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = ['is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProblemUpdateForm(forms.Form):
    year = forms.ChoiceField(
        label='연도',
        choices=models.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exam = forms.ChoiceField(
        label='시험',
        choices=models.exam_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    update_file = forms.FileField(
        label='문제 업데이트',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )


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
