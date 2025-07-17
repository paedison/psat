from django.apps import apps
from django.db import models
from django.db.models import functions
from django.utils import timezone


class StudyCategoryQuerySet(models.QuerySet):
    def with_prefetch_related(self):
        return self.prefetch_related('psats')

    def annotate_student_count(self):
        return self.annotate(student_count=models.Count('curriculum__students')).order_by('-id')


class StudyPsatQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('category')

    def get_qs_psat(self, category):
        return self.with_select_related().filter(category=category)


class StudyProblemQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('psat', 'psat__category', 'problem', 'problem__psat')

    def opened_category_problem_count(self, category, opened_rounds):
        return self.filter(psat__category=category, psat__round__in=opened_rounds).count()

    def get_qs_study_problem(self, category):
        return self.filter(psat__category=category).select_related(
            'psat', 'psat__category', 'problem', 'problem__psat')

    def annotate_answer_count_in_category(self, category):
        annotate_dict = {
            'original_psat_id': models.F('problem__psat_id'),
            'season': models.F('psat__category__season'),
            'study_type': models.F('psat__category__study_type'),
            'round': models.F('psat__round'),
            'subject': models.F('problem__subject'),
            'ans_official': models.F('problem__answer'),
        }
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}_all'] = models.F(f'answer_count__{fld}')
            annotate_dict[f'{fld}_top'] = models.F(f'answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = models.F(f'answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = models.F(f'answer_count_low_rank__{fld}')
        return (
            self.filter(psat__category=category).order_by('psat__round', 'number').annotate(**annotate_dict)
            .select_related(
                'psat', 'psat__category', 'problem', 'problem__psat',
                'answer_count', 'answer_count_top_rank', 'answer_count_mid_rank', 'answer_count_low_rank',
            )
        )

    def get_ordered_qs_by_subject_field(self):
        subject = models.Case(
            models.When(problem__subject='헌법', then=models.Value('subject_0')),
            models.When(problem__subject='언어', then=models.Value('subject_1')),
            models.When(problem__subject='자료', then=models.Value('subject_2')),
            models.When(problem__subject='상황', then=models.Value('subject_3')),
            default=models.Value(''),
            output_field=models.CharField(),
        )
        return self.values('psat_id', 'problem__subject').annotate(
            subject=subject, count=models.Count('id')).order_by('psat_id', 'subject')


class StudyCurriculumQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('organization', 'category')

    def annotate_student_count(self):
        return (
            self.select_related('organization', 'category')
            .annotate(
                student_count=models.Count('students'),
                registered_student_count=models.Count(
                    'students', filter=models.Q(students__user__isnull=False)
                )
            )
            .order_by('-id')
        )

    def current_year_curriculum(self, organization, semester):
        return self.filter(organization__name=organization, year=timezone.now().year, semester=semester).first()


class StudyCurriculumScheduleQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('curriculum')

    def schedule_info(self):
        return (
            self.values('curriculum')
            .annotate(
                study_rounds=models.Count('id'),
                earliest=models.Min('lecture_datetime'),
                latest=models.Max('lecture_datetime'),
            )
        )

    def open_curriculum_schedule(self, curriculum, current_time):
        return self.filter(
            curriculum=curriculum, lecture_open_datetime__lt=current_time).order_by('-lecture_number')

    def homework_schedule(self, curriculum, homework_round):
        return self.filter(curriculum=curriculum, homework_round=homework_round).first()


class StudyStudentQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('curriculum', 'curriculum__organization', 'curriculum__category')

    def _with_prefetch_related_to_results(self):
        study_result_model = apps.get_model('a_psat', 'StudyResult')
        return self.prefetch_related(
            models.Prefetch(
                'results', queryset=study_result_model.objects.select_related('psat'), to_attr='result_list')
        )

    def requested_student(self, curriculum, user):
        return (
            self.select_related('curriculum', 'curriculum__organization', 'curriculum__category')
            .filter(curriculum=curriculum, user=user).first()
        )

    def annotate_curriculum_rank(self, curriculum, **kwargs):
        return self.filter(curriculum=curriculum, **kwargs).annotate(
            rank=models.Window(expression=functions.Rank(), order_by=[models.F('score_total').desc()]))

    def students_with_results_in_category(self, category):
        return (
            self._with_prefetch_related_to_results()
            .select_related('curriculum', 'curriculum__organization', 'curriculum__category')
            .filter(curriculum__category=category)
            .order_by(models.F('rank_total').asc(nulls_last=True))
        )

    def students_with_results_in_curriculum(self, curriculum):
        return (
            self._with_prefetch_related_to_results()
            .select_related('curriculum', 'curriculum__organization', 'curriculum__category')
            .filter(curriculum=curriculum)
            .order_by(models.F('rank_total').asc(nulls_last=True))
        )

    def get_filtered_qs_by_user(self, user):
        return (
            self.select_related('curriculum', 'curriculum__organization', 'curriculum__category')
            .filter(user=user)
            .annotate(score_count=models.Count('results', filter=models.Q(results__score__gt=0)))
            .order_by('-id')
        )


class StudyAnswerQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('student', 'problem', 'problem__psat', 'problem__problem')

    def answers_with_correct(self, student, **kwargs):
        subject = models.Case(
            models.When(problem__problem__subject='헌법', then=models.Value('subject_0')),
            models.When(problem__problem__subject='언어', then=models.Value('subject_1')),
            models.When(problem__problem__subject='자료', then=models.Value('subject_2')),
            models.When(problem__problem__subject='상황', then=models.Value('subject_3')),
            default=models.Value(''),
            output_field=models.CharField(),
        )
        is_correct = models.Case(
            models.When(answer=models.F('problem__problem__answer'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField(),
        )
        return (
            self.select_related('student', 'problem', 'problem__psat', 'problem__problem')
            .filter(student=student, **kwargs)
            .order_by('problem__psat__round', 'problem__problem__subject')
            .annotate(round=models.F('problem__psat__round'), subject=subject, is_correct=is_correct)
            .values('round', 'subject', 'is_correct')
        )

    def answers_in_homework_rounds(self, student, homework_rounds):
        return (
            self.select_related('student', 'problem', 'problem__psat', 'problem__problem')
            .filter(student=student, problem__psat__round__in=homework_rounds)
        )

    def get_study_answer_distribution(self, rank_type):
        lookup_field = f'student__rank_total'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants = models.F('student__curriculum__category__participants')

        lookup_exp = {}
        if rank_type == 'top':
            lookup_exp[f'{lookup_field}__lte'] = participants * top_rank_threshold
        elif rank_type == 'mid':
            lookup_exp[f'{lookup_field}__gt'] = participants * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants * mid_rank_threshold
        elif rank_type == 'low':
            lookup_exp[f'{lookup_field}__gt'] = participants * mid_rank_threshold

        return (
            self.filter(**lookup_exp).values('problem_id', 'answer')
            .annotate(count=models.Count('id')).order_by('problem_id', 'answer')
        )


class StudyAnswerCountQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('problem', 'problem__psat', 'problem__problem')

    def get_filtered_qs_by_psat(self, psat):
        return self.filter(problem__psat=psat).annotate(no=models.F('problem__number')).order_by('no')


class StudyResultQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related(
            'student', 'psat', 'student__curriculum',
            'student__curriculum__category', 'student__curriculum__organization',
        )

    def opened_round_student_results(self, student, opened_rounds):
        return self.select_related('psat').filter(
            student=student, psat__round__in=opened_rounds).order_by('-psat__round')

    def opened_round_scores(self, curriculum, opened_rounds):
        return self.filter(student__curriculum=curriculum, psat__round__in=opened_rounds).order_by(
            'psat__round').values('score', round=models.F('psat__round'))

    def user_result(self, pk, user):
        return (
            self.select_related(
                'student', 'psat', 'student__curriculum',
                'student__curriculum__category', 'student__curriculum__organization',)
            .filter(pk=pk, student__user=user).first()
        )

    def homework_round_result(self, student, homework_round):
        return self.filter(student=student, psat__round=homework_round).first()

    def get_result_count_dict_by_category(self, category):
        queryset = self.filter(student__curriculum__category=category, score__isnull=False).values(
            'student').annotate(result_count=models.Count('id')).order_by('student')
        return {q['student']: q['result_count'] for q in queryset}

    def get_result_count_dict_by_curriculum(self, curriculum):
        queryset = self.filter(student__curriculum=curriculum, score__isnull=False).values(
            'student').annotate(result_count=models.Count('id')).order_by('student')
        return {q['student']: q['result_count'] for q in queryset}

    def get_rank_calculated(self, qs_student, psats):
        return self.filter(student__in=qs_student, psat__in=psats).annotate(
            rank_calculated=models.Case(
                models.When(score__isnull=True, then=models.Value(None)),
                default=models.Window(
                    expression=functions.Rank(),
                    partition_by=models.F('psat'),
                    order_by=[models.F('score').desc()]),
                output_field=models.IntegerField(),
            )
        )
