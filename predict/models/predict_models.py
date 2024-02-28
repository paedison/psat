import os

from django.conf import settings
from django.db import models
from django.utils import timezone

from . import base_models

CATEGORY_CHOICES = {
    'PSAT': 'PSAT',
    'Prime': '프라임',
}
EX_CHOICES = {
    '행시': '5급공채',
    '입시': '입법고시',
    '칠급': '7급공채',
    '민경': '민간경력',
    '프모': '프라임 모의고사',
}
SUB_CHOICES = {
    '헌법': '헌법',
    '언어': '언어논리',
    '자료': '자료해석',
    '상황': '상황판단',
}
data_dir = os.path.join(settings.BASE_DIR, 'predict', 'models', 'data')


class Exam(base_models.TimeRecordField):
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)  # PSAT, prime
    year = models.IntegerField()
    ex = models.CharField(max_length=2, choices=EX_CHOICES)
    round = models.IntegerField()  # 0 for PSAT, round number for Prime
    predict_open_date = models.DateTimeField(default=timezone.now)
    exam_date = models.DateTimeField()
    answer_open_date = models.DateTimeField()

    @property
    def exam(self):
        return EX_CHOICES[self.ex]

    @property
    def answer_file(self):
        return os.path.join(data_dir, f"answer_file_{self.category}_{self.year}{self.ex}-{self.round}.csv")


class Student(
    base_models.TimeRecordField,
    base_models.UserIdField,
    base_models.NameField,
):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='students')
    serial = models.CharField(max_length=10)
    password = models.IntegerField()
    unit_id = models.IntegerField()
    department_id = models.IntegerField()
    prime_id = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "성적 예측 수험 정보"
        verbose_name_plural = "성적 예측 수험 정보"

    def __str__(self):
        return (f'[Student#{self.id}]{self.exam.category}-'
                f'{self.exam.year}{self.exam.ex}{self.exam.round}'
                f'-dep{self.department_id}-user{self.user_id}')


class Answer(base_models.TimeRecordField):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='answers')
    sub = models.CharField(max_length=2, choices=SUB_CHOICES)
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
        return (f'[Answer#{self.id}]{self.student.exam.category}'
                f'-{self.student.exam.year}{self.student.exam.ex}{self.student.exam.round}{self.sub}'
                f'-dep{self.student.department_id}-user{self.student.user_id}')

    @property
    def subject(self):
        return SUB_CHOICES[self.sub]


class AnswerCount(base_models.AnswerCountBase):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='answer_counts')
    sub = models.CharField(max_length=2, choices=SUB_CHOICES)
    number = models.IntegerField()
    answer = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "성적 예측 답안 개수"
        verbose_name_plural = "성적 예측 답안 개수"

    def __str__(self):
        return (f'[AnswerCount#{self.id}]{self.exam.category}'
                f'-{self.exam.year}{self.exam.ex}{self.exam.round}{self.sub}-{self.number}')

    @property
    def subject(self):
        return SUB_CHOICES[self.sub]


class Statistics(base_models.StatisticsBase):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='statistics')

    def __str__(self):
        return (f'[PredictStatistics#{self.id}]{self.student.exam.category}'
                f'-{self.student.exam.year}{self.student.exam.ex}{self.student.exam.round}'
                f'-dep{self.student.department_id}-user{self.student.user_id}')


class StatisticsVirtual(base_models.StatisticsBase):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='statistics_virtual')


class Location(base_models.TimeRecordField):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='locations')
    serial_start = models.IntegerField()
    serial_end = models.IntegerField()
    region = models.CharField(max_length=10)
    department = models.CharField(max_length=100)
    school = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    contact = models.CharField(max_length=20, blank=True, null=True)
