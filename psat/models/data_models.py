from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from .base_models import Base


class Ratings(models.IntegerChoices):
    STAR1 = 1, '⭐️'
    STAR2 = 2, '⭐️⭐️'
    STAR3 = 3, '⭐️⭐️⭐️'
    STAR4 = 4, '⭐️⭐️⭐️⭐️'
    STAR5 = 5, '⭐️⭐️⭐️⭐️⭐️'


class Answers(models.IntegerChoices):
    ANSWER1 = 1, '①'
    ANSWER2 = 2, '②'
    ANSWER3 = 3, '③'
    ANSWER4 = 4, '④'
    ANSWER5 = 5, '⑤'


class Open(Base):
    user_id = models.IntegerField(blank=True, null=True)
    ip_address = models.TextField(blank=True, null=True)


class Like(Base):
    is_liked = models.BooleanField()


class Rate(Base):
    rating = models.IntegerField(choices=Ratings.choices)


class Solve(Base):
    answer = models.IntegerField(choices=Answers.choices)
    is_correct = models.BooleanField()


class Memo(Base):
    content = models.TextField("내용")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user_id", "problem"]]


class Tag(Base):
    tags = TaggableManager()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tagged problem")
        verbose_name_plural = _("Tagged problems")
        unique_together = [["user_id", "problem"]]
