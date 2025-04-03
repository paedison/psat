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
    predict_close_date = forms.DateField(
        label='성적 예측 종료일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', label_suffix='', initial=time(9, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', label_suffix='', initial=time(12, 50),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_predict_open_time = forms.TimeField(
        label='예상 정답 공개 시각', label_suffix='', initial=time(12, 50),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_official_open_time = forms.TimeField(
        label='공식 정답 공개 시각', label_suffix='', initial=time(12, 50),
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
            predict_close_date = cleaned_data['predict_close_date']
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
        cleaned_data['predict_closed_at'] = get_local_time(predict_close_date, time(17, 00))

        return cleaned_data


class LeetActiveForm(forms.ModelForm):
    class Meta:
        model = models.Leet
        fields = ['is_active']
        widgets = {'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})}


class ResultStudentForm(forms.Form):
    leet = forms.ModelChoiceField(
        label='시험명', queryset=models.Leet.objects.filter(year=2026, is_active=True),
        empty_label='시험을 선택해주세요',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    serial = forms.CharField(label='수험번호', widget=forms.TextInput(attrs={'class': 'form-control'}))
    student_name = forms.CharField(label='이름', widget=forms.TextInput(attrs={'class': 'form-control'}))
    student_password = forms.CharField(
        label='비밀번호', widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'password'}))


class PredictStudentForm(ResultStudentForm):
    leet = forms.ModelChoiceField(
        label='시험명',
        queryset=models.Leet.objects.filter(
            year=2026, page_opened_at__lte=timezone.now(), predict_closed_at__gte=timezone.now()),
        empty_label='시험을 선택해주세요',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    school = forms.ChoiceField(
        label='출신대학', choices=models.choices.university_choice(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    major = forms.ChoiceField(
        label='전공', choices=models.choices.major_choice,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    aspiration_1 = forms.ChoiceField(
        label='1지망', choices=models.choices.university_choice,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    aspiration_2 = forms.ChoiceField(
        label='2지망', choices=models.choices.university_choice,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gpa_type = forms.ChoiceField(
        label='학점(GPA) 종류', choices=models.choices.gpa_type_choice,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gpa = forms.FloatField(label='학점(GPA)', widget=forms.TextInput(attrs={'class': 'form-control'}))
    english_type = forms.ChoiceField(
        label='공인 영어성적 종류', choices=models.choices.english_type_choice,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    english = forms.IntegerField(label='공인 영어성적', widget=forms.TextInput(attrs={'class': 'form-control'}))


class UploadFileForm(forms.Form):
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))
