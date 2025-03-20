from datetime import datetime

from django.db import models
from django.db.models import functions
from django.urls import reverse_lazy

from common.models import User
from . import choices, abstract_models, managers
from .problem_models import Problem

verbose_name_prefix = '[스터디] '


def get_study_statistics_aggregation(qs_student):
    return qs_student.aggregate(
        participants=models.Count('id'), max=models.Max('score_total'), avg=models.Avg('score_total'))


def get_study_student_score_calculated_annotation(qs_student):
    return qs_student.annotate(
        score_calculated=functions.Coalesce(models.Sum('results__score'), None))


def get_study_student_total_rank_calculated_annotation(qs_student):
    return qs_student.annotate(
        rank_calculated=models.Case(
            models.When(score_total__isnull=True, then=models.Value(None)),
            default=models.Window(expression=functions.Rank(), order_by=[models.F('score_total').desc()]),
            output_field=models.IntegerField(),
        )
    )


class StudyCategory(models.Model):
    objects = managers.StudyCategoryManager()
    season = models.PositiveSmallIntegerField(default=1, verbose_name='시즌')
    study_type = models.CharField(
        max_length=5, choices=choices.study_category_choice, default='기본', verbose_name='종류')
    name = models.CharField(max_length=20, verbose_name='카테고리명')
    round = models.PositiveSmallIntegerField(default=1, verbose_name='회차 수')
    participants = models.PositiveIntegerField(default=1, verbose_name='참여자 수')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_카테고리'
        db_table = 'a_psat_study_category'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'study_type'], name='unique_psat_study_category'
            ),
        ]

    def __str__(self):
        return self.category_info

    @property
    def category_info(self):
        return f'시즌{self.season:02}{self.study_type}'

    @property
    def full_reference(self):
        return f'시즌{self.season:02} {self.study_type} [{self.name}]'

    def get_admin_study_category_detail_url(self):
        return reverse_lazy('psat:admin-study-detail', args=['category', self.id])


class StudyPsat(models.Model):
    objects = managers.StudyPsatManager()
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='psats', verbose_name='카테고리')
    round = models.PositiveSmallIntegerField(
        choices=choices.study_round_choice, default=1, verbose_name='회차')
    statistics = models.JSONField(default=abstract_models.get_default_statistics, verbose_name='통계')
    problem_counts = models.JSONField(
        default=abstract_models.get_default_problem_counts, verbose_name='문제 수')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_PSAT'
        db_table = 'a_psat_study_psat'
        ordering = ['category', 'round']
        constraints = [
            models.UniqueConstraint(fields=['category', 'round'], name='unique_psat_study_psat'),
        ]

    def __str__(self):
        return self.psat_info

    @property
    def category_info(self):
        return self.category.category_info

    @property
    def psat_info(self):
        return f'{self.category_info}-{self.round:02}'

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
    objects = managers.StudyProblemManager()
    psat = models.ForeignKey(StudyPsat, models.CASCADE, related_name='problems', verbose_name='PSAT')
    number = models.PositiveSmallIntegerField(
        choices=choices.number_choice, default=1, verbose_name='번호')
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='study_problems', verbose_name='스터디 문제')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_문제'
        db_table = 'a_psat_study_problem'
        ordering = ['psat', 'number']
        constraints = [
            models.UniqueConstraint(fields=['psat', 'number'], name='unique_psat_study_problem'),
        ]

    def __str__(self):
        return self.problem_info

    @property
    def category_info(self):
        return self.psat.category.category_info

    @property
    def psat_info(self):
        return self.psat.psat_info

    @property
    def problem_info(self):
        return f'{self.psat.psat_info}-{self.number:02}'

    @property
    def problem_reference(self):
        return self.problem.reference

    @property
    def answer_official(self):
        return self.problem.answer

    @property
    def answer(self):
        return self.problem.answer


class StudyOrganization(models.Model):
    name = models.CharField(
        choices=choices.study_organization_choice, max_length=20, unique=True, verbose_name='이름')
    logo = models.ImageField(upload_to='images/logo', verbose_name='로고')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_교육기관'
        db_table = 'a_psat_study_organization'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_psat_study_organization'),
        ]

    def __str__(self):
        return self.name


class StudyCurriculum(models.Model):
    objects = managers.StudyCurriculumManager()
    year = models.PositiveSmallIntegerField(
        choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    organization = models.ForeignKey(
        StudyOrganization, models.CASCADE, related_name='curriculum', verbose_name='교육기관')
    semester = models.PositiveSmallIntegerField(choices=choices.study_semester_choice, default=1, verbose_name='학기')
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='curriculum', verbose_name='카테고리')
    name = models.CharField(max_length=20, default='', verbose_name='커리큘럼명')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_커리큘럼'
        db_table = 'a_psat_study_curriculum'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'organization', 'semester'], name='unique_psat_study_curriculum'
            ),
        ]

    def __str__(self):
        return self.curriculum_info

    @property
    def category_info(self):
        return self.category.category_info

    @property
    def curriculum_info(self):
        return f'{self.organization}-{self.year}-{self.semester}'

    @property
    def full_reference(self):
        return f'{self.organization.name} {self.get_year_display()}-{self.get_organization_semester()}'

    def get_organization_semester(self):
        if self.organization in ['프라임']:
            return f'{self.semester}순환'
        else:
            return self.get_semester_display()

    def get_admin_study_curriculum_detail_url(self):
        return reverse_lazy('psat:admin-study-detail', args=['curriculum', self.id])

    def get_study_curriculum_detail_url(self):
        return reverse_lazy('psat:study-detail', args=[self.id])


class StudyCurriculumSchedule(models.Model):
    objects = managers.StudyCurriculumScheduleManager()
    curriculum = models.ForeignKey(
        StudyCurriculum, on_delete=models.CASCADE, related_name='schedules', verbose_name='커리큘럼')
    lecture_number = models.PositiveSmallIntegerField(default=1, verbose_name='강의 주차')
    lecture_theme = models.IntegerField(choices=choices.study_lecture_theme, default=1, verbose_name='강의 주제')
    lecture_round = models.PositiveSmallIntegerField(
        choices=choices.study_round_choice, null=True, blank=True, verbose_name='미니테스트 강의 회차')
    homework_round = models.PositiveSmallIntegerField(
        choices=choices.study_round_choice, null=True, blank=True, verbose_name='미니테스트 과제 회차')
    lecture_open_datetime = models.DateTimeField(null=True, blank=True, verbose_name='공개 날짜')
    homework_end_datetime = models.DateTimeField(null=True, blank=True, verbose_name='과제 마감 날짜')
    lecture_datetime = models.DateTimeField(null=True, blank=True, verbose_name='강의 날짜')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_커리큘럼 스케줄'
        db_table = 'a_psat_study_curriculum_schedule'
        constraints = [
            models.UniqueConstraint(
                fields=['curriculum', 'lecture_number'], name='unique_psat_study_curriculum_schedule'
            ),
        ]

    def __str__(self):
        return f'[PSAT]StudyCurriculumSchedule(#{self.id}):{self.curriculum.curriculum_info}-{self.lecture_number}'

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_psat_studycurriculumschedule_change', args=[self.id])


class StudyStudent(models.Model):
    objects = managers.StudyStudentManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정 일시')
    curriculum = models.ForeignKey(StudyCurriculum, models.CASCADE, related_name='students', verbose_name='커리큘럼')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, default='', verbose_name='이름')
    user = models.ForeignKey(
        User, models.SET_NULL, null=True, blank=True, related_name='psat_study_students', verbose_name='사용자')
    score_total = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='총점')
    rank_total = models.PositiveIntegerField(null=True, blank=True, verbose_name='등수')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_학생'
        db_table = 'a_psat_study_student'
        constraints = [
            models.UniqueConstraint(
                fields=['curriculum', 'serial'], name='unique_psat_study_student'
            ),
        ]

    def __str__(self):
        return f'{self.serial}-{self.name}'

    @property
    def curriculum_info(self):
        return self.curriculum.curriculum_info

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'

    @property
    def year(self):
        return self.curriculum.year

    @property
    def organization(self):
        return self.curriculum.organization.name

    @property
    def semester(self):
        return self.curriculum.semester

    def get_result_list(self):
        return self.results.order_by('psat__round')

    def get_study_curriculum_detail_url(self):
        return reverse_lazy('psat:study-detail', args=[self.curriculum_id])

    def get_admin_study_student_detail_url(self):
        return reverse_lazy('psat:admin-study-student-detail', args=[self.id])


class StudyAnswer(models.Model):
    objects = managers.StudyAnswerManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    student = models.ForeignKey(
        StudyStudent, on_delete=models.CASCADE, related_name='answers', verbose_name='학생')
    problem = models.ForeignKey(
        StudyProblem, on_delete=models.CASCADE, related_name='answers', verbose_name='스터디 문제')
    answer = models.IntegerField(choices=choices.answer_choice, default=0, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_답안'
        db_table = 'a_psat_study_answer'
        ordering = ['student', 'problem']
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_psat_study_answer')
        ]

    def __str__(self):
        return f'{self.student_info}-{self.problem_info}'

    @property
    def curriculum_info(self):
        return self.student.curriculum_info

    @property
    def student_info(self):
        return self.student.student_info

    @property
    def problem_info(self):
        return self.problem.problem_info

    @property
    def problem_reference(self):
        return self.problem.problem_reference

    @property
    def answer_official(self):
        return self.problem.answer_official

    @property
    def answer_correct(self):
        return self.problem.answer_official

    @property
    def answer_student(self):
        return self.answer


class StudyAnswerCount(abstract_models.AnswerCount):
    objects = managers.StudyAnswerCountManager()
    problem = models.OneToOneField(StudyProblem, on_delete=models.CASCADE, related_name='answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수'
        db_table = 'a_psat_study_answer_count'
        ordering = ['problem']

    def __str__(self):
        return f'[PSAT]StudyAnswerCount(#{self.id}):{self.problem_info}'

    @property
    def problem_info(self):
        return self.problem.problem_info

    @property
    def problem_reference(self):
        return self.problem.problem_reference

    @property
    def answer_official(self):
        return self.problem.problem.answer

    @property
    def round(self):
        return self.problem.psat.round

    @property
    def number(self):
        return self.problem.number

    @property
    def subject(self):
        return self.problem.problem.subject


class StudyResult(models.Model):
    objects = managers.StudyResultManager()
    student = models.ForeignKey(StudyStudent, on_delete=models.CASCADE, related_name='results', verbose_name='학생')
    psat = models.ForeignKey(StudyPsat, on_delete=models.CASCADE, related_name='results', verbose_name='PSAT')
    rank = models.PositiveIntegerField(null=True, blank=True, verbose_name='등수')
    score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='점수')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_성적'
        db_table = 'a_psat_study_result'
        ordering = ['student']
        constraints = [
            models.UniqueConstraint(fields=['student', 'psat'], name='unique_psat_study_result')
        ]

    def __str__(self):
        return f'{self.student}({self.psat})'

    @property
    def curriculum_info(self):
        return self.student.curriculum_info

    @property
    def student_info(self):
        return self.student.student_info

    @property
    def psat_info(self):
        return self.psat.psat_info

    @property
    def psat_round(self):
        return self.psat.round

    def get_answer_input_url(self):
        return reverse_lazy('psat:study-answer-input', args=[self.id])

    def get_answer_confirm_url(self):
        return reverse_lazy('psat:study-answer-confirm', args=[self.id])


class StudyAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(StudyProblem, on_delete=models.CASCADE, related_name='answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(상위권)'
        db_table = 'a_psat_study_answer_count_top_rank'
        ordering = ['problem']

    def __str__(self):
        return self.problem_info

    @property
    def problem_info(self):
        return self.problem.problem_info

    @property
    def problem_reference(self):
        return self.problem.problem_reference


class StudyAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(StudyProblem, on_delete=models.CASCADE, related_name='answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(중위권)'
        db_table = 'a_psat_study_answer_count_mid_rank'
        ordering = ['problem']

    @property
    def problem_info(self):
        return self.problem.problem_info

    @property
    def problem_reference(self):
        return self.problem.problem_reference


class StudyAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(StudyProblem, on_delete=models.CASCADE, related_name='answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}12_답안 개수(하위권)'
        db_table = 'a_psat_study_answer_count_low_rank'
        ordering = ['problem']

    @property
    def problem_info(self):
        return self.problem.problem_info

    @property
    def problem_reference(self):
        return self.problem.problem_reference
