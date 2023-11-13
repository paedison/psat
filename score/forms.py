from django import forms

from .models import Student, PsatStudent, PrimeStudent


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['year', 'department', 'serial']


class PsatStudentForm(forms.ModelForm):
    class Meta:
        model = PsatStudent
        fields = ['year', 'department', 'serial']


class PrimeStudentForm(forms.ModelForm):
    class Meta:
        model = PrimeStudent
        fields = ['year', 'round', 'serial', 'name', 'password']
