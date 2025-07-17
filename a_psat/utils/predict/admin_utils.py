__all__ = [
    'AdminDetailContext', 'AdminCreateContext', 'AdminUpdateContext', 'AdminExportExcelContext',
]

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
from django.db.models import Count, F, QuerySet, Window
from django.db.models.functions import Rank

from a_psat import forms
from a_psat.models.choices import answer_choice
from a_psat.utils.variables import ModelData, SubjectVariants
from common.utils import HtmxHttpRequest, get_paginator_context
from common.utils.export_excel_methods import *
from common.utils.modify_models_methods import *

_model = ModelData()

UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class AdminDetailContext:
    request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._psat = self._context['psat']
        self._subject_variants = SubjectVariants(_psat=self._psat)

        self._subject_vars = self._subject_variants.subject_vars
        self._subject_vars_avg = self._subject_variants.subject_vars_avg
        self._qs_problem = _model.problem.objects.filtered_problem_by_psat(self._psat)
        self._qs_answer_count = _model.ac_all.objects.predict_filtered_by_psat(self._psat)

    def get_admin_problem_context(self):
        page_number = self.request.GET.get('page', 1)
        return {'problem_context': get_paginator_context(self._qs_problem, page_number)}

    def get_admin_statistics_context(self, per_page=10) -> dict:
        page_number = self.request.GET.get('page', 1)
        total_data, filtered_data = self.get_admin_statistics_data()
        total_context = get_paginator_context(total_data, page_number, per_page)
        filtered_context = get_paginator_context(filtered_data, page_number, per_page)
        total_context.update({
            'id': '0', 'title': '전체', 'prefix': 'TotalStatistics', 'header': 'total_statistics_list',
        })
        filtered_context.update({
            'id': '1', 'title': '필터링', 'prefix': 'FilteredStatistics', 'header': 'filtered_statistics_list',
        })
        return {'statistics_context': {'total': total_context, 'filtered': filtered_context}}

    def get_admin_statistics_data(self) -> tuple[list, list]:
        department_list = list(
            _model.category.objects.filter(exam=self._psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        total_data, filtered_data = defaultdict(dict), defaultdict(dict)
        total_scores, filtered_scores = defaultdict(dict), defaultdict(dict)
        for department in department_list:
            total_data[department] = {'department': department, 'participants': 0}
            filtered_data[department] = {'department': department, 'participants': 0}
            total_scores[department] = {sub: [] for sub in self._subject_vars_avg}
            filtered_scores[department] = {sub: [] for sub in self._subject_vars_avg}

        qs_students = (
            _model.student.objects.filter(psat=self._psat)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .annotate(
                department=F('category__department'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                subject_2=F('score__subject_2'),
                subject_3=F('score__subject_3'),
                average=F('score__average'),
            )
        )
        for qs_s in qs_students:
            for sub, (_, field, _, _) in self._subject_vars_avg.items():
                score = getattr(qs_s, field)
                if score is not None:
                    total_scores['전체'][sub].append(score)
                    total_scores[qs_s.department][sub].append(score)
                    if qs_s.is_filtered:
                        filtered_scores['전체'][sub].append(score)
                        filtered_scores[qs_s.department][sub].append(score)

        self.update_admin_statistics_data(total_data, total_scores)
        self.update_admin_statistics_data(filtered_data, filtered_scores)

        return list(total_data.values()), list(filtered_data.values())

    def update_admin_statistics_data(self, data_statistics: dict, score_list: dict) -> None:
        for department, score_dict in score_list.items():
            for sub, scores in score_dict.items():
                subject, fld, _, _ = self._subject_vars_avg[sub]
                participants = len(scores)

                sorted_scores = sorted(scores, reverse=True)
                max_score = top_score_10 = top_score_20 = avg_score = None
                if sorted_scores:
                    max_score = sorted_scores[0]
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    top_score_10 = sorted_scores[top_10_threshold - 1]
                    top_score_20 = sorted_scores[top_20_threshold - 1]
                    avg_score = round(sum(scores) / participants, 1)

                data_statistics[department][fld] = {
                    'field': fld,
                    'is_confirmed': True,
                    'sub': sub,
                    'subject': subject,
                    'participants': participants,
                    'max': max_score,
                    't10': top_score_10,
                    't20': top_score_20,
                    'avg': avg_score,
                }

    def get_admin_catalog_context(self, student_name=None) -> dict:
        page_number = self.request.GET.get('page', 1)
        total_list = _model.student.objects.filtered_student_by_psat(self._psat)
        if student_name:
            total_list = total_list.filter(name=student_name)
        filtered_list = total_list.filter(is_filtered=True)
        total_context = get_paginator_context(total_list, page_number)
        filtered_context = get_paginator_context(filtered_list, page_number)

        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
        for obj in filtered_context['page_obj']:
            obj.rank_tot_num = obj.filtered_rank_tot_num
            obj.rank_dep_num = obj.filtered_rank_dep_num
            for key, fld in field_dict.items():
                setattr(obj, f'rank_tot_{key}', getattr(obj, f'filtered_rank_tot_{key}'))
                setattr(obj, f'rank_dep_{key}', getattr(obj, f'filtered_rank_dep_{key}'))

        total_context.update({
            'id': '0', 'title': '전체', 'prefix': 'TotalCatalog', 'header': 'total_catalog_list',
        })
        filtered_context.update({
            'id': '1', 'title': '필터링', 'prefix': 'FilteredCatalog', 'header': 'filtered_catalog_list',
        })

        return {'catalog_context': {'total': total_context, 'filtered': filtered_context}}

    def get_admin_answer_context(self, subject=None, per_page=10) -> dict:
        page_number = self.request.GET.get('page', 1)
        sub_list = [sub for sub in self._subject_vars]
        qs_answer_count_group = {sub: [] for sub in self._subject_vars}
        answer_context = {}

        qs_answer_count = _model.ac_all.objects.filtered_by_psat_and_subject(self._psat, subject)
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            if sub not in qs_answer_count_group:
                qs_answer_count_group[sub] = []
            qs_answer_count_group[sub].append(qs_ac)

        for sub, qs_answer_count in qs_answer_count_group.items():
            if qs_answer_count:
                data_answers = self.get_admin_answer_data(qs_answer_count)
                context = get_paginator_context(data_answers, page_number, per_page)
                context.update({
                    'id': str(sub_list.index(sub)),
                    'title': sub,
                    'prefix': 'Answer',
                    'header': 'answer_list',
                    'answer_count': 4 if sub == '헌법' else 5,
                })
                answer_context[sub] = context

        return {'answer_context': answer_context}

    def get_admin_answer_data(self, qs_answer_count: QuerySet) -> QuerySet:
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            field = self._subject_vars[sub][1]
            ans_official = qs_ac.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            qs_ac.no = qs_ac.number
            qs_ac.ans_official = ans_official
            qs_ac.ans_official_circle = qs_ac.problem.get_answer_display()
            qs_ac.ans_predict_circle = answer_choice()[qs_ac.ans_predict] if qs_ac.ans_predict else None
            qs_ac.ans_list = answer_official_list
            qs_ac.field = field

            qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
            qs_ac.rate_correct_top = qs_ac.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_mid = qs_ac.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_low = qs_ac.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            try:
                qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
            except TypeError:
                qs_ac.rate_gap = None

        return qs_answer_count

    def get_admin_only_answer_context(self, queryset: QuerySet) -> dict:
        sub_list = self._subject_variants.sub_list
        query_dict = defaultdict(list)
        for query in queryset.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for idx, sub in enumerate(sub_list)
        }

    def get_admin_answer_predict_context(self):
        return {'answer_predict_context': self.get_admin_only_answer_context(self._qs_answer_count)}

    def get_admin_answer_official_context(self):
        return {'answer_official_context': self.get_admin_only_answer_context(self._qs_problem)}


@dataclass(kw_only=True)
class AdminCreateContext:
    form: forms.PredictPsatForm

    def __post_init__(self):
        year = self.form.cleaned_data['year']
        exam = self.form.cleaned_data['exam']
        self._psat = _model.psat.objects.get(year=year, exam=exam)

    def process_post_request(self):
        predict_psat, _ = _model.predict_psat.objects.get_or_create(psat=self._psat)
        predict_psat.is_active = True
        predict_psat.page_opened_at = self.form.cleaned_data['page_opened_at']
        predict_psat.exam_started_at = self.form.cleaned_data['exam_started_at']
        predict_psat.exam_finished_at = self.form.cleaned_data['exam_finished_at']
        predict_psat.answer_predict_opened_at = self.form.cleaned_data['answer_predict_opened_at']
        predict_psat.answer_official_opened_at = self.form.cleaned_data['answer_official_opened_at']
        predict_psat.predict_closed_at = self.form.cleaned_data['predict_closed_at']
        predict_psat.save()

        self.create_answer_count_model_instances()
        self.create_statistics_model_instances()

    def create_answer_count_model_instances(self) -> None:
        problems = _model.problem.objects.filter(psat=self._psat).order_by('id')
        for model in _model.ac_model_set.values():
            list_create = []
            for problem in problems:
                append_list_create(model, list_create, problem=problem)
            bulk_create_or_update(model, list_create, [], [])

    @with_bulk_create_or_update()
    def create_statistics_model_instances(self):
        category_model = _model.category
        department_list = list(
            category_model.objects.filter(exam=self._psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        list_create = []
        for department in department_list:
            append_list_create(category_model, list_create, psat=self._psat, department=department)
        return category_model, list_create, [], []


@dataclass(kw_only=True)
class AdminUpdateContext:
    request: HtmxHttpRequest
    psat: _model.psat

    def __post_init__(self):
        self._subject_variants = SubjectVariants(_psat=self.psat)
        self._subject_vars = self._subject_variants.subject_vars
        self._subject_vars_avg = self._subject_variants.subject_vars_avg
        self._sub_list = self._subject_variants.sub_list
        self._qs_student = _model.student.objects.filter(psat=self.psat).order_by('id')

    def update_problem_model_for_answer_official(self) -> tuple[bool | None, str]:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '정답을 업데이트했습니다.',
            False: '기존 정답과 일치합니다.',
        }
        list_create, list_update = [], []

        problem_model = _model.problem
        form = forms.UploadFileForm(self.request.POST, self.request.FILES)
        file = self.request.FILES.get('file')

        if form.is_valid():
            df = pd.read_excel(file, sheet_name='정답', header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = problem_model.objects.get(psat=self.psat, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except problem_model.DoesNotExist:
                            problem = problem_model(psat=self.psat, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(problem_model, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        return [self.update_score_model()]

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        result_list = []
        for _bool in [False, True]:
            for model in _model.rank_model_set.values():
                result_list.append(self.update_rank_model(model, _bool))
        return result_list

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        total_data, filtered_data = self.get_statistics_data()
        return [
            self.update_statistics_model(total_data, False),
            self.update_statistics_model(filtered_data, True),
        ]

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        result_list = []
        for _bool in [False, True]:
            for model in _model.ac_model_set.values():
                result_list.append(self.update_answer_count_model(model, _bool))
        return result_list

    @with_bulk_create_or_update()
    def update_score_model(self):
        score_model = _model.score
        list_create, list_update = [], []

        for student in self._qs_student:
            original_score_instance, _ = score_model.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self._sub_list):
                problem_count = 25 if sub == '헌법' else 40
                correct_count = 0

                qs_answer = (
                    _model.answer.objects.filter(student=student, problem__subject=sub)
                    .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
                )
                for entry in qs_answer:
                    answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                    correct_count += 1 if entry.answer_student in answer_correct_list else 0

                score = correct_count * 100 / problem_count
                score_list.append(score)
                fields_not_match.append(getattr(original_score_instance, f'subject_{idx}') != score)

            score_sum = sum(score_list[1:])
            average = round(score_sum / 3, 1)

            fields_not_match.append(original_score_instance.sum != score_sum)
            fields_not_match.append(original_score_instance.average != average)

            if any(fields_not_match):
                for idx, score in enumerate(score_list):
                    setattr(original_score_instance, f'subject_{idx}', score)
                original_score_instance.sum = score_sum
                original_score_instance.average = average
                list_update.append(original_score_instance)

        update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average']
        return score_model, list_create, list_update, update_fields

    @with_bulk_create_or_update()
    def update_rank_model(self, rank_model, is_filtered: bool):
        qs_student = self._qs_student
        prefix = ''
        if is_filtered:
            qs_student = self._qs_student.filter(is_filtered=is_filtered)
            prefix = 'filtered_'

        list_create = []
        list_update = []
        subject_count = len(self._sub_list)

        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        annotate_dict = {f'{prefix}rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
        annotate_dict[f'{prefix}rank_average'] = rank_func('score__average')

        participants = qs_student.count()
        for student in qs_student:
            rank_list = qs_student.annotate(**annotate_dict)
            if rank_model == _model.rank_category:
                rank_list = rank_list.filter(category=student.category)
                participants = rank_list.count()
            target, _ = rank_model.objects.get_or_create(student=student)

            fields_not_match = [getattr(target, f'{prefix}participants') != participants]
            for row in rank_list:
                if row.id == student.id:
                    for idx in range(subject_count):
                        fields_not_match.append(
                            getattr(target, f'{prefix}subject_{idx}') != getattr(row, f'{prefix}rank_{idx}')
                        )
                    fields_not_match.append(
                        getattr(target, f'{prefix}average') != getattr(row, f'{prefix}rank_average')
                    )

                    if any(fields_not_match):
                        for idx in range(subject_count):
                            setattr(target, f'{prefix}subject_{idx}', getattr(row, f'{prefix}rank_{idx}'))
                        setattr(target, f'{prefix}average', getattr(row, f'{prefix}rank_average'))
                        setattr(target, f'{prefix}participants', participants)
                        list_update.append(target)

        update_fields = [
            f'{prefix}subject_0', f'{prefix}subject_1', f'{prefix}subject_2',
            f'{prefix}subject_3', f'{prefix}average', f'{prefix}participants'
        ]
        return rank_model, list_create, list_update, update_fields

    def get_statistics_data(self) -> tuple[list, list]:
        department_list = list(
            _model.category.objects.filter(exam=self.psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        total_data, filtered_data = defaultdict(dict), defaultdict(dict)
        total_scores, filtered_scores = defaultdict(dict), defaultdict(dict)
        for department in department_list:
            total_data[department] = {'department': department, 'participants': 0}
            filtered_data[department] = {'department': department, 'participants': 0}
            total_scores[department] = {sub: [] for sub in self._subject_vars_avg}
            filtered_scores[department] = {sub: [] for sub in self._subject_vars_avg}

        qs_students = (
            _model.student.objects.filter(psat=self.psat)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .annotate(
                department=F('category__department'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                subject_2=F('score__subject_2'),
                subject_3=F('score__subject_3'),
                average=F('score__average'),
            )
        )
        for qs_s in qs_students:
            for sub, (_, fld, _, _) in self._subject_vars_avg.items():
                score = getattr(qs_s, fld)
                if score is not None:
                    total_scores['전체'][sub].append(score)
                    total_scores[qs_s.department][sub].append(score)
                    if qs_s.is_filtered:
                        filtered_scores['전체'][sub].append(score)
                        filtered_scores[qs_s.department][sub].append(score)

        self.update_statistics_data(total_data, total_scores)
        self.update_statistics_data(filtered_data, filtered_scores)

        return list(total_data.values()), list(filtered_data.values())

    def update_statistics_data(self, data_statistics: dict, score_list: dict) -> None:
        for department, score_dict in score_list.items():
            for sub, scores in score_dict.items():
                subject, fld, _, _ = self._subject_vars_avg[sub]
                participants = len(scores)

                sorted_scores = sorted(scores, reverse=True)
                max_score = top_score_10 = top_score_20 = avg_score = None
                if sorted_scores:
                    max_score = sorted_scores[0]
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    top_score_10 = sorted_scores[top_10_threshold - 1]
                    top_score_20 = sorted_scores[top_20_threshold - 1]
                    avg_score = round(sum(scores) / participants, 1)

                data_statistics[department][fld] = {
                    'field': fld,
                    'is_confirmed': True,
                    'sub': sub,
                    'subject': subject,
                    'participants': participants,
                    'max': max_score,
                    't10': top_score_10,
                    't20': top_score_20,
                    'avg': avg_score,
                }

    def update_statistics_model(self, data_statistics, is_filtered: bool) -> tuple[bool | None, str]:
        statistics_model = _model.statistics
        prefix = 'filtered_' if is_filtered else ''
        message_dict = get_update_messages('통계')
        list_update = []
        list_create = []

        for data_stat in data_statistics:
            department = data_stat['department']
            stat_dict = {'department': department}
            for (_, fld, _, _) in self._subject_vars_avg.values():
                stat_dict.update({
                    f'{prefix}{fld}': {
                        'participants': data_stat[fld]['participants'],
                        'max': data_stat[fld]['max'],
                        't10': data_stat[fld]['t10'],
                        't20': data_stat[fld]['t20'],
                        'avg': data_stat[fld]['avg'],
                    }
                })

            try:
                instance = statistics_model.objects.get(psat=self.psat, department=department)
                fields_not_match = any(
                    getattr(instance, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except statistics_model.DoesNotExist:
                list_create.append(statistics_model(psat=self.psat, **stat_dict))
        update_fields = [
            'department', f'{prefix}subject_0', f'{prefix}subject_1',
            f'{prefix}subject_2', f'{prefix}subject_3', f'{prefix}average',
        ]
        is_updated = bulk_create_or_update(statistics_model, list_create, list_update, update_fields)
        return is_updated, message_dict[is_updated]

    @with_bulk_create_or_update()
    def update_answer_count_model(self, answer_count_model, is_filtered: bool):
        prefix = 'filtered_' if is_filtered else ''

        list_update = []
        list_create = []

        lookup_field = f'student__rank_total__{prefix}average'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F(f'student__rank_total__{prefix}participants')

        lookup_exp = {}
        if is_filtered:
            lookup_exp['student__is_filtered'] = is_filtered
        if answer_count_model == _model.ac_top:
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif answer_count_model == _model.ac_mid:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif answer_count_model == _model.ac_low:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        qs_answer = (
            _model.answer.objects.filter(**lookup_exp)
            .select_related('student', 'student__rank_total')
            .values('problem_id', 'answer')
            .annotate(count=Count('id')).order_by('problem_id', 'answer')
        )
        answer_distribution_dict = defaultdict(lambda: {i: 0 for i in range(6)})
        for qs_a in qs_answer:
            answer_distribution_dict[qs_a['problem_id']][qs_a['answer']] = qs_a['count']

        count_fields = [
            f'{prefix}count_0', f'{prefix}count_1', f'{prefix}count_2', f'{prefix}count_3',
            f'{prefix}count_4', f'{prefix}count_5', f'{prefix}count_multiple',
        ]
        for problem_id, answer_distribution in answer_distribution_dict.items():
            answers = {f'{prefix}count_multiple': 0}
            for ans, cnt in answer_distribution.items():
                if ans <= 5:
                    answers[f'{prefix}count_{ans}'] = cnt
                else:
                    answers[f'{prefix}count_multiple'] = cnt
            answers[f'{prefix}count_sum'] = sum(answers[fld] for fld in count_fields)

            try:
                instance = answer_count_model.objects.get(problem_id=problem_id)
                fields_not_match = any(
                    getattr(instance, fld) != val for fld, val in answers.items()
                )
                if fields_not_match:
                    for fld, val in answers.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except answer_count_model.DoesNotExist:
                list_create.append(answer_count_model(problem_id=problem_id, **answers))
        update_fields = [
            'problem_id', f'{prefix}count_0', f'{prefix}count_1', f'{prefix}count_2', f'{prefix}count_3',
            f'{prefix}count_4', f'{prefix}count_5', f'{prefix}count_multiple', f'{prefix}count_sum',
        ]
        return answer_count_model, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminExportExcelContext:
    psat: _model.psat

    def __post_init__(self):
        self._subject_variants = SubjectVariants(_psat=self.psat)
        self._subject_vars = self._subject_variants.subject_vars
        self._subject_vars_avg = self._subject_variants.subject_vars_avg
        self._sub_list = [sub for sub in self._subject_vars]

    def get_statistics_response(self) -> HttpResponse:
        qs_statistics = _model.statistics.objects.filter(psat=self.psat).order_by('id')
        df = pd.DataFrame.from_records(qs_statistics.values())

        filename = f'{self.psat.full_reference}_성적통계.xlsx'
        drop_columns = ['id', 'psat_id']
        column_label = [('직렬', '')]

        subject_vars = self._subject_vars_avg
        subject_vars_total = subject_vars.copy()
        for sub, (subject, fld, idx, problem_count) in subject_vars.items():
            subject_vars_total[f'[필터링]{sub}'] = (f'[필터링]{subject}', f'filtered_{fld}', idx, problem_count)

        for (subject, fld, _, _) in subject_vars_total.values():
            drop_columns.append(fld)
            column_label.extend([
                (subject, '총 인원'), (subject, '최고'), (subject, '상위10%'), (subject, '상위20%'), (subject, '평균'),
            ])
            df_subject = pd.json_normalize(df[fld])
            df = pd.concat([df, df_subject], axis=1)

        df.drop(columns=drop_columns, inplace=True)
        df.columns = pd.MultiIndex.from_tuples(column_label)

        return get_response_for_excel_file(df, filename)

    def get_prime_id_response(self) -> HttpResponse:
        qs_student = _model.student.objects.filter(psat=self.psat).values(
            'id', 'created_at', 'name', 'prime_id').order_by('id')
        df = pd.DataFrame.from_records(qs_student)
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        filename = f'{self.psat.full_reference}_참여자명단.xlsx'
        column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        total_student_list = _model.student.objects.filtered_student_by_psat(self.psat)
        filtered_student_list = total_student_list.filter(is_filtered=True)
        filename = f'{self.psat.full_reference}_성적일람표.xlsx'

        df1 = self.get_catalog_df_for_excel(total_student_list)
        df2 = self.get_catalog_df_for_excel(filtered_student_list, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    def get_catalog_df_for_excel(self, student_list: QuerySet, is_filtered=False) -> pd.DataFrame:
        column_list = [
            'id', 'psat_id', 'category_id', 'user_id',
            'name', 'serial', 'password', 'is_filtered', 'prime_id', 'unit', 'department',
            'created_at', 'latest_answer_time', 'answer_count',
            'score_sum', 'rank_tot_num', 'rank_dep_num', 'filtered_rank_tot_num', 'filtered_rank_dep_num',
        ]
        for sub_type in ['0', '1', '2', '3', 'avg']:
            column_list.append(f'score_{sub_type}')
            for stat_type in ['rank', 'filtered_rank']:
                for dep_type in ['tot', 'dep']:
                    column_list.append(f'{stat_type}_{dep_type}_{sub_type}')
        df = pd.DataFrame.from_records(student_list.values(*column_list))
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        field_list = ['num', '0', '1', '2', '3', 'avg']
        if is_filtered:
            for key in field_list:
                df[f'rank_tot_{key}'] = df[f'filtered_rank_tot_{key}']
                df[f'rank_dep_{key}'] = df[f'filtered_rank_dep_{key}']

        drop_columns = []
        for key in field_list:
            drop_columns.extend([f'filtered_rank_tot_{key}', f'filtered_rank_dep_{key}'])

        column_label = [
            ('DB정보', 'ID'), ('DB정보', 'PSAT ID'), ('DB정보', '카테고리 ID'), ('DB정보', '사용자 ID'),
            ('수험정보', '이름'), ('수험정보', '수험번호'), ('수험정보', '비밀번호'),
            ('수험정보', '필터링 여부'), ('수험정보', '프라임 ID'), ('수험정보', '모집단위'), ('수험정보', '직렬'),
            ('답안정보', '등록일시'), ('답안정보', '최종답안 등록일시'), ('답안정보', '제출 답안수'),
            ('성적정보', 'PSAT 총점'), ('성적정보', '전체 총 인원'), ('성적정보', '직렬 총 인원'),
        ]
        for sub in self._subject_vars_avg:
            column_label.extend([(sub, '점수'), (sub, '전체 등수'), (sub, '직렬 등수')])

        df.drop(columns=drop_columns, inplace=True)
        df.columns = pd.MultiIndex.from_tuples(column_label)

        return df

    def get_answer_response(self) -> HttpResponse:
        qs_answer_count = _model.ac_all.objects.filtered_by_psat_and_subject(self.psat)
        filename = f'{self.psat.full_reference}_문항분석표.xlsx'

        df1 = self.get_answer_df_for_excel(qs_answer_count)
        df2 = self.get_answer_df_for_excel(qs_answer_count, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    @staticmethod
    def get_answer_df_for_excel(qs_answer_count: QuerySet, is_filtered=False) -> pd.DataFrame:
        prefix = 'filtered_' if is_filtered else ''
        column_list = ['id', 'problem_id', 'subject', 'number', 'ans_official', 'ans_predict']
        for rank_type in ['all', 'top', 'mid', 'low']:
            for num in ['1', '2', '3', '4', '5', 'sum']:
                column_list.append(f'{prefix}count_{num}_{rank_type}')

        column_label = [
            ('DB정보', 'ID'), ('DB정보', '문제 ID'),
            ('문제정보', '과목'), ('문제정보', '번호'), ('문제정보', '정답'), ('문제정보', '예상 정답'),
        ]
        for rank_type in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (rank_type, '①'), (rank_type, '②'), (rank_type, '③'),
                (rank_type, '④'), (rank_type, '⑤'), (rank_type, '합계'),
            ])

        df = pd.DataFrame.from_records(qs_answer_count.values(*column_list))
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return df
