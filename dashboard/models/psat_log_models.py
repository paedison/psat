from django.db import models

from .base_models import PsatBase


class PsatOpenLog(PsatBase):
    ip_address = models.TextField(blank=True, null=True)


class PsatLikeLog(PsatBase):
    is_liked = models.BooleanField()


class PsatRateLog(PsatBase):
    rating = models.IntegerField()


class PsatSolveLog(PsatBase):
    answer = models.IntegerField()
    is_correct = models.BooleanField()
