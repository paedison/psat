from crispy_forms.helper import FormHelper
from django import forms

from . import models as custom_models


class ProblemMemoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)

    class Meta:
        model = custom_models.ProblemMemo
        fields = ['user', 'problem', 'content']


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = custom_models.ProblemTag
        fields = ['user', 'problem']


class MemoForm(forms.ModelForm):
    class Meta:
        model = custom_models.Memo
        fields = ['memo']


class TagForm(forms.ModelForm):
    class Meta:
        model = custom_models.Tag
        fields = ['problem']


class CommentForm(forms.ModelForm):
    class Meta:
        model = custom_models.Comment
        fields = ['comment', 'parent']
