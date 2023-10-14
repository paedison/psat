from django.db import models

from common.models import User
from psat.models import Problem, Exam


class Unit(models.Model):
    name = models.CharField(max_length=128)
    ex = models.CharField(max_length=2, choices=Exam.Exams.choices)

    class Meta:
        ordering = ['id']
        verbose_name = "모집단위"
        verbose_name_plural = "모집단위"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=128)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='departments')

    class Meta:
        ordering = ['id']
        verbose_name = "직렬"
        verbose_name_plural = "직렬"

    def __str__(self):
        return f'{self.unit}-{self.name}'


class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='students')
    year = models.IntegerField(choices=Exam.Years.choices)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='students')
    serial = models.CharField(max_length=20, null=True, blank=True)
    eoneo_score = models.FloatField(blank=True, null=True)
    jaryo_score = models.FloatField(blank=True, null=True)
    sanghwang_score = models.FloatField(blank=True, null=True)
    psat_score = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['id']
        verbose_name = "수험 정보"
        verbose_name_plural = "수험 정보"

    def __str__(self):
        return f'{self.year}{self.department.unit.ex}-{self.department}-{self.user}'

    def average(self) -> float: return self.psat_score / 3


class DummyStudent(models.Model):
    user = models.IntegerField()
    year = models.IntegerField(choices=Exam.Years.choices)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='dummy_students')
    serial = models.CharField(max_length=20, null=True, blank=True)
    eoneo_score = models.FloatField(blank=True, null=True)
    jaryo_score = models.FloatField(blank=True, null=True)
    sanghwang_score = models.FloatField(blank=True, null=True)
    psat_score = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['id']
        verbose_name = "수험 정보"
        verbose_name_plural = "수험 정보"

    def __str__(self):
        return f'{self.year}{self.department.unit.ex}-{self.department}-{self.user}'


class TemporaryAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="temporary_answers")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='temporary_answers')
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = "답안(임시 저장용)"
        verbose_name_plural = "답안(임시 저장용)"


class ConfirmedAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="confirmed_answers")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='confirmed_answers')
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_times = models.IntegerField("확정 횟수", default=1)

    class Meta:
        ordering = ['id']
        verbose_name = "답안(최종 제출용)"
        verbose_name_plural = "답안(최종 제출용)"


class DummyAnswer(models.Model):
    student = models.ForeignKey(DummyStudent, on_delete=models.CASCADE, related_name="dummy_answers")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='dummy_answers')
    answer = models.IntegerField("제출 답안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_times = models.IntegerField("확정 횟수", default=1)

    class Meta:
        ordering = ['id']
        verbose_name = "답안(테스트용)"
        verbose_name_plural = "답안(테스트용)"


class AnswerCount(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='answer_counts')
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']
        verbose_name = "답안 개수(통계용)"
        verbose_name_plural = "답안 개수(통계용)"

    @property
    def count_correct(self):
        answer_dict = {
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
