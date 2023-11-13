from django.db import models


class UnitBase(models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        abstract = True
        ordering = ['id']


class InfoBase(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ['id']


class StudentBase(InfoBase):
    # Parent[Infobase] fields: timestamp, update_at, user_id
    year = models.IntegerField()
    serial = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['id']


class AnswerBase(InfoBase):
    # Parent[Infobase] fields: timestamp, update_at, user_id
    answer = models.IntegerField("제출 답안")

    class Meta:
        abstract = True
        ordering = ['id']
