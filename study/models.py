from django.db import models

from psat.models import Problem


class QuestionInfo(models.Model):
    class ChapterChoices(models.IntegerChoices):
        FIRST = 1, '미니테스트 1회'
        SECOND = 2, '미니테스트 2회'
        THIRD = 3, '미니테스트 3회'
        FOURTH = 4, '미니테스트 4회'
        FIFTH = 5, '미니테스트 5회'
        SIXTH = 6, '미니테스트 6회'
        SEVENTH = 7, '미니테스트 7회'
        EIGHTH = 8, '미니테스트 8회'
        NINTH = 9, '미니테스트 9회'
        TENTH = 10, '미니테스트 10회'
        ELEVENTH = 11, '미니테스트 11회'
        TWELFTH = 12, '미니테스트 12회'
        THIRTEENTH = 13, '미니테스트 13회'
        FOURTEENTH = 14, '미니테스트 14회'
        FIFTEENTH = 15, '미니테스트 15회'
        SIXTEENTH = 16, '미니테스트 16회'
        SEVENTEENTH = 17, '실전모의고사 1회'
        EIGHTEENTH = 18, '실전모의고사 2회'

    chapter = models.PositiveSmallIntegerField(choices=ChapterChoices.choices)
    question_num = models.PositiveSmallIntegerField()
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)ss')

    class Meta:
        abstract = True
        ordering = ['chapter', 'question_num']


class AlphaQuestion(QuestionInfo):
    pass


class BetaQuestion(QuestionInfo):
    pass
