from django import forms

from . import models


class NoticeForm(forms.ModelForm):
    title = forms.CharField(
        label='제목', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목'}))
    top_fixed = forms.BooleanField(
        label='상단 고정', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_hidden = forms.BooleanField(
        label='비밀글', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = models.Notice
        fields = ['title', 'content', 'top_fixed', 'is_hidden']


class NoticeCommentCreateForm(forms.ModelForm):
    class Meta:
        model = models.NoticeComment
        fields = ['post', 'content']


class NoticeCommentUpdateForm(forms.ModelForm):
    class Meta:
        model = models.NoticeComment
        fields = ['content']
