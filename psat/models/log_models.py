from django.db import models

from .base_models import LogBase
from .data_models import Ratings, Answers, Open, Like, Rate, Solve


class OpenLog(LogBase):
    data_id = models.ForeignKey(Open, on_delete=models.CASCADE, related_name='logs')


class LikeLog(LogBase):
    data_id = models.ForeignKey(Like, on_delete=models.CASCADE, related_name='logs')
    is_liked = models.BooleanField()


class RateLog(LogBase):
    data_id = models.ForeignKey(Rate, on_delete=models.CASCADE, related_name='logs')
    rating = models.IntegerField(choices=Ratings.choices)


class SolveLog(LogBase):
    data_id = models.ForeignKey(Solve, on_delete=models.CASCADE, related_name='logs')
    answer = models.IntegerField(choices=Answers.choices)
    is_correct = models.BooleanField()
