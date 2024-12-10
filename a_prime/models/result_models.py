from django.db import models

from common.models import User
from . import abstract_models
from .problem_models import Psat, Problem, Category

verbose_name_prefix = '[성적확인] '


class ResultStudent(abstract_models.Student):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='result_students')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='result_students')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        db_table = 'a_prime_result_student'
        constraints = [
            models.UniqueConstraint(fields=['psat', 'category', 'name', 'serial'], name='unique_prime_result_student')
        ]

    def __str__(self):
        return f'[Prime]ResultStudent(#{self.id}):{self.psat.reference}({self.student_info})'


class ResultRegistry(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_result_registries')
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='registries')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_수험정보 연결'
        db_table = 'a_prime_result_registry'
        constraints = [
            models.UniqueConstraint(fields=['user', 'student'], name='unique_prime_result_registry')
        ]

    def __str__(self):
        return f'[Prime]ResultRegistry(#{self.id}):{self.student.psat.reference}({self.student.student_info})'


class ResultAnswer(abstract_models.Answer):
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='result_answers')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_prime_result_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_result_answer')
        ]

    def __str__(self):
        return f'[Prime]ResultAnswer(#{self.id}):{self.student.student_info}-{self.problem.reference}'


class ResultAnswerCount(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_prime_result_answer_count'

    def __str__(self):
        return f'[Prime]ResultAnswerCount(#{self.id}):{self.problem.reference}'


class ResultScore(abstract_models.Score):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_prime_result_score'

    def __str__(self):
        return f'[Prime]ResultScore(#{self.id}):{self.student.student_info}'

    @property
    def average(self):
        return round(self.sum / 3, 1)


class ResultRankTotal(abstract_models.Rank):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_total')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_전체 등수'
        db_table = 'a_prime_result_rank_total'

    def __str__(self):
        return f'[Prime]ResultRankTotal(#{self.id}):{self.student.student_info}'


class ResultRankCategory(abstract_models.Rank):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_category')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_직렬 등수'
        db_table = 'a_prime_result_rank_category'

    def __str__(self):
        return f'[Prime]ResultRankCategory(#{self.id}):{self.student.student_info}'


class ResultAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(상위권)'
        db_table = 'a_prime_result_answer_count_top_rank'


class ResultAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(중위권)'
        db_table = 'a_prime_result_answer_count_mid_rank'


class ResultAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(하위권)'
        db_table = 'a_prime_result_answer_count_low_rank'
