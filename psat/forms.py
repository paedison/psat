from crispy_forms.helper import FormHelper
from django import forms

from .models import ProblemMemo, ProblemTag, Memo, Tag


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


class MemoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)

    class Meta:
        model = Memo
        fields = ['user', 'problem', 'content']


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['user', 'problem']
