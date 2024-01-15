from django.db import models
from django.db.models import F


class PredictStudent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user_id = models.IntegerField()
    category = models.CharField(max_length=20)  # PSAT, prime
    year = models.IntegerField()
    ex = models.CharField(max_length=2)
    round = models.IntegerField()  # 0 for PSAT, round number for Prime

    serial = models.CharField(max_length=20)
    name = models.CharField(max_length=10)
    password = models.IntegerField()
    department_id = models.IntegerField()

    class Meta:
        verbose_name = "성적 예측 수험 정보"
        verbose_name_plural = "성적 예측 수험 정보"

    def __str__(self):
        if self.round:
            return f'{self.category}-{self.year}{self.ex}{self.round}-{self.department_id}-{self.user_id}'
        else:
            return f'{self.category}-{self.year}{self.ex}-dep{self.department_id}-user{self.user_id}'


class PredictAnswer(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    sub = models.CharField(max_length=2)
    is_confirmed = models.BooleanField(default=False)
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
        verbose_name = "성적 예측 제출 답안"
        verbose_name_plural = "성적 예측 제출 답안"


class PredictAnswerCount(models.Model):

    @staticmethod
    def rate_dict(ans_number):
        return {
            'expression': F(f'count_{ans_number}') * 100 / F('count_total'),
            'output_field': models.FloatField(),
            'db_persist': False,
        }

    category = models.CharField(max_length=20)  # PSAT, prime
    year = models.IntegerField()
    ex = models.CharField(max_length=2)
    round = models.IntegerField(default=0)  # 0 for PSAT, round number for Prime
    sub = models.CharField(max_length=2)
    number = models.IntegerField()
    answer = models.IntegerField(null=True, blank=True)
    count_0 = models.IntegerField(default=0)
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=0)
    rate_1 = models.GeneratedField(**rate_dict(1))
    rate_2 = models.GeneratedField(**rate_dict(2))
    rate_3 = models.GeneratedField(**rate_dict(3))
    rate_4 = models.GeneratedField(**rate_dict(4))
    rate_5 = models.GeneratedField(**rate_dict(5))

    class Meta:
        ordering = ['id']
        verbose_name = "성적 예측 답안 개수"
        verbose_name_plural = "성적 예측 답안 개수"


class PredictStatistics(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='statistics')

    score_heonbeob = models.FloatField(null=True, blank=True)
    score_eoneo = models.FloatField(null=True, blank=True)
    score_jaryo = models.FloatField(null=True, blank=True)
    score_sanghwang = models.FloatField(null=True, blank=True)
    score_psat = models.FloatField(null=True, blank=True)
    score_psat_avg = models.FloatField(null=True, blank=True)

    rank_total_heonbeob = models.PositiveIntegerField(null=True, blank=True)
    rank_total_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_total_psat = models.PositiveIntegerField(null=True, blank=True)

    rank_department_heonbeob = models.PositiveIntegerField(null=True, blank=True)
    rank_department_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_department_psat = models.PositiveIntegerField(null=True, blank=True)

    rank_ratio_total_heonbeob = models.FloatField(null=True, blank=True)
    rank_ratio_total_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_total_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_total_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_total_psat = models.FloatField(null=True, blank=True)

    rank_ratio_department_heonbeob = models.FloatField(null=True, blank=True)
    rank_ratio_department_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_department_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_department_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_department_psat = models.FloatField(null=True, blank=True)
