from django.db import models
from django.urls import reverse_lazy

from . import abstract_models, managers, choices
from .problem_models import Leet, Problem

verbose_name_prefix = '[가상답안] '


class FakeRefAspiration(models.Model):
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='fake_ref_aspiration')
    university = models.CharField(max_length=10, choices=choices.university_choice, verbose_name='지망 대학')
    aspiration_1 = models.IntegerField(default=0, verbose_name='1지망 지원자수')
    aspiration_2 = models.IntegerField(default=0, verbose_name='2지망 지원자수')
    aspiration_sum = models.IntegerField(default=0, verbose_name='전체 지원자수')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_참고 지원자수'
        db_table = 'a_prime_leet_fake_ref_aspiration'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'university'], name='unique_prime_leet_fake_ref_aspiration')
        ]

    def __str__(self):
        return f'{self.leet.abbr} - {self.university}'


class FakeRefAnswerCount(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='fake_ref_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_참고 답안 개수'
        db_table = 'a_prime_leet_fake_ref_answer_count'

    def __str__(self):
        return self.problem.reference


class FakeStatistics(abstract_models.Statistics):
    objects = managers.StatisticsManager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='fake_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_시험통계'
        db_table = 'a_prime_leet_fake_statistics'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'aspiration'], name='unique_prime_leet_fake_statistics')
        ]

    def __str__(self):
        return self.leet.abbr


class FakeStudent(models.Model):
    objects = managers.StudentManager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='fake_students')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, verbose_name='이름')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')
    aspiration_1 = models.CharField(
        max_length=10, choices=choices.university_choice, null=True, blank=True, verbose_name='1지망')
    aspiration_2 = models.CharField(
        max_length=10, choices=choices.university_choice, null=True, blank=True, verbose_name='2지망')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_수험정보'
        db_table = 'a_prime_leet_fake_student'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'serial'], name='unique_prime_leet_fake_student')
        ]

    def __str__(self):
        return self.serial

    def get_admin_detail_student_url(self):
        return reverse_lazy('prime_leet:admin-detail-student', args=['fake', self.id])

    def get_admin_detail_student_print_url(self):
        return reverse_lazy('prime_leet:admin-detail-student-print', args=['fake', self.id])


class FakeScore(abstract_models.Score):
    objects = managers.ScoreManager()
    student = models.OneToOneField(FakeStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_점수'
        db_table = 'a_prime_leet_fake_score'

    def __str__(self):
        return self.student.serial


class FakeRank(abstract_models.Rank):
    student = models.OneToOneField(FakeStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_등수(전체)'
        db_table = 'a_prime_leet_fake_rank'

    def __str__(self):
        return self.student.serial


class FakeRankAspiration1(abstract_models.Rank):
    student = models.OneToOneField(FakeStudent, on_delete=models.CASCADE, related_name='rank_aspiration_1')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수(1지망)'
        db_table = 'a_prime_leet_fake_rank_aspiration_1'

    def __str__(self):
        return self.student.serial


class FakeRankAspiration2(abstract_models.Rank):
    student = models.OneToOneField(FakeStudent, on_delete=models.CASCADE, related_name='rank_aspiration_2')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_등수(2지망)'
        db_table = 'a_prime_leet_fake_rank_aspiration_2'

    def __str__(self):
        return self.student.serial


class FakeAnswerCount(abstract_models.AnswerCount):
    objects = managers.AnswerCountManager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='fake_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(전체)'
        db_table = 'a_prime_leet_fake_answer_count'

    def __str__(self):
        return self.problem.reference


class FakeAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='fake_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_prime_leet_fake_answer_count_top_rank'

    def __str__(self):
        return self.problem.reference


class FakeAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='fake_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_prime_leet_fake_answer_count_mid_rank'

    def __str__(self):
        return self.problem.reference


class FakeAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='fake_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_prime_leet_fake_answer_count_low_rank'

    def __str__(self):
        return self.problem.reference
