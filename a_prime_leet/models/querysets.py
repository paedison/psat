from django.apps import apps
from django.db import models


class ProblemQuerySet(models.QuerySet):
    def get_qs_problem(self, **kwargs):
        return self.filter(**kwargs).order_by('subject', 'number')


class StudentQuerySet(models.QuerySet):
    def _with_select_related(self):
        return self.select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2')

    def _with_registries(self):
        return self.prefetch_related('registries')

    def order_by_rank(self, leet):
        return self.filter(leet=leet).order_by('rank__sum')

    def annotate_answer_log(self):
        return self.annotate(latest_answer_time=models.Max('answers__created_at'), answer_count=models.Count('answers'))

    def annotate_score_and_rank(self):
        annotate_dict = {
            'rank_num': models.F(f'rank__participants'),
            'rank_num_aspiration_1': models.F(f'rank_aspiration_1__participants'),
            'rank_num_aspiration_2': models.F(f'rank_aspiration_2__participants'),
        }
        field_dict = {'0': 'subject_0', '1': 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = models.F(f'score__raw_{fld}')
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = models.F(f'rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = models.F(f'rank_aspiration_2__{fld}')
        return self.annotate(**annotate_dict)

    # fake_detail_view / result_detail_view
    def get_student(self, **kwargs):
        return self._with_select_related().filter(**kwargs).annotate_score_and_rank().order_by('id').last()

    def get_qs_fake_student_by_stat_type(self, student, stat_type='total'):
        qs_student = self.filter(leet=student.leet)
        if stat_type != 'total':  # aspiration_1 | aspiration_2
            aspiration = getattr(student, stat_type)
            qs_student = qs_student.filter(
                models.Q(aspiration_1=aspiration) | models.Q(aspiration_2=aspiration)
            )
        return qs_student

    def get_qs_student_list_by_leet(self, leet, model_type: str):
        queryset = self._with_select_related()
        if model_type == 'fake':
            return queryset.order_by_rank(leet)
        elif model_type == 'result':
            return queryset._with_registries().annotate_answer_log().annotate_score_and_rank().order_by_rank(leet)

    def get_qs_fake_student_list_by_leet(self, leet):
        return self._with_select_related().order_by_rank(leet)

    def get_qs_result_student_list_by_leet(self, leet):
        return self._with_registries()._with_select_related().annotate_answer_log().order_by_rank(leet)

    def get_qs_predict_student(self, user, leet):
        qs_student = (
            self._with_select_related().filter(user=user, leet=leet).prefetch_related('answers')
            .annotate_score_and_rank().order_by('-id').last()
        )
        if qs_student:
            answer_count_model = apps.get_model('a_prime_leet', 'PredictAnswer')
            answer_count = answer_count_model.objects.filter(student=qs_student).aggregate(
                subject_0=models.Count('id', filter=models.Q(problem__subject='언어')),
                subject_1=models.Count('id', filter=models.Q(problem__subject='추리')),
            )
            answer_count['sum'] = sum(answer_count.values())
            qs_student.answer_count = answer_count
        return qs_student


class ResultRegistryQueryset(models.QuerySet):
    def _with_select_related(self):
        return self.select_related(
            'user', 'student', 'student__leet', 'student__score',
            'student__rank', 'student__rank_aspiration_1', 'student__rank_aspiration_2')

    @staticmethod
    def get_annotate_dict():
        annotate_dict = {
            'serial': models.F('student__serial'),
            'name': models.F('student__name'),
            'password': models.F('student__password'),
            'school': models.F('student__school'),
            'major': models.F('student__major'),
            'aspiration_1': models.F('student__aspiration_1'),
            'aspiration_2': models.F('student__aspiration_2'),
            'gpa': models.F('student__gpa'),
            'gpa_type': models.F('student__gpa_type'),
            'english': models.F('student__english'),
            'english_type': models.F('student__english_type'),
            'score_sum': models.F('student__score__sum'),
            'rank_num': models.F(f'student__rank__participants'),
            'rank_num_aspiration_1': models.F(f'student__rank_aspiration_1__participants'),
            'rank_num_aspiration_2': models.F(f'student__rank_aspiration_2__participants'),
        }
        field_dict = {'0': 'subject_0', '1': 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = models.F(f'student__score__raw_{fld}')
            annotate_dict[f'score_{key}'] = models.F(f'student__score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'student__rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = models.F(f'student__rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = models.F(f'student__rank_aspiration_2__{fld}')
        return annotate_dict

    def annotate_student_info_score_rank(self):
        annotate_dict = {
            'serial': models.F('student__serial'),
            'name': models.F('student__name'),
            'password': models.F('student__password'),
            'school': models.F('student__school'),
            'major': models.F('student__major'),
            'aspiration_1': models.F('student__aspiration_1'),
            'aspiration_2': models.F('student__aspiration_2'),
            'gpa': models.F('student__gpa'),
            'gpa_type': models.F('student__gpa_type'),
            'english': models.F('student__english'),
            'english_type': models.F('student__english_type'),
            'score_sum': models.F('student__score__sum'),
            'rank_num': models.F(f'student__rank__participants'),
            'rank_num_aspiration_1': models.F(f'student__rank_aspiration_1__participants'),
            'rank_num_aspiration_2': models.F(f'student__rank_aspiration_2__participants'),
        }
        field_dict = {'0': 'subject_0', '1': 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = models.F(f'student__score__raw_{fld}')
            annotate_dict[f'score_{key}'] = models.F(f'student__score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'student__rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = models.F(f'student__rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = models.F(f'student__rank_aspiration_2__{fld}')
        return self.annotate(**annotate_dict)

    def get_qs_registry_by_leet(self, leet):
        return self._with_select_related().filter(
            student__leet=leet).annotate_student_info_score_rank().order_by('-id')

    def get_qs_registry_by_user(self, user):
        annotate_dict = self.get_annotate_dict()
        return self._with_select_related().filter(
            user=user, student__leet__is_active=True).annotate(**annotate_dict).order_by('-student__leet')


class AnswerQueryset(models.QuerySet):
    def get_qs_answer_values_by_stat_type(self, student, stat_type='total', is_filtered=False):
        qs_answer = (
            self.filter(problem__leet=student.leet).values('problem__subject')
            .annotate(participant_count=models.Count('student_id', distinct=True))
        )
        if stat_type != 'total':  # aspiration_1 | aspiration_2
            aspiration = getattr(student, stat_type)
            qs_answer = qs_answer.filter(
                models.Q(student__aspiration_1=aspiration) | models.Q(student__aspiration_2=aspiration)
            )
        if is_filtered:
            qs_answer = qs_answer.filter(student__is_filtered=True)
        return qs_answer

    def get_qs_answer_with_sub_number(self, student):
        return self.filter(student=student).annotate(
            sub=models.F('problem__subject'), number=models.F('problem__number')).order_by('sub', 'number')

    def get_qs_answer_by_student(self, student):
        return self.filter(
            problem__leet=student.leet, student=student).annotate(
            is_correct=models.Case(
                models.When(answer=models.F('problem__answer'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            )
        ).select_related(
            'problem',
            'problem__result_answer_count',
            'problem__result_answer_count_top_rank',
            'problem__result_answer_count_mid_rank',
            'problem__result_answer_count_low_rank',
        )

    def prime_leet_qs_answer_by_student_with_predict_result(self, student):
        return self.filter(
            problem__leet=student.leet, student=student).annotate(
            subject=models.F('problem__subject'),
            real_result=models.Case(
                models.When(answer=models.F('problem__answer'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField(),
            ),
            predict_result=models.Case(
                models.When(answer=models.F('problem__predict_answer_count__answer_predict'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField(),
            )
        ).select_related(
            'problem',
            'problem__result_answer_count',
            'problem__result_answer_count_top_rank',
            'problem__result_answer_count_mid_rank',
            'problem__result_answer_count_low_rank',
            'problem__predict_answer_count',
            'problem__predict_answer_count_top_rank',
            'problem__predict_answer_count_mid_rank',
            'problem__predict_answer_count_low_rank',
        )


class AnswerCountQueryset(models.QuerySet):
    def filtered_by_leet(self, leet):
        return self.filter(problem__leet=leet)

    def get_qs_answer_count_with_all_ranks(self, leet, model_type='result', subject=None):
        annotate_dict = {
            'subject': models.F('problem__subject'),
            'number': models.F('problem__number'),
            'ans_predict': models.F(f'problem__{model_type}_answer_count__answer_predict'),
            'ans_official': models.F('problem__answer'),
        }
        prefix_list = [''] if model_type != 'predict' else ['', 'filtered_']
        for prefix in prefix_list:
            for rank in ['all', 'top', 'mid', 'low']:
                for fld in ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']:
                    if rank == 'all':
                        f_expr = f'{prefix}{fld}'
                    else:
                        f_expr = f'problem__{model_type}_answer_count_{rank}_rank__{prefix}{fld}'
                    annotate_dict[f'{prefix}{fld}_{rank}'] = models.F(f_expr)
        qs_answer_count = (
            self.filtered_by_leet(leet)
            .order_by('problem__subject', 'problem__number').annotate(**annotate_dict)
            .select_related(
                f'problem',
                f'problem__{model_type}_answer_count_top_rank',
                f'problem__{model_type}_answer_count_mid_rank',
                f'problem__{model_type}_answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def get_qs_answer_count(self, leet):
        return self.filtered_by_leet(leet).annotate(
            no=models.F('problem__number'), sub=models.F('problem__subject'), ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class ScoreQueryset(models.QuerySet):
    def get_qs_score_by_stat_type(self, student, stat_type='total', is_filtered=False):
        qs_score = self.filter(student__leet=student.leet)
        if stat_type != 'total':
            aspiration = getattr(student, stat_type)
            qs_score = qs_score.filter(
                models.Q(student__aspiration_1=aspiration) | models.Q(student__aspiration_2=aspiration)
            )
        if is_filtered:
            qs_score = qs_score.filter(student__is_filtered=True)
        return qs_score.values()
