from django.db import models

from common.models import User
from .problem_models import Psat, Problem, Category
from . import choices


class ResultStudent(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='result_students')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='result_students')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 01_수험정보"
        db_table = 'a_prime_result_student'
        constraints = [
            models.UniqueConstraint(fields=['psat', 'category', 'name', 'serial'], name='unique_prime_result_student')
        ]

    def __str__(self):
        return f'[Prime]ResultStudent(#{self.id}):{self.psat.reference}({self.student_info})'

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class ResultRegistry(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_result_registries')
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='registries')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 02_수험정보 연결"
        db_table = 'a_prime_result_registry'
        constraints = [
            models.UniqueConstraint(fields=['user', 'student'], name='unique_prime_result_registry')
        ]

    def __str__(self):
        return f'[Prime]ResultRegistry(#{self.id}):{self.student.psat.reference}({self.student.student_info})'


class ResultAnswer(models.Model):
    student = models.ForeignKey(ResultStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='result_answers')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 03_답안"
        db_table = 'a_prime_result_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_prime_result_answer')
        ]

    def __str__(self):
        return f'[Prime]ResultAnswer(#{self.id}):{self.student.student_info}-{self.problem.reference}'


class ResultAnswerCount(models.Model):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='result_answer_count')
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_5 = models.IntegerField(default=0, verbose_name='⑤')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_total = models.IntegerField(default=0, verbose_name='총계')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 04_답안 개수"
        db_table = 'a_prime_result_answer_count'

    def __str__(self):
        return f'[Prime]ResultAnswerCount(#{self.id}):{self.problem.reference}'


class ResultScore(models.Model):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='score')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    total = models.FloatField(null=True, blank=True, verbose_name='PSAT 총점')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 05_점수"
        db_table = 'a_prime_result_score'

    def __str__(self):
        return f'[Prime]ResultScore(#{self.id}):{self.student.student_info}'


class ResultRankTotal(models.Model):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_total')
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='상황판단')
    total = models.IntegerField(null=True, blank=True, verbose_name='PSAT')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 06_전체 등수"
        db_table = 'a_prime_result_rank_total'

    def __str__(self):
        return f'[Prime]ResultRankTotal(#{self.id}):{self.student.student_info}'


class ResultRankCategory(models.Model):
    student = models.OneToOneField(ResultStudent, on_delete=models.CASCADE, related_name='rank_category')
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='상황판단')
    total = models.IntegerField(null=True, blank=True, verbose_name='PSAT')

    class Meta:
        verbose_name = verbose_name_plural = "[성적확인] 07_직렬 등수"
        db_table = 'a_prime_result_rank_category'

    def __str__(self):
        return f'[Prime]ResultRankCategory(#{self.id}):{self.student.student_info}'
