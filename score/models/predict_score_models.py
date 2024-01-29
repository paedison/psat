from django.db import models

from score.models.base_models import StatisticsBase, AnswerCountBase


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
            return (f'[PredictStudent#{self.id}]{self.category}-{self.year}{self.ex}{self.round}'
                    f'-dep{self.department_id}-user{self.user_id}')
        else:
            return (f'[PredictStudent#{self.id}]{self.category}-{self.year}{self.ex}'
                    f'-dep{self.department_id}-user{self.user_id}')


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

    def __str__(self):
        if self.student.round:
            return (f'[PredictAnswer#{self.id}]{self.student.category}'
                    f'-{self.student.year}{self.student.ex}{self.student.round}{self.sub}'
                    f'-dep{self.student.department_id}-user{self.student.user_id}')
        else:
            return (f'[PredictAnswer#{self.id}]{self.student.category}'
                    f'-{self.student.year}{self.student.ex}{self.sub}'
                    f'-dep{self.student.department_id}-user{self.student.user_id}')


class PredictAnswerCount(AnswerCountBase):
    category = models.CharField(max_length=20)  # PSAT, prime
    year = models.IntegerField()
    ex = models.CharField(max_length=2)
    round = models.IntegerField(default=0)  # 0 for PSAT, round number for Prime
    sub = models.CharField(max_length=2)
    number = models.IntegerField()
    answer = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "성적 예측 답안 개수"
        verbose_name_plural = "성적 예측 답안 개수"

    def __str__(self):
        if self.round:
            return (f'[PredictAnswerCount#{self.id}]{self.category}'
                    f'-{self.year}{self.ex}{self.round}{self.sub}')
        else:
            return (f'[PredictStudent#{self.id}]{self.category}'
                    f'-{self.year}{self.ex}{self.sub}')


class PredictStatistics(StatisticsBase):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='statistics')

    def __str__(self):
        if self.student.round:
            return (f'[PredictStatistics#{self.id}]{self.student.category}'
                    f'-{self.student.year}{self.student.ex}{self.student.round}'
                    f'-dep{self.student.department_id}-user{self.student.user_id}')
        else:
            return (f'[PredictStatistics#{self.id}]{self.student.category}'
                    f'-{self.student.year}{self.student.ex}'
                    f'-dep{self.student.department_id}-user{self.student.user_id}')


class PredictStatisticsVirtual(StatisticsBase):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='statistics_virtual')
