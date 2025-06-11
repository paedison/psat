__all__ = [
    'Lecture', 'LectureTag', 'LectureTaggedItem',
    'LectureOpen', 'LectureLike', 'LectureMemo', 'LectureComment',
]

from datetime import datetime

import pytz
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from taggit.models import TagBase, TaggedItemBase

from a_psat.models import choices
from a_psat.models.queryset import lecture_queryset as queryset
from common.models import User


def get_remarks(message_type: str, remarks: str | None) -> str:
    utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
    separator = '|' if remarks else ''
    if remarks:
        remarks += f"{separator}{message_type}_at:{utc_now}"
    else:
        remarks = f"{message_type}_at:{utc_now}"
    return remarks


class LectureTag(TagBase):
    objects = queryset.LectureTagQuerySet.as_manager()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 05_태그"
        db_table = 'a_psat_lecture_tag'

    def __str__(self):
        return f'[PSAT]LectureTag(#{self.id}):{self.name}'


class LectureTaggedItem(TaggedItemBase):
    objects = queryset.LectureTaggedItemQuerySet.as_manager()
    tag = models.ForeignKey(LectureTag, on_delete=models.CASCADE, related_name="tagged_items")
    content_object = models.ForeignKey('Lecture', on_delete=models.CASCADE, related_name='tagged_lectures')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_tagged_lectures')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 06_태그된 강의"
        db_table = 'a_psat_lecture_tagged_item'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'content_object', 'user'],
                name='unique_psat_lecture_tagged_item',
            )
        ]

    def __str__(self):
        return f'[PSAT]LectureTaggedItem(#{self.id}):[{self.tag.name}]{self.content_object.reference}({self.user.username})'

    @property
    def tag_name(self):
        return self.tag.name

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'tagged')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)

    @property
    def reference(self):
        return self.content_object.reference


class Lecture(models.Model):
    objects = queryset.LectureQuerySet.as_manager()
    subject = models.CharField(max_length=2, choices=choices.lecture_subject_choice, default='언어')
    title = models.CharField(max_length=20, null=True, blank=True)
    sub_title = models.CharField(max_length=50, null=True, blank=True)
    youtube_id = models.CharField(max_length=20, null=True, blank=True)
    content = RichTextUploadingField(default='')
    order = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 01_강의"
        ordering = ['subject', 'order']
        db_table = 'a_psat_lecture'

    def __str__(self):
        return f'[Lecture]Psat(#{self.id}):{self.reference}'

    @property
    def youtube_url(self):
        if self.youtube_id:
            return f'https://youtu.be/{self.youtube_id}'

    @property
    def thumbnail_url(self):
        if self.youtube_id:
            return f'https://img.youtube.com/vi/{self.youtube_id}/maxresdefault.jpg'

    @property
    def embed_src(self):
        if self.youtube_id:
            return f'https://www.youtube.com/embed/{self.youtube_id}'

    @property
    def reference(self):
        return f'{self.subject}{self.order:02}-{self.title}'

    def get_memo_url(self):
        return reverse_lazy('psat:memo-lecture', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('psat:tag-lecture', args=[self.id])

    @staticmethod
    def get_lecture_list_url():
        return reverse_lazy('psat:lecture-list')

    def get_lecture_detail_url(self):
        return reverse_lazy('psat:lecture-detail', args=[self.id])


class LectureOpen(models.Model):
    objects = queryset.LectureOpenQuerySet.as_manager()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_lecture_opens')
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'[PSAT]LectureOpen(#{self.id}):{self.lecture.reference}({self.user.username})'

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 02_확인기록"
        db_table = 'a_psat_lecture_open'


class LectureLike(models.Model):
    objects = queryset.LectureLikeQuerySet.as_manager()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_lecture_likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.is_liked:
            return f'[PSAT]LectureLike(#{self.id}):{self.lecture.reference}(Liked, {self.user.username})'
        return f'[PSAT]LectureLike(#{self.id}):{self.lecture.reference}(Unliked, {self.user.username})'

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 03_즐겨찾기"
        ordering = ['-id']
        db_table = 'a_psat_lecture_like'
        constraints = [
            models.UniqueConstraint(fields=['user', 'lecture'], name='unique_psat_lecture_like'),
        ]

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'liked')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class LectureMemo(models.Model):
    objects = queryset.LectureMemoQuerySet.as_manager()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_memos')
    content = RichTextField(config_name='minimal')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "[온라인강의] 04_메모"
        db_table = 'a_psat_lecture_memo'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'lecture'],
                name='unique_psat_lecture_memo',
            )
        ]

    def __str__(self):
        return f'[PSAT]LectureMemo(#{self.id}):{self.lecture.reference}({self.user.username})'

    def get_memo_url(self):
        return reverse_lazy('psat:memo-lecture', args=[self.lecture_id])


class LectureComment(models.Model):
    objects = queryset.LectureCommentQuerySet.as_manager()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_lecture_comments')
    content = RichTextField(config_name='minimal')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'a_psat_lecture_comment'
        ordering = ['-id']

    def __str__(self):
        return f'[PSAT]LectureComment(#{self.id}):{self.lecture.reference}({self.user.username})'

    # def get_absolute_url(self):
    #     return reverse_lazy('lecture:comment_container', args=[self.lecture_id])
