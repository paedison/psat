from django import forms

from .models import TemporaryAnswer


class TemporaryAnswerForm(forms.ModelForm):
    class Meta:
        model = TemporaryAnswer
        fields = ['problem', 'answer']
