from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['unit_id', 'department_id', 'serial', 'name', 'password']
