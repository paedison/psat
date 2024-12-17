from django import forms

from . import models


class PsatForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = '__all__'
        widgets = {
            'year': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'round': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'page_opened_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'exam_started_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'exam_finished_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'answer_predict_opened_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'answer_official_opened_at': forms.DateTimeInput(attrs={'class': 'form-control'}),
        }


class PrimePsatStudentForm(forms.ModelForm):
    class Meta:
        model = models.ResultStudent
        fields = ['serial', 'name', 'password']
