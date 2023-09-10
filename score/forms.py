from crispy_forms.helper import FormHelper
from django import forms

from score.models import TemporaryAnswer


class TemporaryAnswerForm(forms.ModelForm):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper(self)
    #
    class Meta:
        model = TemporaryAnswer
        fields = ['problem', 'answer']
        # fields = ['user', 'problem', 'answer']
