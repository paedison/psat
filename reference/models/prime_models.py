from django.db import models

from .base_models import TestBase, ProblemBase


class Prime(TestBase):
    # Parent[TestBase] fields: year, exam, subject
    round = models.IntegerField()


class PrimeProblem(ProblemBase):
    # Parent[ProblemBase] fields: number, answer
    prime = models.ForeignKey(Prime, on_delete=models.CASCADE, related_name='prime_problems')

    class Meta:
        ordering = ['-prime__year', 'id']
