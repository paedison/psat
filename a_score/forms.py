from django import forms

from .models import PrimePsatStudent, PrimePoliceStudent


class PrimePsatStudentForm(forms.ModelForm):
    class Meta:
        model = PrimePsatStudent
        fields = ['serial', 'name', 'password']


class PrimePoliceStudentForm(forms.ModelForm):
    class Meta:
        model = PrimePoliceStudent
        fields = ['serial', 'name', 'password']
