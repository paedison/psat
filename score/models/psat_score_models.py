from django.db import models

from reference.models import Exam, PsatProblem
from score.models.base_models import UnitBase, StudentBase, AnswerBase


class PsatUnit(UnitBase):
    # Parent[UnitBase] fields: name
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='units')

    class Meta:
        verbose_name = "모집단위"
        verbose_name_plural = "모집단위"

    def __str__(self):
        return self.name


class PsatUnitDepartment(UnitBase):
    # Parent[UnitBase] fields: name
    unit = models.ForeignKey(PsatUnit, on_delete=models.CASCADE, related_name='departments')

    class Meta:
        verbose_name = "직렬"
        verbose_name_plural = "직렬"

    def __str__(self):
        return f'{self.unit}-{self.name}'


class PsatStudent(StudentBase):
    # Parent-Parent[InfoBase] fields: timestamp, update_at, user_id
    # Parent[StudentBase] fields: year, serial
    department = models.ForeignKey(PsatUnitDepartment, on_delete=models.CASCADE, related_name='students')
    heonbeob_score = models.FloatField(default=0)
    eoneo_score = models.FloatField(default=0)
    jaryo_score = models.FloatField(default=0)
    sanghwang_score = models.FloatField(default=0)
    psat_score = models.FloatField(default=0)

    class Meta:
        verbose_name = "수험 정보"
        verbose_name_plural = "수험 정보"

    def __str__(self):
        return f'{self.year}{self.department.unit.exam.abbr}-{self.department}-{self.user_id}'

    def average(self) -> float: return self.psat_score / 3


class PsatTemporaryAnswer(AnswerBase):
    # Parent-Parent[InfoBase] fields: timestamp, update_at, user_id
    # Parent[AnswerBase] fields: answer
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='temporary_answers')

    class Meta:
        verbose_name = "답안(임시 저장용)"
        verbose_name_plural = "답안(임시 저장용)"


class PsatConfirmedAnswer(AnswerBase):
    # Parent-Parent[InfoBase] fields: timestamp, update_at, user_id
    # Parent[AnswerBase] fields: answer
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='confirmed_answers')
    confirmed_times = models.IntegerField("확정 횟수", default=1)

    class Meta:
        verbose_name = "답안(최종 제출용)"
        verbose_name_plural = "답안(최종 제출용)"


class PsatAnswerCount(models.Model):
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='answer_counts')
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
