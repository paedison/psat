from django import forms

from .models import PrimePsatStudent


# class StudentForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields = ['year', 'department', 'serial']
#
#
# class PsatStudentForm(forms.ModelForm):
#     class Meta:
#         model = PsatStudent
#         fields = ['year', 'department', 'serial']


class PrimePsatStudentForm(forms.ModelForm):
    class Meta:
        model = PrimePsatStudent
        fields = ['serial', 'name', 'password']


# class PredictStudentForm(forms.ModelForm):
#     class Meta:
#         model = PredictStudent
#         fields = ['department_id', 'serial', 'name', 'password']
