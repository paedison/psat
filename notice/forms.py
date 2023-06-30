from django import forms
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

from notice.models import Post, Comment


# Apply summernote to specific fields.
class SomeForm(forms.Form):
    foo = forms.CharField(widget=SummernoteWidget())  # instead of forms.Textarea


# If you don't like <iframe>, then use inplace widget
# Or if you're using django-crispy-forms, please use this.
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['category', 'title', 'content', 'top_fixed']
        widgets = {
            'content': SummernoteWidget(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
