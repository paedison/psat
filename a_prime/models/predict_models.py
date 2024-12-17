from django.db import models

from common.models import User
from .problem_models import Psat, Problem, Category
from . import choices

verbose_name_prefix = '[성적예측] '


class PredictStudent(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_students')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='predict_students')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_predict_students')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')

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

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class PredictAnswer(models.Model):
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_prime_predict_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_predict_answer')
        ]

    def __str__(self):
        return f'[Prime]PredictAnswer(#{self.id}):{self.student.student_info}-{self.problem.reference}'


class PredictAnswerCount(models.Model):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count')
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_5 = models.IntegerField(default=0, verbose_name='⑤')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_total = models.IntegerField(default=0, verbose_name='총계')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_prime_predict_answer_count'

    def __str__(self):
        return f'[Prime]PredictAnswerCount(#{self.id}):{self.problem.reference}'


class PredictScore(models.Model):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    total = models.FloatField(null=True, blank=True, verbose_name='PSAT 총점')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_prime_predict_score'

    def __str__(self):
        return f'[Prime]PredictScore(#{self.id}):{self.student.student_info}'


class PredictRank(models.Model):
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='상황판단')
    total = models.IntegerField(null=True, blank=True, verbose_name='PSAT')

    class Meta:
        abstract = True


class PredictRankTotal(PredictRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_total')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_전체 등수'
        db_table = 'a_prime_predict_rank_total'

    def __str__(self):
        return f'[Prime]PredictRankTotal(#{self.id}):{self.student.student_info}'


class PredictRankCategory(PredictRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_category')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_직렬 등수'
        db_table = 'a_prime_predict_rank_category'

    def __str__(self):
        return f'[Prime]PredictRankCategory(#{self.id}):{self.student.student_info}'


class PredictAnswerCountLowRank(PredictAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(하위권)'
        db_table = 'a_prime_predict_answer_count_low_rank'


class PredictAnswerCountMidRank(PredictAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(중위권)'
        db_table = 'a_prime_predict_answer_count_mid_rank'


class PredictAnswerCountTopRank(PredictAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(상위권)'
        db_table = 'a_prime_predict_answer_count_top_rank'
