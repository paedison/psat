from django.apps import apps
from django.db import models
from django.db.models import functions


class ProblemManager(models.Manager):
    def get_filtered_qs_by_psat(self, psat):
        return self.select_related('psat').filter(psat=psat).annotate(
            no=models.F('number'), ans=models.F('answer'), ans_official=models.F('answer')).order_by('subject', 'no')


class LectureManager(models.Manager):
    def order_by_subject_code(self):
        return self.get_queryset().annotate(
            subject_code=models.Case(
                models.When(subject='공부', then=0),
                models.When(subject='언어', then=1),
                models.When(subject='자료', then=2),
                models.When(subject='상황', then=3),
                default=4,
                output_field=models.IntegerField(),
            )
        ).order_by('subject_code')


class CategoryManager(models.Manager):
    def get_filtered_qs_by_unit(self, unit=None):
        if unit:
            return self.filter(unit=unit).order_by('order')
        return self.order_by('order')


class StatisticsManager(models.Manager):
    def get_filtered_qs_by_psat(self, psat):
        return self.filter(psat=psat).order_by('id')


class StudentManager(models.Manager):
    def with_select_related(self):
        return self.select_related('psat', 'category', 'score', 'rank_total', 'rank_category')

    def get_filtered_qs_by_psat(self, psat):
        return self.filter(psat=psat).order_by('id')

    @staticmethod
    def get_annotate_dict_for_score_and_rank():
        annotate_dict = {
            'score_sum': models.F('score__sum'),
            'rank_tot_num': models.F(f'rank_total__participants'),
            'rank_dep_num': models.F(f'rank_category__participants'),
            'filtered_rank_tot_num': models.F(f'rank_total__filtered_participants'),
            'filtered_rank_dep_num': models.F(f'rank_category__filtered_participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_tot_{key}'] = models.F(f'rank_total__{fld}')
            annotate_dict[f'rank_dep_{key}'] = models.F(f'rank_category__{fld}')
            annotate_dict[f'filtered_rank_tot_{key}'] = models.F(f'rank_total__filtered_{fld}')
            annotate_dict[f'filtered_rank_dep_{key}'] = models.F(f'rank_category__filtered_{fld}')
        return annotate_dict

    def get_filtered_qs_student_list_by_psat(self, psat):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        return (
            self.with_select_related().filter(psat=psat)
            .order_by('psat__year', 'psat__order', 'rank_total__average')
            .annotate(
                department=models.F('category__department'),
                latest_answer_time=models.Max('answers__created_at'),
                answer_count=models.Count('answers'),
                **annotate_dict
            )
        )

    def get_filtered_qs_by_user_and_psat_list(self, user, psat_list):
        return self.with_select_related().filter(user=user, psat__in=psat_list).order_by('id')

    def get_filtered_qs_by_psat_and_user_with_answer_count(self, user, psat):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        qs_student = (
            self.with_select_related().filter(user=user, psat=psat)
            .prefetch_related('answers')
            .annotate(department=models.F('category__department'), **annotate_dict)
            .order_by('id').last()
        )
        if qs_student:
            qs_answer_count = qs_student.answers.values(
                subject=models.F('problem__subject')).annotate(answer_count=models.Count('id'))
            average_answer_count = 0
            for q in qs_answer_count:
                qs_student.answer_count[q['subject']] = q['answer_count']
                if q['subject'] != '헌법':
                    average_answer_count += q['answer_count']
            qs_student.answer_count['평균'] = average_answer_count
        return qs_student


class AnswerManager(models.Manager):
    def with_selected_related(self):
        return self.select_related(
            'problem',
            'problem__predict_answer_count',
            'problem__predict_answer_count_top_rank',
            'problem__predict_answer_count_mid_rank',
            'problem__predict_answer_count_low_rank',
        )

    def get_filtered_qs_by_psat_and_student(self, student, psat):
        return self.with_selected_related().filter(
            student=student, problem__psat=psat).annotate(
            subject=models.F('problem__subject'),
            result=models.Case(
                models.When(answer=models.F('problem__answer'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
            predict_result=models.Case(
                models.When(
                    answer=models.F('problem__predict_answer_count__answer_predict'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            )
        )

    def get_filtered_qs_by_student_and_sub(self, student, sub: str):
        return self.filter(student=student, problem__subject=sub).annotate(
            answer_correct=models.F('problem__answer'), answer_student=models.F('answer'))

    def get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
            self, psat, student, stat_type='total', is_filtered=False):
        qs = self.filter(problem__psat=psat).values('problem__subject').annotate(
            participant_count=models.Count('student_id', distinct=True))
        if stat_type == 'department':
            qs = qs.filter(student__category__department=student.category.department)
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs


class AnswerCountManager(models.Manager):
    def get_filtered_qs_by_psat_and_subject(self, psat, subject=None):
        annotate_dict = {
            'subject': models.F('problem__subject'),
            'number': models.F('problem__number'),
            'ans_predict': models.F(f'problem__predict_answer_count__answer_predict'),
            'ans_official': models.F('problem__answer'),
        }
        for prefix in ['', 'filtered_']:
            for rank in ['all', 'top', 'mid', 'low']:
                for fld in ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']:
                    if rank == 'all':
                        f_expr = f'{prefix}{fld}'
                    else:
                        f_expr = f'problem__predict_answer_count_{rank}_rank__{prefix}{fld}'
                    annotate_dict[f'{prefix}{fld}_{rank}'] = models.F(f_expr)
        qs_answer_count = (
            self.filter(problem__psat=psat)
            .order_by('problem__subject', 'problem__number').annotate(**annotate_dict)
            .select_related(
                f'problem',
                f'problem__predict_answer_count_top_rank',
                f'problem__predict_answer_count_mid_rank',
                f'problem__predict_answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def get_filtered_qs_by_psat(self, psat):
        return self.filter(problem__psat=psat).annotate(
            no=models.F('problem__number'), sub=models.F('problem__subject'), ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class ScoreManager(models.Manager):
    def get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
            self, psat, student, stat_type='total', is_filtered=False):
        qs = self.filter(student__psat=psat)
        if stat_type == 'department':
            qs = qs.filter(student__category__department=student.category.department)
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs.values()


class StudyCategoryManager(models.Manager):
    def with_prefetch_related(self):
        return self.prefetch_related('psats')

    def annotate_student_count(self):
        return self.annotate(student_count=models.Count('curriculum__students')).order_by('-id')


class StudyPsatManager(models.Manager):
    def with_select_related(self):
        return self.select_related('category')

    def get_qs_psat(self, category):
        return self.with_select_related().filter(category=category)


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


class StudyCurriculumManager(models.Manager):
    def with_select_related(self):
        return self.select_related('organization', 'category')

    def annotate_student_count(self):
        return self.with_select_related().annotate(
            student_count=models.Count('students'),
            registered_student_count=models.Count('students', filter=models.Q(students__user__isnull=False))
        ).order_by('-id')


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


class StudyStudentManager(models.Manager):
    def with_select_related(self):
        return self.select_related('curriculum', 'curriculum__organization', 'curriculum__category')

    @staticmethod
    def _with_prefetch_related_to_results(queryset):
        study_result_model = apps.get_model('a_psat', 'StudyResult')
        return queryset.prefetch_related(
            models.Prefetch(
                'results', queryset=study_result_model.objects.select_related('psat'), to_attr='result_list')
        )

    def get_filtered_qs_by_category(self, category):
        return self.with_select_related().filter(curriculum__category=category).order_by(
            models.F('rank_total').asc(nulls_last=True))

    def get_filtered_qs_by_category_for_catalog(self, category):
        queryset = self.get_filtered_qs_by_category(category)
        return self._with_prefetch_related_to_results(queryset)

    def get_filtered_qs_by_curriculum(self, curriculum):
        return self.with_select_related().filter(curriculum=curriculum).order_by(
            models.F('rank_total').asc(nulls_last=True))

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


class StudyAnswerManager(models.Manager):
    def with_select_related(self):
        return self.select_related('student', 'problem', 'problem__psat', 'problem__problem')

    def get_filtered_qs_by_student(self, student, **kwargs):
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
            self.with_select_related().filter(student=student, **kwargs)
            .order_by('problem__psat__round', 'problem__problem__subject')
            .annotate(round=models.F('problem__psat__round'), subject=subject, is_correct=is_correct)
            .values('round', 'subject', 'is_correct')
        )


class StudyAnswerCountManager(models.Manager):
    def with_select_related(self):
        return self.select_related('problem', 'problem__psat', 'problem__problem')

    def get_filtered_qs_by_psat(self, psat):
        return self.filter(problem__psat=psat).annotate(no=models.F('problem__number')).order_by('no')


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
