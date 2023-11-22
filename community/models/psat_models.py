from django.db import models

from .base_models import Base


class Category(models.Model):
    name = models.CharField(max_length=128)


class Post(Base):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='posts', verbose_name='카테고리')
    title = models.CharField(max_length=50, verbose_name='제목')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    top_fixed = models.BooleanField(default=False, verbose_name='상단 고정')
    is_hidden = models.BooleanField(default=False, verbose_name='비밀글')

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Comment(Base):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments', verbose_name='게시글')

    class Meta:
        ordering = ["-id"]
