from django.db import models

from reference.models import PsatProblem


class Base(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField()
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='%(class)ss')

    class Meta:
        abstract = True
        ordering = ['-id']

    def __str__(self):
        return f'{self.problem.psat.year}{self.problem.psat.exam.abbr}{self.problem.psat.subject.abbr}-{self.problem.number:02}({self.user_id})'


class LogBase(Base):
    session_key = models.TextField(blank=True, null=True)
    repetition = models.IntegerField()

    class Meta:
        abstract = True
