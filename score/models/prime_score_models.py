from django.db import models
from django.db.models import F

from common.models import User
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
    user_id = None
    updated_at = None
    round = models.IntegerField()
    serial = models.CharField(max_length=20)
    name = models.CharField(max_length=10)
    password = models.IntegerField()
    department = models.ForeignKey(PrimeDepartment, on_delete=models.CASCADE, related_name='students')

    category = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "수험 정보"
        verbose_name_plural = "수험 정보"

    def __str__(self):
        return f'{self.year}{self.department.exam.abbr}-{self.department}'


class PrimeVerifiedUser(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_verified_users')
    student = models.ForeignKey(PrimeStudent, on_delete=models.CASCADE, related_name='prime_verified_users')


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

    @staticmethod
    def rate_dict(ans_number):
        return {
            'expression': F(f'count_{ans_number}') * 100 / F('count_total'),
            'output_field': models.FloatField(),
            'db_persist': False,
        }

    problem = models.ForeignKey(PrimeProblem, on_delete=models.CASCADE, related_name='answer_counts')
    count_0 = models.IntegerField(default=0)
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=1)
    rate_1 = models.GeneratedField(**rate_dict(1))
    rate_2 = models.GeneratedField(**rate_dict(2))
    rate_3 = models.GeneratedField(**rate_dict(3))
    rate_4 = models.GeneratedField(**rate_dict(4))
    rate_5 = models.GeneratedField(**rate_dict(5))

    class Meta:
        ordering = ['id']
        verbose_name = "답안 개수"
        verbose_name_plural = "답안 개수"


class PrimeStatistics(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    student = models.OneToOneField(PrimeStudent, on_delete=models.CASCADE, related_name='statistics')

    score_eoneo = models.FloatField(null=True, blank=True)
    score_jaryo = models.FloatField(null=True, blank=True)
    score_sanghwang = models.FloatField(null=True, blank=True)
    score_psat = models.FloatField(null=True, blank=True)
    score_psat_avg = models.FloatField(null=True, blank=True)
    score_heonbeob = models.FloatField(null=True, blank=True)

    rank_total_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_total_psat = models.PositiveIntegerField(null=True, blank=True)
    rank_total_heonbeob = models.PositiveIntegerField(null=True, blank=True)

    rank_department_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_department_psat = models.PositiveIntegerField(null=True, blank=True)
    rank_department_heonbeob = models.PositiveIntegerField(null=True, blank=True)

    rank_ratio_total_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_total_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_total_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_total_psat = models.FloatField(null=True, blank=True)
    rank_ratio_total_heonbeob = models.FloatField(null=True, blank=True)

    rank_ratio_department_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_department_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_department_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_department_psat = models.FloatField(null=True, blank=True)
    rank_ratio_department_heonbeob = models.FloatField(null=True, blank=True)
