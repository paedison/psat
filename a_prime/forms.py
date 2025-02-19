from datetime import time, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import make_aware

from . import models


class PsatForm(forms.Form):
    year = forms.ChoiceField(
        label='연도', label_suffix='', initial=timezone.now().year,
        choices=models.choices.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exam = forms.ChoiceField(
        label='시험', label_suffix='', initial='프모',
        choices=models.choices.exam_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    round = forms.IntegerField(
        label='회차', label_suffix='', initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    page_open_date = forms.DateField(
        label='페이지 오픈일', label_suffix='', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_date = forms.DateField(
        label='시험일', label_suffix='', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', label_suffix='', initial=time(9, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', label_suffix='', initial=time(17, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_predict_open_time = forms.TimeField(
        label='예상 정답 공개 시각', label_suffix='', initial=time(17, 30),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_official_open_time = forms.TimeField(
        label='공식 정답 공개 시각', label_suffix='', initial=time(17, 30),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()

        def get_local_time(target_date, target_time=time(9, 0)):
            if not target_date:
                raise ValidationError("Date is required for timezone conversion.")
            target_datetime = datetime.combine(target_date, target_time)
            return make_aware(target_datetime)

        try:
            page_open_date = cleaned_data['page_open_date']
            exam_date = cleaned_data['exam_date']
            exam_start_time = cleaned_data['exam_start_time']
            exam_finish_time = cleaned_data['exam_finish_time']
            answer_predict_open_time = cleaned_data['answer_predict_open_time']
            answer_official_open_time = cleaned_data['answer_official_open_time']
        except KeyError as e:
            raise ValidationError(f"Missing field: {e.args[0]}")

        cleaned_data['page_opened_at'] = get_local_time(page_open_date)
        cleaned_data['exam_started_at'] = get_local_time(exam_date, exam_start_time)
        cleaned_data['exam_finished_at'] = get_local_time(exam_date, exam_finish_time)
        cleaned_data['answer_predict_opened_at'] = get_local_time(exam_date, answer_predict_open_time)
        cleaned_data['answer_official_opened_at'] = get_local_time(exam_date, answer_official_open_time)

        return cleaned_data


class PsatActiveForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = ['is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PrimeResultStudentForm(forms.ModelForm):
    password = forms.CharField(
        max_length=10, initial='', label='비밀번호',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
    )

    class Meta:
        model = models.ResultStudent
        fields = ['serial', 'name', 'password']
        widgets = {
            'serial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '수험번호'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}),
        }


class PrimePredictStudentForm(forms.ModelForm):
    unit = forms.ChoiceField(
        choices=models.choices.unit_choice(),
        initial='모집단위를 선택해주세요',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='모집단위',
        required=True,
    )
    department = forms.ChoiceField(
        choices=models.choices.department_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='직렬',
        required=True,
    )
    password = forms.CharField(
        max_length=10, initial='', label='비밀번호',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
    )

    class Meta:
        model = models.PredictStudent
        fields = ['serial', 'name', 'password']
        widgets = {
            'serial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '수험번호'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}),
        }

    def save(self, commit=True):
        unit = self.cleaned_data['unit']
        department = self.cleaned_data['department']
        category = models.Category.objects.get(unit=unit, department=department)
        student = super().save(commit=False)
        student.category = category
        if commit:
            student.save()
        return student


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='',
        label_suffix='',
        widget=forms.FileInput(
            attrs={'class': 'form-control'}),
    )
