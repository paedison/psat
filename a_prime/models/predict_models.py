from django.db import models

from common.models import User
from . import abstract_models
from .problem_models import Psat, Problem, Category

verbose_name_prefix = '[성적예측] '


class PredictStatistics(abstract_models.ExtendedStatistics):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험통계'
        db_table = 'a_prime_predict_statistics'
        constraints = [
            models.UniqueConstraint(fields=['psat', 'department'], name='unique_prime_predict_statistics')
        ]

    def __str__(self):
        return f'[Prime]PredictStatistics(#{self.id}):{self.psat.reference}'


class PredictStudent(abstract_models.Student):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_students')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='predict_students')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_predict_students')
    is_filtered = models.BooleanField(default=False, verbose_name='필터링 여부')
    department = ''
    answer_count = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0, '평균': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        db_table = 'a_prime_predict_student'
        constraints = [
            models.UniqueConstraint(
                fields=['psat', 'category', 'user', 'name', 'serial'],
                name='unique_prime_predict_student',
            )
        ]

    def __str__(self):
        return f'[Prime]PredictStudent(#{self.id}):{self.psat.reference}({self.student_info})'


class PredictAnswer(abstract_models.Answer):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성 일시')
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_prime_predict_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_predict_answer')
        ]

    def __str__(self):
        return f'[Prime]PredictAnswer(#{self.id}):{self.student.student_info}-{self.problem.reference}'


class PredictAnswerCount(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_prime_predict_answer_count'

    def __str__(self):
        return f'[Prime]PredictAnswerCount(#{self.id}):{self.problem.reference}'


class PredictScore(abstract_models.Score):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_prime_predict_score'

    def __str__(self):
        return f'[Prime]PredictScore(#{self.id}):{self.student.student_info}'


class PredictRankTotal(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_total')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_전체 등수'
        db_table = 'a_prime_predict_rank_total'

    def __str__(self):
        return f'[Prime]PredictRankTotal(#{self.id}):{self.student.student_info}'


class PredictRankCategory(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_category')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_직렬 등수'
        db_table = 'a_prime_predict_rank_category'

    def __str__(self):
        return f'[Prime]PredictRankCategory(#{self.id}):{self.student.student_info}'


class PredictAnswerCountTopRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(상위권)'
        db_table = 'a_prime_predict_answer_count_top_rank'


class PredictAnswerCountMidRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(중위권)'
        db_table = 'a_prime_predict_answer_count_mid_rank'


class PredictAnswerCountLowRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(하위권)'
        db_table = 'a_prime_predict_answer_count_low_rank'
