from datetime import time, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import make_aware

from . import models


class LeetForm(forms.Form):
    year = forms.ChoiceField(
        label='연도', label_suffix='', initial=timezone.now().year + 1,
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
    name = forms.CharField(
        label='시험명', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    abbr = forms.CharField(
        label='약칭', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
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


class PrimeLeetStudentForm(forms.ModelForm):
    class Meta:
        model = models.ResultStudent
        fields = ['serial', 'name', 'password']


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='',
        label_suffix='',
        widget=forms.FileInput(
            attrs={'class': 'form-control'}),
    )
