from django.db import models

from common.models import User

CATEGORY_CHOICES = [
    (1, '일반'),
    (2, '사용팁'),
]


class Post(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    category = models.IntegerField("카테고리", choices=CATEGORY_CHOICES)
    title = models.CharField("제목", max_length=50)
    content = models.TextField("내용")
    hit = models.IntegerField("조회수", default=1)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)
    top_fixed = models.BooleanField("상단 고정", null=True)

    class Meta:
        ordering = ["-id"]


class Comment(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자 ID", db_column="user_id")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="게시글", db_column="post_id")
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    modified_at = models.DateTimeField("수정일", auto_now=True)
