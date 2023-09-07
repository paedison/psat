from django.db import models

from common.models import User
from psat.models import Problem


class TemporaryAnswer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, verbose_name="사용자 ID", default=1)
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, verbose_name="문제 ID")
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_confirmed = models.BooleanField("확정 여부", default=False)


class ConfirmedAnswer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, verbose_name="사용자 ID", default=1)
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, verbose_name="문제 ID")
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_times = models.IntegerField("확정 횟수", default=1)
