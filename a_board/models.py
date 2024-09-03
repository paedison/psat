from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy

from common.models import User


class Notice(models.Model):
    CATEGORY_CHOICES = [(1, '일반'), (2, '사용팁')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notices')
    category = models.IntegerField(choices=CATEGORY_CHOICES, default=1, verbose_name='카테고리')
    title = models.CharField(max_length=50, verbose_name='제목')
    content = RichTextUploadingField(verbose_name='내용')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    modified_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    top_fixed = models.BooleanField(default=False, verbose_name='고정글')
    is_hidden = models.BooleanField(default=False, verbose_name='비밀글')

    class Meta:
        verbose_name = verbose_name_plural = "01_공지사항"
        db_table = 'a_board_notice'
        ordering = ["-id"]

    def __str__(self):
        return f'[Board]Notice(#{self.id}):{self.title}'

    @property
    def comment_count(self):
        return self.post_comments.count()

    def get_absolute_url(self):
        return reverse_lazy(f'board:notice-detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy(f'board:notice-list')

    def get_create_url(self):
        return reverse_lazy(f'board:notice-create', args=[self.id])

    def get_update_url(self):
        return reverse_lazy(f'board:notice-update', args=[self.id])

    def get_detail_url(self):
        return reverse_lazy(f'board:notice-detail', args=[self.id])

    def get_delete_url(self):
        return reverse_lazy(f'board:notice-delete', args=[self.id])

    @staticmethod
    def get_comment_list_url():
        return reverse_lazy(f'board:notice-comment-list')

    @staticmethod
    def get_comment_create_url():
        return reverse_lazy(f'board:notice-comment-create')

    @staticmethod
    def get_admin_change_list_url():
        return reverse_lazy(f'admin:a_board_notice_changelist')

    def get_admin_change_url(self):
        return reverse_lazy(f'admin:a_board_notice_change', args=[self.id])

    def get_admin_delete_url(self):
        return reverse_lazy(f'admin:a_board_notice_delete', args=[self.id])

    def update_hit(self):
        self.hit += 1
        self.save()


class NoticeComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notice_comments')
    post = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='post_comments')
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    modified_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = verbose_name_plural = "02_공지사항 댓글"
        db_table = 'a_board_notice_comment'
        ordering = ["-id"]

    def __str__(self):
        return f'[Board]NoticeComment(#{self.id}):{self.user.username}-{self.post.title}'

    @staticmethod
    def get_list_url():
        return reverse_lazy(f'board:notice-list')

    def get_update_url(self):
        return reverse_lazy(f'board:notice-comment-update', args=[self.id])

    def get_delete_url(self):
        return reverse_lazy(f'board:notice-comment-delete', args=[self.id])

    def get_detail_url(self):
        return reverse_lazy(f'board:notice-detail', args=[self.post_id])
