from django.db import models

from reference.models.base_models import Exam
from reference.models.prime_models import PrimeProblem, Prime
from score.models.base_models import UnitBase, StudentBase, AnswerBase


class PrimeDepartment(UnitBase):
    # Parent[UnitBase] fields: name
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='prime_units')

    class Meta:
        verbose_name = "직렬"
        verbose_name_plural = "직렬"

    def __str__(self):
        return self.name


class PrimeStudent(StudentBase):
    # Parent-Parent[InfoBase] fields: timestamp, updated_at, user_id
    # Parent[StudentBase] fields: year, serial
    updated_at = None
    round = models.IntegerField()
    name = models.CharField(max_length=10)
    password = models.IntegerField()
    department = models.ForeignKey(PrimeDepartment, on_delete=models.CASCADE, related_name='students')

    eoneo_score = models.FloatField(default=0)
    jaryo_score = models.FloatField(default=0)
    sanghwang_score = models.FloatField(default=0)
    psat_score = models.FloatField(default=0)
    heonbeob_score = models.FloatField(default=0)

    user_id = models.IntegerField(default=0)

    class Meta:
        verbose_name = "수험 정보"
        verbose_name_plural = "수험 정보"

    def __str__(self):
        return f'{self.year}{self.department.exam.abbr}-{self.department}-{self.user_id}'

    def average(self) -> float: return self.psat_score / 3


class PrimeAnswer(AnswerBase):
    # Parent-Parent[InfoBase] fields: timestamp, updated_at, user_id
    # Parent[AnswerBase] fields: answer
    updated_at = None
    user_id = None
    answer = None
    prime = models.ForeignKey(Prime, on_delete=models.CASCADE, related_name='prime_answers')
    student = models.ForeignKey(PrimeStudent, on_delete=models.CASCADE, related_name='student_answers')
    prob1 = models.IntegerField(blank=True, null=True)
    prob2 = models.IntegerField(blank=True, null=True)
    prob3 = models.IntegerField(blank=True, null=True)
    prob4 = models.IntegerField(blank=True, null=True)
    prob5 = models.IntegerField(blank=True, null=True)
    prob6 = models.IntegerField(blank=True, null=True)
    prob7 = models.IntegerField(blank=True, null=True)
    prob8 = models.IntegerField(blank=True, null=True)
    prob9 = models.IntegerField(blank=True, null=True)
    prob10 = models.IntegerField(blank=True, null=True)
    prob11 = models.IntegerField(blank=True, null=True)
    prob12 = models.IntegerField(blank=True, null=True)
    prob13 = models.IntegerField(blank=True, null=True)
    prob14 = models.IntegerField(blank=True, null=True)
    prob15 = models.IntegerField(blank=True, null=True)
    prob16 = models.IntegerField(blank=True, null=True)
    prob17 = models.IntegerField(blank=True, null=True)
    prob18 = models.IntegerField(blank=True, null=True)
    prob19 = models.IntegerField(blank=True, null=True)
    prob20 = models.IntegerField(blank=True, null=True)
    prob21 = models.IntegerField(blank=True, null=True)
    prob22 = models.IntegerField(blank=True, null=True)
    prob23 = models.IntegerField(blank=True, null=True)
    prob24 = models.IntegerField(blank=True, null=True)
    prob25 = models.IntegerField(blank=True, null=True)
    prob26 = models.IntegerField(blank=True, null=True)
    prob27 = models.IntegerField(blank=True, null=True)
    prob28 = models.IntegerField(blank=True, null=True)
    prob29 = models.IntegerField(blank=True, null=True)
    prob30 = models.IntegerField(blank=True, null=True)
    prob31 = models.IntegerField(blank=True, null=True)
    prob32 = models.IntegerField(blank=True, null=True)
    prob33 = models.IntegerField(blank=True, null=True)
    prob34 = models.IntegerField(blank=True, null=True)
    prob35 = models.IntegerField(blank=True, null=True)
    prob36 = models.IntegerField(blank=True, null=True)
    prob37 = models.IntegerField(blank=True, null=True)
    prob38 = models.IntegerField(blank=True, null=True)
    prob39 = models.IntegerField(blank=True, null=True)
    prob40 = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "제출 답안"
        verbose_name_plural = "제출 답안"


class PrimeAnswerCount(models.Model):
    problem = models.ForeignKey(PrimeProblem, on_delete=models.CASCADE, related_name='answer_counts')
    count_0 = models.IntegerField(default=0)
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']
        verbose_name = "답안 개수"
        verbose_name_plural = "답안 개수"

    @property
    def count_correct(self):
        answer_dict = {
            '0': self.count_0,
            '1': self.count_1,
            '2': self.count_2,
            '3': self.count_3,
            '4': self.count_4,
            '5': self.count_5,
        }
        correct_answer = self.problem.answer
        return answer_dict[correct_answer]

    @property
    def answer_1_rate(self): return self.count_1 / self.count_total
    @property
    def answer_2_rate(self): return self.count_2 / self.count_total
    @property
    def answer_3_rate(self): return self.count_3 / self.count_total
    @property
    def answer_4_rate(self): return self.count_4 / self.count_total
    @property
    def answer_5_rate(self): return self.count_5 / self.count_total
    @property
    def correctness_rate(self): return self.count_correct / self.count_total