# Django Core Import
from django import forms

# Custom App Import
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['user', 'category', 'title', 'content', 'top_fixed']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
