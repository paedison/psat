from django.db import models


class PredictCategoryQuerySet(models.QuerySet):
    def filtered_category_by_psat_unit(self, unit=None):
        if unit:
            return self.filter(unit=unit).order_by('order')
        return self.order_by('order')


class PredictStatisticsQuerySet(models.QuerySet):
    pass


class PredictStudentQuerySet(models.QuerySet):
    def average_scores_over(self, psat, score: int):
        return self.filter(psat=psat, score__average__gte=score).values_list('score__average', flat=True)

    def registered_psat_student(self, user, psat_list):
        return (
            self.select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .filter(user=user, psat__in=psat_list).order_by('id')
        )

    def filtered_student_by_psat(self, psat):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        return (
            self.select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .filter(psat=psat)
            .order_by('psat__year', 'psat__order', 'rank_total__average')
            .annotate(
                unit=models.F('category__unit'),
                department=models.F('category__department'),
                latest_answer_time=models.Max('answers__created_at'),
                answer_count=models.Count('answers'),
                **annotate_dict
            )
        )

    def psat_student_with_answer_count(self, user, psat):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        qs_student = (
            self.select_related('psat', 'category', 'score', 'rank_total', 'rank_category', 'user')
            .filter(user=user, psat=psat)
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


class PredictAnswerQuerySet(models.QuerySet):
    def filtered_by_psat_student(self, student):
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

    def filtered_by_psat_student_and_stat_type(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(problem__psat=student.psat).values('problem__subject').annotate(
            participant_count=models.Count('student_id', distinct=True))
        if stat_type == 'department':
            qs = qs.filter(student__category__department=student.category.department)
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs

    def filtered_by_psat_student_and_sub(self, student, sub: str):
        return self.filter(student=student, problem__subject=sub).annotate(
            answer_correct=models.F('problem__answer'), answer_student=models.F('answer'))


class PredictAnswerCountQuerySet(models.QuerySet):
    def filtered_by_psat_and_subject(self, psat, subject=None):
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
            self.filter(problem__psat=psat)
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

    def predict_filtered_by_psat(self, psat):
        return self.filter(problem__psat=psat).annotate(
            no=models.F('problem__number'),
            number=models.F('problem__number'),
            sub=models.F('problem__subject'),
            subject=models.F('problem__subject'),
            ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class PredictScoreQuerySet(models.QuerySet):
    def predict_filtered_scores_of_student(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(student__psat=student.psat)
        if stat_type == 'department':
            qs = qs.filter(student__category__department=student.category.department)
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs.values()
