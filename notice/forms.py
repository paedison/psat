from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['user', 'category', 'title', 'content', 'top_fixed', 'is_hidden']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['user', 'post', 'content']
