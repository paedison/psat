from datetime import time

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from a_psat import models
from common.utils import get_local_time


class PsatForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = ['year', 'exam', 'is_active']
        widgets = {
            'year': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PsatActiveForm(forms.ModelForm):
    class Meta:
        model = models.Psat
        fields = ['is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProblemUpdateForm(forms.Form):
    year = forms.ChoiceField(
        label='연도',
        choices=models.choices.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exam = forms.ChoiceField(
        label='시험',
        choices=models.choices.exam_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    file = forms.FileField(
        label='문제 업데이트',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )


class ProblemTagForm(forms.ModelForm):
    class Meta:
        model = models.ProblemTag
        fields = []


class ProblemCommentForm(forms.ModelForm):
    class Meta:
        model = models.ProblemComment
        fields = ['content', 'parent']


class ProblemMemoForm(forms.ModelForm):
    class Meta:
        model = models.ProblemMemo
        fields = ['content']


class ProblemCollectionForm(forms.ModelForm):
    title = forms.CharField(
        label='', label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': _('Input new collection name')}
        )
    )

    class Meta:
        model = models.ProblemCollection
        fields = ['title']


class LectureMemoForm(forms.ModelForm):
    class Meta:
        model = models.LectureMemo
        fields = ['content']


class PredictStudentForm(forms.Form):
    unit = forms.ChoiceField(
        choices=models.choices.predict_unit_choice(),
        initial='모집단위를 선택해주세요',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='모집단위',
        required=True,
    )
    department = forms.ChoiceField(
        choices=models.choices.predict_department_choice(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='직렬',
        required=True,
    )
    serial = forms.CharField(
        max_length=10, label='수험번호',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '수험번호'}),
    )
    name = forms.CharField(
        max_length=20, label='이름',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}),
    )
    password = forms.CharField(
        max_length=10, label='비밀번호',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
    )
    prime_id = forms.CharField(
        max_length=15, label='프라임법학원 ID', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '프라임법학원 ID'}),
    )


class UploadFileForm(forms.Form):
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))


class PredictPsatForm(forms.Form):
    year = forms.ChoiceField(
        label='연도', initial=timezone.now().year, choices=models.choices.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exam = forms.ChoiceField(
        label='시험', initial='5급공채/행정고시', choices=models.choices.exam_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    page_open_date = forms.DateField(
        label='페이지 오픈일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_date = forms.DateField(
        label='시험일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    predict_close_date = forms.DateField(
        label='합격 예측 종료일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', initial=time(9, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', initial=time(18, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_predict_open_time = forms.TimeField(
        label='예상 정답 공개 시각', initial=time(18, 30),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_official_open_time = forms.TimeField(
        label='공식 정답 공개 시각', initial=time(21, 00),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()

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

        if page_open_date:
            cleaned_data['page_opened_at'] = get_local_time(page_open_date)
        if exam_date:
            cleaned_data['exam_started_at'] = get_local_time(exam_date, exam_start_time)
        cleaned_data['exam_finished_at'] = get_local_time(exam_date, exam_finish_time)
        cleaned_data['answer_predict_opened_at'] = get_local_time(exam_date, answer_predict_open_time)
        cleaned_data['answer_official_opened_at'] = get_local_time(exam_date, answer_official_open_time)
        if predict_close_date:
            cleaned_data['predict_closed_at'] = get_local_time(predict_close_date)

        return cleaned_data
