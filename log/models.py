# Django Core Import
from django.db import models

# Custom App Import
from common.models import User
from psat.models import Problem

DIFFICULTY_CHOICES = [
    (1, '⭐️'),
    (2, '⭐️⭐️'),
    (3, '⭐️⭐️⭐️'),
    (4, '⭐️⭐️⭐️⭐️'),
    (5, '⭐️⭐️⭐️⭐️⭐️'),
]


class AccountLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    log_url = models.URLField()
    log_content = models.TextField()

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id} &raquo; {self.log_content}'


class RequestLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    log_url = models.URLField()
    log_content = models.TextField()

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id} &raquo; {self.log_content}'


class ProblemLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, verbose_name="문제 ID", db_column="problem_id")

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id}, Problem:{self.problem.full_title()}, Opened'


class LikeLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", null=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, verbose_name="문제 ID", db_column="problem_id")
    is_liked = models.BooleanField("추천 여부")

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id}, Problem:{self.problem.full_title()}, Is_liked:{self.is_liked}'


class RateLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", null=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, verbose_name="문제 ID", db_column="problem_id")
    difficulty_rated = models.IntegerField("평가 난이도", choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id}, Problem:{self.problem.full_title()}, Is_liked:{self.is_liked}'


class AnswerLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="사용자 ID", db_column="user_id", null=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, verbose_name="문제 ID", db_column="problem_id")
    submitted_answer = models.IntegerField("제출 정답")
    is_correct = models.BooleanField("정오 여부")

    def __str__(self):
        return f'{self.timestamp}(User ID:{self.id}, Problem:{self.problem.full_title()}, Is_liked:{self.is_liked}'
