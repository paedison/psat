from django.db import models
from django.urls import reverse_lazy

from common.models import User
from . import abstract_models, querysets
from .problem_models import Leet, Problem

verbose_name_prefix = '[성적확인] '


class ResultStatistics(abstract_models.Statistics):
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='result_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험통계'
        db_table = 'a_prime_leet_result_statistics'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'aspiration'], name='unique_prime_leet_result_statistics')
        ]

    def __str__(self):
        return self.leet.reference


class ResultStudent(abstract_models.Student):
    objects = querysets.StudentQuerySet.as_manager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='result_students')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        db_table = 'a_prime_leet_result_student'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'name', 'serial'], name='unique_prime_leet_result_student')
        ]

    def __str__(self):
        return self.student_info

    def get_admin_detail_student_url(self):
        return reverse_lazy('prime_leet:admin-detail-student', args=['result', self.id])

    def get_admin_detail_student_print_url(self):
        return reverse_lazy('prime_leet:admin-detail-student-print', args=['result', self.id])


class ResultRegistry(models.Model):
    objects = querysets.ResultRegistryQueryset.as_manager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_leet_result_registries')
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='registries')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_수험정보 연결'
        db_table = 'a_prime_leet_result_registry'
        constraints = [
            models.UniqueConstraint(fields=['user', 'student'], name='unique_prime_leet_result_registry')
        ]

    def __str__(self):
        return self.student.student_info

    def get_admin_detail_student_url(self):
        return reverse_lazy('prime_leet:admin-detail-student', args=['result', self.student_id])

    def get_admin_detail_student_print_url(self):
        return reverse_lazy('prime_leet:admin-detail-student-print', args=['result', self.student_id])


class ResultAnswer(abstract_models.Answer):
    objects = querysets.AnswerQueryset.as_manager()
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='result_answers')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_prime_leet_result_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_leet_result_answer')
        ]

    def __str__(self):
        return f'{self.student.student_info}-{self.problem.reference}'


class ResultAnswerCount(abstract_models.AnswerCount):
    objects = querysets.AnswerCountQueryset.as_manager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_prime_leet_result_answer_count'

    def __str__(self):
        return self.problem.reference


class ResultScore(abstract_models.Score):
    objects = querysets.ScoreQueryset.as_manager()
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_prime_leet_result_score'

    def __str__(self):
        return self.student.student_info


class ResultRank(abstract_models.Rank):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수(전체)'
        db_table = 'a_prime_leet_result_rank'

    def __str__(self):
        return self.student.student_info


class ResultRankAspiration1(abstract_models.Rank):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_aspiration_1')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_등수(1지망)'
        db_table = 'a_prime_leet_result_rank_aspiration_1'

    def __str__(self):
        return self.student.student_info


class ResultRankAspiration2(abstract_models.Rank):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_aspiration_2')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_등수(2지망)'
        db_table = 'a_prime_leet_result_rank_aspiration_2'

    def __str__(self):
        return self.student.student_info


class ResultAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_prime_leet_result_answer_count_top_rank'

    def __str__(self):
        return self.problem.reference


class ResultAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_prime_leet_result_answer_count_mid_rank'

    def __str__(self):
        return self.problem.reference


class ResultAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_prime_leet_result_answer_count_low_rank'

    def __str__(self):
        return self.problem.reference
