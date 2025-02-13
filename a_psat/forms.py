from datetime import time, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

from . import models


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


class PredictStudentForm(forms.ModelForm):
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
        category = models.PredictCategory.objects.get(unit=unit, department=department)
        student = super().save(commit=False)
        student.category = category
        if commit:
            student.save()
        return student


class UploadFileForm(forms.Form):
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))


class PredictPsatForm(forms.Form):
    year = forms.ChoiceField(
        label='연도', label_suffix='', initial=timezone.now().year,
        choices=models.choices.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    exam = forms.ChoiceField(
        label='시험', label_suffix='', initial='5급공채/행정고시',
        choices=models.choices.exam_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
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
        label='합격 예측 종료일', label_suffix='', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    exam_start_time = forms.TimeField(
        label='시험 시작 시각', label_suffix='', initial=time(9, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    exam_finish_time = forms.TimeField(
        label='시험 종료 시각', label_suffix='', initial=time(18, 0),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_predict_open_time = forms.TimeField(
        label='예상 정답 공개 시각', label_suffix='', initial=time(18, 30),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    answer_official_open_time = forms.TimeField(
        label='공식 정답 공개 시각', label_suffix='', initial=time(21, 00),
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


class StudyCategoryForm(forms.Form):
    season = forms.IntegerField(
        label='시즌', label_suffix='', initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    study_type = forms.ChoiceField(
        label='종류', label_suffix='', initial='기본',
        choices=models.choices.study_category_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    name = forms.CharField(
        label='카테고리명', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    category_round = forms.IntegerField(
        label='총 회차수', label_suffix='', initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )


class StudyOrganizationForm(forms.ModelForm):
    class Meta:
        model = models.StudyOrganization
        fields = ['name', 'logo']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudyCurriculumForm(forms.ModelForm):
    class Meta:
        model = models.StudyCurriculum
        fields = ['year', 'organization', 'semester', 'category']
        labels = {
            'organization': '교육기관',
            'category': '카테고리',
        }
        widgets = {
            'year': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = models.StudyOrganization.objects.all()
        self.fields['organization'].label_from_instance = lambda obj: obj.name
        self.fields['category'].queryset = models.StudyCategory.objects.all()
        self.fields['category'].label_from_instance = lambda obj: obj.category_info


class StudyAnswerForm(forms.Form):
    curriculum = forms.ModelChoiceField(
        label='커리큘럼',
        queryset=models.StudyCurriculum.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    file = forms.FileField(label='업로드 파일', widget=forms.FileInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['curriculum'].label_from_instance = lambda obj: obj.curriculum_info


class StudyStudentRegisterForm(forms.Form):
    organization = forms.ChoiceField(
        label='교육기관명', label_suffix='', initial='서울과기대',
        choices=models.choices.study_organization_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    semester = forms.ChoiceField(
        label='학기', label_suffix='', initial=1,
        choices=models.choices.study_semester_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    serial = forms.CharField(
        label='학번(수험번호)', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    name = forms.CharField(
        label='이름', label_suffix='',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data['organization']
        semester = cleaned_data['semester']
        curriculum = models.StudyCurriculum.objects.filter(
            year=timezone.now().year, organization__name=organization, semester=semester)
        if not curriculum.exists():
            self.add_error('organization', '선택한 교육기관명이 맞는지 확인해주세요.')
            self.add_error('semester', '선택한 학기가 맞는지 확인해주세요.')

        return cleaned_data
