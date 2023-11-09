from django.db import models

from .base_models import TestBase, ProblemBase


class Prime(TestBase):
    # Parent[TestBase] fields: year, exam, subject
    round = models.IntegerField()

    # def __str__(self):
    #     return f'{self.year}-{self.round:02}{self.exam.abbr}{self.subject.abbr}'


class PrimeProblem(ProblemBase):
    # Parent[ProblemBase] fields: number, answer
    prime = models.ForeignKey(Prime, on_delete=models.CASCADE, related_name='prime_problems')

    url_name = 'prime_v2:detail'

    class Meta:
        ordering = ['-prime__year', 'id']

    # def __str__(self):
    #     return f'{self.prime.year}-{self.prime.round:02}{self.prime.subject.abbr}-{self.number:02}'
