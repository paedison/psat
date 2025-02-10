from datetime import datetime

from django.db import models
from django.urls import reverse_lazy

from common.models import User
from .problem_models import Problem
from . import choices, abstract_models

verbose_name_prefix = '[스터디] '


class StudyCategory(models.Model):
    season = models.PositiveSmallIntegerField(default=1, verbose_name='시즌')
    study_type = models.CharField(
        max_length=5, choices=choices.study_category_choice, default='기본', verbose_name='종류')
    name = models.CharField(max_length=20, verbose_name='카테고리명')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_카테고리'
        db_table = 'a_psat_study_category'
        ordering = ['-season', 'study_type']
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'study_type'], name='unique_psat_study_category'
            ),
        ]

    def __str__(self):
        return f'[PSAT]StudyCategory(#{self.id}):{self.category_info}'

    @property
    def category_info(self):
        return f'시즌{self.season:02}{self.study_type}'

    def get_admin_study_category_detail_url(self):
        return reverse_lazy('psat:admin-study-category-detail', args=[self.id])


class StudyPsat(models.Model):
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='psats')
    round = models.PositiveSmallIntegerField(
        choices=choices.study_round_choice, default=1, verbose_name='회차')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_PSAT'
        db_table = 'a_psat_study_psat'
        ordering = ['-category', 'round']
        constraints = [
            models.UniqueConstraint(fields=['category', 'round'], name='unique_psat_study_psat'),
        ]

    def __str__(self):
        return f'[PSAT]StudyPsat(#{self.id}):{self.psat_info}'

    @property
    def psat_info(self):
        return f'{self.category.category_info}-{self.get_round_display()}'

    @property
    def season(self):
        return self.category.season

    @property
    def study_type(self):
        return self.category.study_type

    @property
    def name(self):
        return self.category.name


class StudyProblem(models.Model):
    psat = models.ForeignKey(StudyPsat, models.CASCADE, related_name='problems')
    number = models.PositiveSmallIntegerField(
        choices=choices.number_choice, default=1, verbose_name='번호')
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='study_problems')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_문제'
        db_table = 'a_psat_study_problem'
        ordering = ['psat', 'number']
        constraints = [
            models.UniqueConstraint(fields=['psat', 'number'], name='unique_psat_study_problem'),
        ]

    def __str__(self):
        return f'[PSAT]StudyProblem(#{self.id}):{self.category_info}-{self.problem_info}'

    @property
    def category_info(self):
        return self.psat.category.category_info

    @property
    def problem_info(self):
        return f'{self.psat.get_round_display()}-{self.get_number_display()}'


class StudyStatistics(abstract_models.Statistics):
    department = None
    subject_0 = None
    psat = models.OneToOneField(StudyPsat, models.CASCADE, related_name='statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_통계'
        db_table = 'a_psat_study_statistics'
        ordering = ['-psat']

    def __str__(self):
        return f'[PSAT]StudyStatistics(#{self.id}):{self.psat.psat_info}'


class StudyOrganization(models.Model):
    name = models.CharField(
        choices=choices.study_organization_choice, max_length=20, unique=True, verbose_name='이름')
    logo = models.ImageField(upload_to='images/logo', verbose_name='로고')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_교육기관'
        db_table = 'a_psat_study_organization'
        ordering = ['id']

    def __str__(self):
        return f'[PSAT]StudyOrganization(#{self.id}):{self.name}'


class StudyCurriculum(models.Model):
    year = models.PositiveSmallIntegerField(
        choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    organization = models.ForeignKey(StudyOrganization, models.CASCADE, related_name='curriculum')
    semester = models.PositiveSmallIntegerField(choices=choices.semester_choice, default=1, verbose_name='학기')
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='curriculum')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_커리큘럼'
        db_table = 'a_psat_study_curriculum'
        ordering = ['-year', 'organization', 'semester']
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'organization', 'semester'], name='unique_psat_study_curriculum'
            ),
        ]

    def __str__(self):
        return f'[PSAT]StudyCurriculum(#{self.id}):{self.curriculum_info}({self.category.category_info})'

    @property
    def curriculum_info(self):
        return f'{self.organization.name}-{self.year}-{self.semester}'

    def get_organization_semester(self):
        if self.organization in ['프라임']:
            return f'{self.semester}순환'
        else:
            return self.get_semester_display()


class StudyStudent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정 일시')
    curriculum = models.ForeignKey(StudyCurriculum, models.CASCADE, related_name='attendances')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, verbose_name='이름')
    user = models.ForeignKey(
        User, models.SET_NULL, null=True, blank=True, related_name='psat_study_students')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_학생'
        db_table = 'a_psat_study_student'

    def __str__(self):
        return f'[PSAT]StudyStudent(#{self.id}):{self.curriculum_info}-{self.student_info}'

    @property
    def curriculum_info(self):
        return self.curriculum.curriculum_info

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class StudyAnswer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    student = models.ForeignKey(StudyStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(
        StudyProblem, on_delete=models.CASCADE, related_name='university_answers')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_답안'
        db_table = 'a_psat_study_answer'
        ordering = ['student', 'problem']
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_psat_study_answer')
        ]

    def __str__(self):
        return f'[PSAT]StudyAnswer(#{self.id}):{self.student.student_info}-{self.problem.problem_info}'


class StudyAnswerCount(abstract_models.AnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='study_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수'
        db_table = 'a_psat_study_answer_count'
        ordering = ['problem']

    def __str__(self):
        return f'[PSAT]StudyAnswerCount(#{self.id}):{self.problem.reference}'


class StudyScore(abstract_models.Score):
    subject_0 = None
    student = models.OneToOneField(StudyStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_점수'
        db_table = 'a_psat_study_score'
        ordering = ['student']

    def __str__(self):
        return f'[PSAT]StudyScore(#{self.id}):{self.student.student_info}'


class StudyRank(abstract_models.Rank):
    subject_0 = None
    student = models.OneToOneField(StudyStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_등수'
        db_table = 'a_psat_study_rank'
        ordering = ['student']

    def __str__(self):
        return f'[PSAT]StudyRank(#{self.id}):{self.student.student_info}'


class StudyAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='study_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(상위권)'
        db_table = 'a_psat_study_answer_count_top_rank'
        ordering = ['problem']

    def __str__(self):
        return f'[PSAT]StudyAnswerCountTopRank(#{self.id}):{self.problem.reference}'


class StudyAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='study_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}12_답안 개수(중위권)'
        db_table = 'a_psat_study_answer_count_mid_rank'
        ordering = ['problem']


class StudyAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='study_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}13_답안 개수(하위권)'
        db_table = 'a_psat_study_answer_count_low_rank'
        ordering = ['problem']
