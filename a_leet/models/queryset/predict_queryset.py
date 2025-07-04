from django.db import models


class PredictStatisticsQuerySet(models.QuerySet):
    def filtered_statistics_by_leet(self, leet):
        return self.select_related('leet').filter(leet=leet).order_by('id')


class PredictStudentQuerySet(models.QuerySet):
    def annotate_score_and_rank(self):
        annotate_dict = {
            'participants': models.F(f'rank__participants'),
            'participants_1': models.F(f'rank_aspiration_1__participants'),
            'participants_2': models.F(f'rank_aspiration_2__participants'),
            'filtered_participants': models.F(f'rank__filtered_participants'),
            'filtered_participants_1': models.F(f'rank_aspiration_1__filtered_participants'),
            'filtered_participants_2': models.F(f'rank_aspiration_2__filtered_participants'),
        }
        field_dict = {'0': 'subject_0', '1': 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = models.F(f'score__raw_{fld}')
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = models.F(f'rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = models.F(f'rank_aspiration_2__{fld}')
            annotate_dict[f'filtered_rank_{key}'] = models.F(f'rank__filtered_{fld}')
            annotate_dict[f'filtered_rank_{key}_aspiration_1'] = models.F(f'rank_aspiration_1__filtered_{fld}')
            annotate_dict[f'filtered_rank_{key}_aspiration_2'] = models.F(f'rank_aspiration_2__filtered_{fld}')
        return self.annotate(**annotate_dict)

    @staticmethod
    def get_annotate_dict_for_score_and_rank():
        annotate_dict = {
            'score_sum': models.F('score__sum'),
            'rank_num': models.F(f'rank__participants'),
            'rank_1_num': models.F(f'rank_aspiration_1__participants'),
            'rank_2_num': models.F(f'rank_aspiration_2__participants'),
            'filtered_rank_num': models.F(f'rank__filtered_participants'),
            'filtered_rank_1_num': models.F(f'rank_aspiration_1__filtered_participants'),
            'filtered_rank_2_num': models.F(f'rank_aspiration_2__filtered_participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
            annotate_dict[f'rank_1_{key}'] = models.F(f'rank_aspiration_1__{fld}')
            annotate_dict[f'rank_2_{key}'] = models.F(f'rank_aspiration_2__{fld}')
            annotate_dict[f'filtered_rank_{key}'] = models.F(f'rank__filtered_{fld}')
            annotate_dict[f'filtered_rank_1_{key}'] = models.F(f'rank_aspiration_1__filtered_{fld}')
            annotate_dict[f'filtered_rank_2_{key}'] = models.F(f'rank_aspiration_2__filtered_{fld}')
        return annotate_dict

    def average_scores_over(self, leet, score: int):
        return self.filter(leet=leet, score__sum__gte=score).values_list('score__sum', flat=True)

    def registered_leet_student(self, user, leet_list):
        return (
            self.select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2')
            .filter(user=user, leet__in=leet_list).order_by('id')
        )

    def filtered_student_by_leet(self, leet):
        return (
            self.annotate_score_and_rank()
            .select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2')
            .filter(leet=leet).order_by('leet__year', 'rank__sum')
            .annotate(
                latest_answer_time=models.Max('answers__created_at'),
                answer_count=models.Count('answers'),
                # **annotate_dict
            )
        )

    def leet_student_with_answer_count(self, user, leet):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        qs_student = (
            self.select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2', 'user')
            .filter(user=user, leet=leet).prefetch_related('answers')
            .annotate(**annotate_dict).order_by('id').last()
        )
        if qs_student:
            qs_student_answers = qs_student.answers.values(
                subject=models.F('problem__subject')).annotate(answer_count=models.Count('id'))
            answer_count_sum = 0
            for qs_sa in qs_student_answers:
                qs_student.answer_count[qs_sa['subject']] = qs_sa['answer_count']
                answer_count_sum += qs_sa['answer_count']
            qs_student.answer_count['총점'] = answer_count_sum
        return qs_student


class PredictAnswerQuerySet(models.QuerySet):
    def filtered_by_leet_student(self, student):
        fields = [
            'problem',
            'problem__predict_answer_count',
            'problem__predict_answer_count_top_rank',
            'problem__predict_answer_count_mid_rank',
            'problem__predict_answer_count_low_rank'
        ]
        result = models.Case(
            models.When(answer=models.F('problem__answer'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        predict_result = models.Case(
            models.When(
                answer=models.F('problem__predict_answer_count__answer_predict'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        return (
            self.select_related(*fields).filter(student=student)
            .annotate(subject=models.F('problem__subject'), result=result, predict_result=predict_result)
        )

    def filtered_by_leet_student_and_stat_type(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(problem__leet=student.leet).values('problem__subject').annotate(
            participant_count=models.Count('student_id', distinct=True))
        if stat_type != 'all':
            qs = qs.filter(**{f'student__{stat_type}': getattr(student, stat_type)})
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs

    def filtered_by_leet_student_and_sub(self, student, sub: str):
        return self.filter(student=student, problem__subject=sub).annotate(
            answer_official=models.F('problem__answer'), answer_student=models.F('answer'))


class PredictAnswerCountQuerySet(models.QuerySet):
    def filtered_by_leet_and_subject(self, leet, subject=None):
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

        annotate_dict['subject_code'] = models.Case(
                models.When(subject='헌법', then=0),
                models.When(subject='언어', then=1),
                models.When(subject='자료', then=2),
                models.When(subject='상황', then=3),
                default=4,
                output_field=models.IntegerField(),
            )

        qs_answer_count = (
            self.filter(problem__leet=leet)
            .annotate(**annotate_dict).order_by('subject_code', 'problem__number')
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

    def predict_filtered_by_leet(self, leet):
        return self.filter(problem__leet=leet).annotate(
            no=models.F('problem__number'),
            sub=models.F('problem__subject'),
            subject=models.F('problem__subject'),
            ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class PredictScoreQuerySet(models.QuerySet):
    def predict_filtered_scores_of_student(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(student__leet=student.leet)
        if stat_type != 'all':
            qs = qs.filter(**{f'student__{stat_type}': getattr(student, stat_type)})
        if is_filtered:
            qs = qs.filter(student__is_filtered=is_filtered)
        return qs.values()
