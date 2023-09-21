from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy

from common.models import User


class PostInfo:
    app_name = 'notice'
    id: int
    hit: int
    post_comments: any

    def get_absolute_url(self): return reverse_lazy(f'{self.app_name}:detail', args=[self.id])
    @property
    def post_detail_url(self): return reverse_lazy(f'{self.app_name}:detail', args=[self.id])
    @property
    def post_detail_content_url(self): return reverse_lazy(f'{self.app_name}:detail_content', args=[self.id])
    @property
    def post_list_url(self): return reverse_lazy(f'{self.app_name}:list')
    @property
    def post_list_navigation_url(self): return reverse_lazy(f'{self.app_name}:list_navigation')
    @property
    def post_update_url(self): return reverse_lazy(f'{self.app_name}:update', args=[self.id])
    @property
    def post_update_content_url(self): return reverse_lazy(f'{self.app_name}:update_content', args=[self.id])
    @property
    def post_delete_url(self): return reverse_lazy(f'{self.app_name}:delete', args=[self.id])
    @property
    def comment_create_url(self): return reverse_lazy(f'{self.app_name}:comment_create', args=[self.id])

    @property
    def comment_count(self): return self.post_comments.count()

    def update_hit(self):
        hit = self.hit
        self.hit = hit + 1
        self.save()


class CommentInfo:
    app_name = 'notice'
    id: int
    post: any

    @property
    def comment_update_url(self):
        return reverse_lazy(f'{self.app_name}:comment_update',
                            kwargs={'post_id': self.post.id, 'comment_id': self.id})

    @property
    def comment_delete_url(self):
        return reverse_lazy(f'{self.app_name}:comment_delete',
                            kwargs={'post_id': self.post.id, 'comment_id': self.id})

    @property
    def post_detail_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.post.id])


class Post(PostInfo, models.Model):
    CATEGORY_CHOICES = [
        (1, '일반'),
        (2, '사용팁'),
        (3, '공부법'),
    ]

    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    category = models.IntegerField(
        "카테고리", choices=CATEGORY_CHOICES, default=1)
    title = models.CharField("제목", max_length=50)
    content = RichTextUploadingField()
    hit = models.IntegerField("조회수", default=1)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)
    top_fixed = models.BooleanField("상단 고정", default=False)
    is_hidden = models.BooleanField("비밀글", default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Comment(CommentInfo, models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자 ID",
        db_column="user_id", related_name="user_comments")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, verbose_name="게시글",
        db_column="post_id", related_name="post_comments")
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ["-id"]
