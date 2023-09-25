from django.db import models

from common.models import User
from psat.models import Problem


class TemporaryAnswer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자 ID")
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        related_name='temporary_answers', verbose_name="문제 ID")
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']


class ConfirmedAnswer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="사용자 ID")
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        related_name='confirmed_answers', verbose_name="문제 ID")
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_times = models.IntegerField("확정 횟수", default=1)

    class Meta:
        ordering = ['id']


class DummyAnswer(models.Model):
    user = models.IntegerField()
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        related_name='dummy_answers', verbose_name="문제 ID")
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_times = models.IntegerField("확정 횟수", default=1)

    class Meta:
        ordering = ['id']


class AnswerCount(models.Model):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        related_name='answer_counts', verbose_name="문제 ID")
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']

    @property
    def count_correct(self):
        answer_dict = {
            '1': self.count_1,
            '2': self.count_2,
            '3': self.count_3,
            '4': self.count_4,
            '5': self.count_5,
        }
        correct_answer = self.problem.answer
        return answer_dict[correct_answer]

    @property
    def answer_1_rate(self): return self.count_1 / self.count_total
    @property
    def answer_2_rate(self): return self.count_2 / self.count_total
    @property
    def answer_3_rate(self): return self.count_3 / self.count_total
    @property
    def answer_4_rate(self): return self.count_4 / self.count_total
    @property
    def answer_5_rate(self): return self.count_5 / self.count_total
    @property
    def correctness_rate(self): return self.count_correct / self.count_total
