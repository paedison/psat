from django import forms

from .models import ResultStudent


class PrimePsatStudentForm(forms.ModelForm):
    class Meta:
        model = ResultStudent
        fields = ['serial', 'name', 'password']
