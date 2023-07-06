from django.db import models
from django.urls import reverse_lazy

from common.models import User

CATEGORY_CHOICES = [
    (1, '일반'),
    (2, '사용팁'),
]

app_name = 'notice'


class Post(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    category = models.IntegerField("카테고리", choices=CATEGORY_CHOICES, default=1)
    title = models.CharField("제목", max_length=50)
    content = models.TextField("내용")
    hit = models.IntegerField("조회수", default=1)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)
    top_fixed = models.BooleanField("상단 고정", default=False)

    class Meta:
        ordering = ["-id"]

    def get_absolute_url(self):
        return reverse_lazy(f'{app_name}:detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy(f'{app_name}:list')

    @staticmethod
    def get_create_url():
        return reverse_lazy(f'{app_name}:create')

    def get_update_url(self):
        return reverse_lazy(f'{app_name}:update', args=[self.id])

    def get_delete_url(self):
        return reverse_lazy(f'{app_name}:delete', args=[self.id])

    def get_create_comment_url(self):
        return reverse_lazy(f'{app_name}:comment_create', args=[self.id])

    def get_comment_count(self):
        return self.comment.count()


class Comment(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="게시글", db_column="post_id", related_name="comment")
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ["-id"]

    def get_comment_update_url(self):
        return reverse_lazy(f'{app_name}:comment_update', args=[self.id])

    def get_comment_delete_url(self):
        return reverse_lazy(f'{app_name}:comment_delete', args=[self.id])
