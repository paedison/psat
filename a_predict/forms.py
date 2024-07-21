from django import forms

from .models import PsatStudent, PoliceStudent


class PsatStudentForm(forms.ModelForm):
    serial = forms.CharField(
        label='수험번호',
        label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '수험번호'}),
        error_messages={'required': '수험번호를 입력해주세요.'},
    )
    name = forms.CharField(
        label='이름',
        label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '이름'}),
        error_messages={'required': '이름을 입력해주세요.'},
    )

    class Meta:
        model = PsatStudent
        fields = ['unit', 'department', 'serial', 'name', 'password', 'prime_id']
        error_messages = {
            'department': {'required': '모집 단위 및 직렬을 선택해주세요.'},
        }


class PoliceStudentForm(forms.ModelForm):
    selection = forms.CharField(
        label='선택과목',
        label_suffix='',
        widget=forms.Select(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '선택과목'}),
        error_messages={'required': '선택과목을 선택해주세요.'},
    )
    serial = forms.CharField(
        label='수험번호',
        label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '수험번호'}),
        error_messages={'required': '수험번호를 입력해주세요.'},
    )
    name = forms.CharField(
        label='이름',
        label_suffix='',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '이름'}),
        error_messages={'required': '이름을 입력해주세요.'},
    )

    class Meta:
        model = PoliceStudent
        fields = ['selection', 'serial', 'name', 'prime_id']
        error_messages = {
            'department': {'required': '모집 단위 및 직렬을 선택해주세요.'},
        }


class UploadAnswerOfficialFileForm(forms.Form):
    file = forms.FileField(
        label='',
        label_suffix='',
        widget=forms.FileInput(
            attrs={'class': 'form-control'}),
    )
