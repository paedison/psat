# Django Core Import
from django.db import models

# Custom App Import
from common.models import User
from psat.models import Problem, Evaluation

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_column="user_id", blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    log_url = models.TextField()
    log_content = models.TextField()

    def __str__(self):
        return f'{self.timestamp}(User {self.user.id} &raquo; {self.log_content}'


class RequestLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_column="user_id", blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    log_url = models.TextField()
    log_content = models.TextField()

    def __str__(self):
        return f'{self.timestamp}(User {self.user.id} &raquo; {self.log_content}'


class ProblemLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.SET_NULL, db_column="evaluation_id", blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    session_key = models.TextField(blank=True, null=True)
    problem_id = models.IntegerField()

    def __str__(self):
        return f'{self.timestamp}(User {self.user_id} - {self.evaluation.full_title()} &raquo; Opened'


class LikeLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.SET_NULL, db_column="evaluation_id", blank=True, null=True)
    user_id = models.IntegerField()
    problem_id = models.IntegerField()
    is_liked = models.BooleanField()

    def __str__(self):
        return f'{self.timestamp}(User {self.user_id} - {self.evaluation.full_title()} &raquo; Is liked:{self.is_liked}'


class RateLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.SET_NULL, db_column="evaluation_id", blank=True, null=True)
    user_id = models.IntegerField()
    problem_id = models.IntegerField()
    difficulty_rated = models.IntegerField(choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return f'{self.timestamp}(User {self.user_id} - {self.evaluation.full_title()} &raquo; Difficulty rated:{self.difficulty_rated}'


class AnswerLog(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.SET_NULL, db_column="evaluation_id", blank=True, null=True)
    user_id = models.IntegerField()
    problem_id = models.IntegerField()
    submitted_answer = models.IntegerField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f'{self.timestamp}(User {self.user_id} - {self.evaluation.full_title()} &raquo; Submitted answer:{self.submitted_answer}, Is correct:{self.is_correct}'
