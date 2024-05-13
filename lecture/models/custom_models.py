from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from common.models import User
from . import base_models, lecture_models


class Memo(base_models.Base):
    memo = RichTextField(config_name='minimal')


class Tag(base_models.Base):
    tags = TaggableManager(related_name='lecture_tags')

    class Meta:
        verbose_name = _("Tagged lecture")
        verbose_name_plural = _("Tagged lectures")
        unique_together = [["user_id", "lecture"]]


class Comment(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_comments')
    lecture = models.ForeignKey(lecture_models.Lecture, on_delete=models.CASCADE, related_name='comments')
    title = models.TextField(max_length=100)
    comment = RichTextField(config_name='minimal')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        sub = self.lecture.subject.abbr
        order = self.lecture.order
        return f'{sub}{order}-Comment#{self.id}(User#{self.user_id})'

    def get_absolute_url(self):
        return reverse_lazy('lecture:comment_container', args=[self.lecture_id])
