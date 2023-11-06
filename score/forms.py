from django import forms

from .models import Student, PsatStudent


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['year', 'department', 'serial']


class PsatStudentForm(forms.ModelForm):
    class Meta:
        model = PsatStudent
        fields = ['year', 'department', 'serial']
