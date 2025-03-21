from django.db import models

from common.models import User
from . import abstract_models, managers
from .problem_models import Leet, Problem

verbose_name_prefix = '[성적예측] '


class PredictStatistics(abstract_models.ExtendedStatistics):
    objects = managers.StatisticsManager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='predict_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험통계'
        db_table = 'a_prime_leet_predict_statistics'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'aspiration'], name='unique_prime_leet_predict_statistics')
        ]

    def __str__(self):
        return self.leet.reference


class PredictStudent(abstract_models.Student):
    objects = managers.PredictStudentManager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='predict_students')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_leet_predict_students')
    is_filtered = models.BooleanField(default=False, verbose_name='필터링 여부')
    answer_count = {'언어': 0, '추리': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        db_table = 'a_prime_leet_predict_student'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'user'], name='unique_prime_leet_predict_student')
        ]

    def __str__(self):
        return self.student_info


class PredictAnswer(abstract_models.Answer):
    objects = managers.AnswerManager()
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_prime_leet_predict_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_leet_predict_answer')
        ]

    def __str__(self):
        return f'{self.student.student_info}-{self.problem.reference}'


class PredictAnswerCount(abstract_models.ExtendedAnswerCount):
    objects = managers.AnswerCountManager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_prime_leet_predict_answer_count'

    def __str__(self):
        return self.problem.reference


class PredictScore(abstract_models.Score):
    objects = managers.ScoreManager()
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_prime_leet_predict_score'

    def __str__(self):
        return self.student.student_info


class PredictRank(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수(전체)'
        db_table = 'a_prime_leet_predict_rank'

    def __str__(self):
        return self.student.student_info


class PredictRankAspiration1(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_aspiration_1')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_등수(1지망)'
        db_table = 'a_prime_leet_predict_rank_aspiration_1'

    def __str__(self):
        return self.student.student_info


class PredictRankAspiration2(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_aspiration_2')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_등수(2지망)'
        db_table = 'a_prime_leet_predict_rank_aspiration_2'

    def __str__(self):
        return self.student.student_info


class PredictAnswerCountTopRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_prime_leet_predict_answer_count_top_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountMidRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_prime_leet_predict_answer_count_mid_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountLowRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_prime_leet_predict_answer_count_low_rank'

    def __str__(self):
        return self.problem.reference
