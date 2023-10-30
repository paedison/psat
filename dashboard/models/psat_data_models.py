from django.db import models

from .base_models import PsatBase


class PsatOpenLog(PsatBase):
    pass


class PsatLikeLog(PsatBase):
    is_liked = models.BooleanField()


class PsatRateLog(PsatBase):
    rating = models.IntegerField()


class PsatSolveLog(PsatBase):
    answer = models.IntegerField()
    is_correct = models.BooleanField()
