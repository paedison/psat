from django import forms

from .models import custom_models


class MemoForm(forms.ModelForm):
    class Meta:
        model = custom_models.Memo
        fields = ['memo']


class TagForm(forms.ModelForm):
    class Meta:
        model = custom_models.Tag
        fields = []


class CommentForm(forms.ModelForm):
    class Meta:
        model = custom_models.Comment
        fields = ['comment', 'parent']
