from django import forms
from django.utils import timezone

from a_psat import models
from common.utils import get_local_time


class StudyCategoryForm(forms.Form):
    season = forms.IntegerField(
        label='시즌', initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    study_type = forms.ChoiceField(
        label='종류', initial='기본', choices=models.choices.study_category_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    name = forms.CharField(label='카테고리명', widget=forms.TextInput(attrs={'class': 'form-control'}))
    category_round = forms.IntegerField(
        label='총 회차수', initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))


class StudyOrganizationForm(forms.ModelForm):
    class Meta:
        model = models.StudyOrganization
        fields = ['name', 'logo']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudyStudentCreateForm(forms.ModelForm):
    class Meta:
        model = models.StudyStudent
        fields = ['curriculum', 'serial', 'name']
        widgets = {
            'curriculum': forms.Select(attrs={'class': 'form-select'}),
            'serial': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StudyCurriculumForm(forms.Form):
    hx_request_attrs = {
        'class': 'form-select',
        'hx-trigger': 'change',
        'hx-headers': '{"View-Type": "category"}',
        'hx-target': '#id_category_container',
        'hx-swap': 'outerHTML swap:0.25s',
        'hx-post': '',
    }
    year = forms.ChoiceField(
        label='연도', initial=timezone.now().year, choices=models.choices.year_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    organization = forms.ModelChoiceField(
        label='교육기관', initial='서울과기대', queryset=models.StudyOrganization.objects.all(),
        widget=forms.Select(attrs=hx_request_attrs),
    )
    semester = forms.ChoiceField(
        label='학기', initial=1, choices=models.choices.study_semester_choice,
        widget=forms.Select(attrs=hx_request_attrs),
    )
    category = forms.ModelChoiceField(
        label='카테고리', initial='시즌02심화', queryset=models.StudyCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    lecture_start_date = forms.DateField(
        label='강의 시작일', initial=timezone.now(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    lecture_start_time = forms.TimeField(
        label='강의 시작시간', initial='10:00',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
    )
    lecture_nums = forms.IntegerField(
        label='강의 차수', initial=16,
        widget=forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        lecture_start_date = cleaned_data['lecture_start_date']
        lecture_start_time = cleaned_data['lecture_start_time']
        cleaned_data['lecture_start_datetime'] = get_local_time(lecture_start_date, lecture_start_time)

        return cleaned_data


class StudyCurriculumCategoryForm(forms.Form):
    category = forms.ModelChoiceField(
        label='카테고리', initial='시즌02심화', queryset=models.StudyCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


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
        label='교육기관명', initial='서울과기대',
        choices=models.choices.study_student_register_organization_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    semester = forms.ChoiceField(
        label='학기', initial=1, choices=models.choices.study_semester_choice,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    serial = forms.CharField(label='학번(수험번호)', widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label='이름', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data['organization']
        semester = cleaned_data['semester']
        try:
            cleaned_data['curriculum'] = models.StudyCurriculum.objects.get(
                year=timezone.now().year, organization__name=organization, semester=semester)
        except models.StudyCurriculum.DoesNotExist:
            self.add_error('organization', '선택한 교육기관명이 맞는지 확인해주세요.')
            self.add_error('semester', '선택한 학기가 맞는지 확인해주세요.')
        return cleaned_data
