from datetime import datetime

from django.db import models
from django.db.models import functions
from django.urls import reverse_lazy

from common.models import User
from . import choices, abstract_models
from .problem_models import Problem

verbose_name_prefix = '[스터디] '


class StudyCategoryManager(models.Manager):
    def with_prefetch_related(self):
        return self.prefetch_related('psats')

    def annotate_student_count(self):
        return self.annotate(student_count=models.Count('curriculum__students')).order_by('-id')


class StudyCategory(models.Model):
    objects = StudyCategoryManager()
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
        return f'[PSAT]StudyCategory(#{self.id}):{self.category_info}'

    @property
    def category_info(self):
        return f'시즌{self.season:02}{self.study_type}'

    @property
    def full_reference(self):
        return f'시즌{self.season:02} {self.study_type} [{self.name}]'

    def get_admin_study_category_detail_url(self):
        return reverse_lazy('psat:admin-study-detail', args=['category', self.id])


class StudyPsatManager(models.Manager):
    def with_select_related(self):
        return self.select_related('category')

    def get_qs_psat(self, category: StudyCategory):
        return self.with_select_related().filter(category=category)


class StudyPsat(models.Model):
    objects = StudyPsatManager()
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='psats')
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
        return f'[PSAT]StudyPsat(#{self.id}):{self.psat_info}'

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


class StudyProblemManager(models.Manager):
    def with_select_related(self):
        return self.select_related('psat', 'psat__category', 'problem', 'problem__psat')

    def get_qs_study_problem(self, category):
        return self.filter(psat__category=category).select_related(
            'psat', 'psat__category', 'problem', 'problem__psat')

    def get_filtered_qs_by_category_annotated_with_answer_count(self, category):
        annotate_dict = {'ans_official': models.F('problem__answer')}
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}_all'] = models.F(f'answer_count__{fld}')
            annotate_dict[f'{fld}_top'] = models.F(f'answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = models.F(f'answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = models.F(f'answer_count_low_rank__{fld}')
        return (
            self.filter(psat__category=category).order_by('psat__round', 'number').annotate(**annotate_dict)
            .select_related(
                'psat', 'problem', 'problem__psat', 'answer_count',
                'answer_count_top_rank', 'answer_count_mid_rank', 'answer_count_low_rank',
            )
        )

    def get_ordered_qs_by_subject_field(self):
        return self.values('psat_id', 'problem__subject').annotate(
            subject=get_annotation_for_subject(), count=models.Count('id')).order_by('psat_id', 'subject')


class StudyProblem(models.Model):
    objects = StudyProblemManager()
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
    def psat_info(self):
        return self.psat.psat_info

    @property
    def problem_info(self):
        return f'{self.psat.round:02}회차-{self.number:02}번'

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
        return f'[PSAT]StudyOrganization(#{self.id}):{self.name}'


class StudyCurriculumManager(models.Manager):
    def with_select_related(self):
        return self.select_related('organization', 'category')

    def annotate_student_count(self):
        return self.with_select_related().annotate(
            student_count=models.Count('students'),
            registered_student_count=models.Count('students', filter=models.Q(students__user__isnull=False))
        ).order_by('-id')


class StudyCurriculum(models.Model):
    objects = StudyCurriculumManager()
    year = models.PositiveSmallIntegerField(
        choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    organization = models.ForeignKey(StudyOrganization, models.CASCADE, related_name='curriculum')
    semester = models.PositiveSmallIntegerField(choices=choices.study_semester_choice, default=1, verbose_name='학기')
    category = models.ForeignKey(StudyCategory, models.CASCADE, related_name='curriculum')
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
        return f'[PSAT]StudyCurriculum(#{self.id}):{self.curriculum_info}({self.category_info})'

    @property
    def category_info(self):
        return self.category.category_info

    @property
    def curriculum_info(self):
        return f'{self.organization.name}-{self.year}-{self.semester}'

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


class StudyCurriculumScheduleManager(models.Manager):
    def with_select_related(self):
        return self.select_related('curriculum')

    def get_curriculum_schedule_info(self):
        return (
            self.values('curriculum')
            .annotate(
                study_rounds=models.Count('id'),
                earliest=models.Min('lecture_datetime'),
                latest=models.Max('lecture_datetime'),
            )
        )


class StudyCurriculumSchedule(models.Model):
    objects = StudyCurriculumScheduleManager()
    curriculum = models.ForeignKey(StudyCurriculum, on_delete=models.CASCADE, related_name='schedules')
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


class StudyStudentManager(models.Manager):
    def with_select_related(self):
        return self.select_related('curriculum', 'curriculum__organization', 'curriculum__category')

    @staticmethod
    def _with_prefetch_related_to_results(queryset):
        return queryset.prefetch_related(
            models.Prefetch(
                'results', queryset=StudyResult.objects.select_related('psat'), to_attr='result_list')
        )

    def get_filtered_qs_by_category(self, category):
        return self.with_select_related().filter(curriculum__category=category).order_by('rank_total')

    def get_filtered_qs_by_category_for_catalog(self, category):
        queryset = self.get_filtered_qs_by_category(category)
        return self._with_prefetch_related_to_results(queryset)

    def get_filtered_qs_by_curriculum(self, curriculum):
        return self.with_select_related().filter(curriculum=curriculum).order_by('rank_total')

    def get_filtered_qs_by_curriculum_for_catalog(self, curriculum):
        queryset = self.get_filtered_qs_by_curriculum(curriculum)
        return self._with_prefetch_related_to_results(queryset)

    def get_filtered_qs_by_user(self, user):
        return (
            self.with_select_related().filter(user=user)
            .annotate(score_count=models.Count('results', filter=models.Q(results__score__gt=0)))
            .order_by('-id')
        )

    def get_filtered_student(self, curriculum, user):
        return self.with_select_related().filter(curriculum=curriculum, user=user).first()

    def get_filtered_qs_by_curriculum_for_rank(self, curriculum, **kwargs):
        return self.filter(curriculum=curriculum, **kwargs).annotate(
            rank=models.Window(expression=functions.Rank(), order_by=[models.F('score_total').desc()]))


class StudyStudent(models.Model):
    objects = StudyStudentManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정 일시')
    curriculum = models.ForeignKey(StudyCurriculum, models.CASCADE, related_name='students')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, default='', verbose_name='이름')
    user = models.ForeignKey(
        User, models.SET_NULL, null=True, blank=True, related_name='psat_study_students')
    score_total = models.PositiveSmallIntegerField(default=0, verbose_name='총점')
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
        return f'[PSAT]StudyStudent(#{self.id}):{self.curriculum_info}-{self.student_info}'

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


class StudyAnswerManager(models.Manager):
    def with_select_related(self):
        return self.select_related('student', 'problem', 'problem__psat', 'problem__problem')

    def get_filtered_qs_by_student(self, student, **kwargs):
        return (
            self.with_select_related().filter(student=student, **kwargs)
            .order_by('problem__psat__round', 'problem__problem__subject')
            .annotate(
                round=models.F('problem__psat__round'),
                subject=get_annotation_for_subject(),
                is_correct=get_annotation_for_is_correct(),
            )
            .values('round', 'subject', 'is_correct')
        )


class StudyAnswer(models.Model):
    objects = StudyAnswerManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    student = models.ForeignKey(StudyStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(StudyProblem, on_delete=models.CASCADE, related_name='answers')
    answer = models.IntegerField(choices=choices.answer_choice, default=0, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_답안'
        db_table = 'a_psat_study_answer'
        ordering = ['student', 'problem']
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_psat_study_answer')
        ]

    def __str__(self):
        return f'[PSAT]StudyAnswer(#{self.id}):{self.curriculum_info}-{self.student_info}-{self.problem_info}'

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


class StudyAnswerCountManager(models.Manager):
    def with_select_related(self):
        return self.select_related('problem', 'problem__psat', 'problem__problem')

    def get_filtered_qs_by_psat(self, psat):
        return self.filter(problem__psat=psat).annotate(no=models.F('problem__number')).order_by('no')


class StudyAnswerCount(abstract_models.AnswerCount):
    objects = StudyAnswerCountManager()
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


class StudyResultManager(models.Manager):
    def with_select_related(self):
        return self.select_related(
            'student', 'psat', 'student__curriculum',
            'student__curriculum__category', 'student__curriculum__organization',
        )

    def get_filtered_qs_ordered_by_psat_round(self, curriculum, **kwargs):
        return self.filter(student__curriculum=curriculum, **kwargs).order_by(
            'psat__round').values('score', round=models.F('psat__round'))

    def get_result_count_dict_by_category(self, category):
        queryset = self.filter(student__curriculum__category=category, score__isnull=False).values(
            'student').annotate(result_count=models.Count('id')).order_by('student')
        return {q['student']: q['result_count'] for q in queryset}

    def get_result_count_dict_by_curriculum(self, curriculum):
        queryset = self.filter(student__curriculum=curriculum, score__isnull=False).values(
            'student').annotate(result_count=models.Count('id')).order_by('student')
        return {q['student']: q['result_count'] for q in queryset}


class StudyResult(models.Model):
    objects = StudyResultManager()
    student = models.ForeignKey(StudyStudent, on_delete=models.CASCADE, related_name='results')
    psat = models.ForeignKey(StudyPsat, on_delete=models.CASCADE, related_name='results')
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
        return f'[PSAT]StudyResult(#{self.id}):{self.student.student_info}'

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
        return f'[PSAT]StudyAnswerCountTopRank(#{self.id}):{self.problem_info}'

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


def get_annotation_for_subject():
    return models.Case(
        models.When(problem__problem__subject='헌법', then=models.Value('subject_0')),
        models.When(problem__problem__subject='언어', then=models.Value('subject_1')),
        models.When(problem__problem__subject='자료', then=models.Value('subject_2')),
        models.When(problem__problem__subject='상황', then=models.Value('subject_3')),
        default=models.Value(''),
        output_field=models.CharField(),
    )


def get_annotation_for_is_correct():
    return models.Case(
        models.When(answer=models.F('problem__problem__answer'), then=models.Value(True)),
        default=models.Value(False),
        output_field=models.BooleanField(),
    )

