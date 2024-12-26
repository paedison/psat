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


class PrimeResultStudentForm(forms.ModelForm):
    class Meta:
        model = models.ResultStudent
        fields = ['serial', 'name', 'password']
        widgets = {
            'serial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '수험번호'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
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
        choices=models.choices.department_choices(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='직렬',
        required=True,
    )

    class Meta:
        model = models.PredictStudent
        fields = ['serial', 'name', 'password']
        widgets = {
            'serial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '수험번호'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
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
