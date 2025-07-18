__all__ = [
    'AdminListData', 'AdminDetailData',
    'AdminCreateData', 'AdminUpdateData',
    'AdminExportExcelData',
]

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F, QuerySet, Avg, StdDev, Q
from scipy.stats import rankdata

from a_leet import models, forms
from a_leet.utils.common_utils import *
from common.utils import HtmxHttpRequest, get_paginator_context
from common.utils.export_excel_methods import *
from common.utils.modify_models_methods import *

UPDATE_MESSAGES = {
    'raw_score': get_update_messages('원점수'),
    'score': get_update_messages('표준점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class AdminListData:
    _request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

    def get_predict_leet_context(self):
        predict_leet_list = models.PredictLeet.objects.select_related('leet')
        return get_paginator_context(predict_leet_list, self.page_number)


@dataclass(kw_only=True)
class AdminDetailData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._subject_vars = leet_context.subject_vars
        self._qs_problem = self._model.problem.objects.filtered_problem_by_leet(self._leet)

        self.exam_subject = request_data.exam_subject
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

        self.statistics = AdminDetailStatisticsData(_request=self._request, _leet=self._leet)
        self.catalog = AdminDetailCatalogData(_request=self._request, _leet=self._leet)
        self.answer = AdminDetailAnswerData(_request=self._request, _leet=self._leet)

    def get_problem_context(self):
        return {'problem_context': get_paginator_context(self._qs_problem, self.page_number)}

    def get_answer_predict_context(self):
        qs_answer_count = self._model.ac_all.objects.predict_filtered_by_leet(self._leet)
        return {'answer_predict_context': self.get_answer_dict(qs_answer_count)}

    def get_answer_official_context(self):
        return {'answer_official_context': self.get_answer_dict(self._qs_problem)}

    def get_answer_dict(self, queryset: QuerySet) -> dict:
        query_dict = defaultdict(list)
        for query in queryset.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for sub, (_, _, idx, _) in self._subject_vars.items()
        }


@dataclass(kw_only=True)
class AdminDetailStatisticsData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._subject_fields_sum_first = leet_context.subject_fields_sum_first
        self.page_number = request_data.page_number

    def get_admin_statistics_context(self, per_page=10) -> dict:
        return {
            'statistics_context': {
                'total': self.get_detailed_context(per_page, False),
                'filtered': self.get_detailed_context(per_page, True),
            }
        }

    def get_detailed_context(self, per_page, is_filtered: bool):
        qs_statistics = self._model.statistics.objects.filtered_statistics_by_leet(self._leet)
        data_all = qs_statistics[0] if qs_statistics else None
        data_others = qs_statistics[1:]
        context = get_paginator_context(data_others, self.page_number, per_page)

        if data_all:
            self.update_page_obj(data_all, is_filtered)
        if context['page_obj']:
            for obj in context['page_obj']:
                self.update_page_obj(obj, is_filtered)

        context.update({
            'id': '1' if is_filtered else '0',
            'title': '필터링' if is_filtered else '전체',
            'prefix': 'FilteredStatistics' if is_filtered else 'TotalStatistics',
            'header': 'filtered_statistics_list' if is_filtered else 'total_statistics_list',
            'all': data_all,
        })

        return context

    def update_page_obj(self, obj, is_filtered: bool):
        prefix = 'filtered_' if is_filtered else ''
        stat_list = ['max', 't10', 't25', 't50', 'avg']
        participants_field = ['participants', 'participants_1', 'participants_2']

        obj.members = {fld: getattr(obj, f'{prefix}sum').get(fld) for fld in participants_field}
        obj.stat_data = {
            fld: {
                stat: {
                    'score': getattr(obj, f'{prefix}{fld}').get(stat),
                    'raw_score': getattr(obj, f'{prefix}raw_{fld}').get(stat)
                } for stat in stat_list
            } for fld in self._subject_fields_sum_first
        }


@dataclass(kw_only=True)
class AdminDetailCatalogData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._subject_fields_sum_first = leet_context.subject_fields_sum_first

        self.page_number = request_data.page_number
        self.student_name = request_data.student_name

    def get_admin_catalog_context(self, for_search=False) -> dict:
        return {
            'catalog_context': {
                'total': self.get_detailed_context(for_search, False),
                'filtered': self.get_detailed_context(for_search, True),
            }
        }

    def get_detailed_context(self, for_search: bool, is_filtered: bool) -> dict:
        qs_student = self._model.student.objects.filtered_student_by_leet(self._leet)
        if for_search:
            qs_student = qs_student.filter(name=self.student_name)
        if is_filtered:
            qs_student = qs_student.filter(is_filtered=True)
        context = get_paginator_context(qs_student, self.page_number)

        for obj in context['page_obj']:
            self.update_page_obj(obj, is_filtered)

        context.update({
            'id': '1' if is_filtered else '0',
            'title': '필터링' if is_filtered else '전체',
            'prefix': 'FilteredCatalog' if is_filtered else 'TotalCatalog',
            'header': 'filtered_catalog_list' if is_filtered else 'total_catalog_list',
        })

        return context

    def update_page_obj(self, obj, is_filtered: bool):
        prefix = 'filtered_' if is_filtered else ''
        rank_model_set = ['rank', 'rank_aspiration_1', 'rank_aspiration_2']
        participants_field = ['participants', 'participants_1', 'participants_2']

        def get_rank_info(target_student, field: str):
            rank_info = {}
            for rank_model in rank_model_set:
                rank = ratio = None
                target_rank = getattr(target_student, rank_model, None)
                if target_rank:
                    rank = getattr(target_rank, f'{prefix}{field}')
                    participants = getattr(target_rank, f'{prefix}participants')
                    if rank and participants:
                        ratio = round(rank * 100 / participants, 1)
                rank_info[rank_model] = {'integer': rank, 'ratio': ratio}
            return rank_info

        if hasattr(obj, 'rank'):
            obj.members = {fld: getattr(obj.rank, f'{prefix}sum') for fld in participants_field}
        if hasattr(obj, 'score'):
            obj.stat_data = {
                fld: {
                    'score': getattr(obj.score, fld, ''),
                    'raw_score': getattr(obj.score, f'raw_{fld}', ''),
                    'rank_info': get_rank_info(obj, f'{fld}'),
                } for fld in self._subject_fields_sum_first
            }


@dataclass(kw_only=True)
class AdminDetailAnswerData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._subject_vars = leet_context.subject_vars
        self.exam_subject = request_data.exam_subject
        self.page_number = request_data.page_number

    def get_admin_answer_context(self, for_pagination=False, per_page=10) -> dict:
        sub_list = [sub for sub in self._subject_vars]
        qs_answer_count_group = {sub: [] for sub in self._subject_vars}
        answer_context = {}

        subject = self.exam_subject if for_pagination else None
        qs_answer_count = self._model.ac_all.objects.filtered_by_leet_and_subject(self._leet, subject)
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            if sub not in qs_answer_count_group:
                qs_answer_count_group[sub] = []
            qs_answer_count_group[sub].append(qs_ac)

        for sub, qs_answer_count in qs_answer_count_group.items():
            if qs_answer_count:
                data_answers = self.get_answer_data(qs_answer_count)
                context = get_paginator_context(data_answers, self.page_number, per_page)
                context.update({
                    'id': str(sub_list.index(sub)),
                    'title': sub,
                    'prefix': 'Answer',
                    'header': 'answer_list',
                    'answer_count': 5,
                })
                answer_context[sub] = context

        return {'answer_context': answer_context}

    def get_answer_data(self, qs_answer_count: QuerySet) -> QuerySet:
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
            qs_ac.ans_predict_circle = models.choices.answer_choice()[qs_ac.ans_predict] if qs_ac.ans_predict else None
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


@dataclass(kw_only=True)
class AdminCreateData:
    _form: forms.PredictLeetForm

    def __post_init__(self):
        year = self._form.cleaned_data['year']
        self._leet = models.Leet.objects.get(year=year)

    def process_post_request(self):
        self.create_predict_leet_model_instance()
        self.create_statistics_model_instances()
        self.create_answer_count_model_instances()

    def create_predict_leet_model_instance(self):
        predict_leet, _ = models.PredictLeet.objects.get_or_create(leet=self._leet)
        predict_leet.is_active = True
        predict_leet.page_opened_at = self._form.cleaned_data['page_opened_at']
        predict_leet.exam_started_at = self._form.cleaned_data['exam_started_at']
        predict_leet.exam_finished_at = self._form.cleaned_data['exam_finished_at']
        predict_leet.answer_predict_opened_at = self._form.cleaned_data['answer_predict_opened_at']
        predict_leet.answer_official_opened_at = self._form.cleaned_data['answer_official_opened_at']
        predict_leet.predict_closed_at = self._form.cleaned_data['predict_closed_at']
        predict_leet.save()

    @with_bulk_create_or_update()
    def create_statistics_model_instances(self):
        aspirations = models.choices.get_aspirations()
        list_create = []
        for aspiration in aspirations:
            append_list_create(models.PredictStatistics, list_create, leet=self._leet, aspiration=aspiration)
        return models.PredictStatistics, list_create, [], []

    def create_answer_count_model_instances(self) -> None:
        problems = models.Problem.objects.filter(leet=self._leet).order_by('id')
        model_list = [
            models.PredictAnswerCount,
            models.PredictAnswerCountTopRank,
            models.PredictAnswerCountMidRank,
            models.PredictAnswerCountLowRank,
        ]
        for model in model_list:
            list_create = []
            for problem in problems:
                append_list_create(model, list_create, problem=problem)
            bulk_create_or_update(model, list_create, [], [])


@dataclass(kw_only=True)
class AdminUpdateData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        request_data = RequestContext(_request=self._request)
        self.view_type = request_data.view_type

        self.answer_official = AdminUpdateAnswerOfficialData(_request=self._request, _leet=self._leet)
        self.score = AdminUpdateScoreData(_leet=self._leet)
        self.rank = AdminUpdateRankData(_leet=self._leet)
        self.statistics = AdminUpdateStatisticsData(_leet=self._leet)
        self.answer_count = AdminUpdateAnswerCountData(_leet=self._leet)


@dataclass(kw_only=True)
class AdminUpdateAnswerOfficialData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        self._model = ModelData()

    def update_problem_model_for_answer_official(self) -> tuple[bool | None, str]:
        problem_model = self._model.problem
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '정답을 업데이트했습니다.',
            False: '기존 정답과 일치합니다.',
        }
        list_create, list_update = [], []

        form = forms.UploadFileForm(self._request.POST, self._request.FILES)
        file = self._request.FILES.get('file')

        if form.is_valid():
            df = pd.read_excel(file, header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = problem_model.objects.get(leet=self._leet, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except problem_model.DoesNotExist:
                            problem = problem_model(leet=self._leet, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(problem_model, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]


@dataclass(kw_only=True)
class AdminUpdateScoreData:
    _leet: models.Leet

    def __post_init__(self):
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._sub_list = leet_context.sub_list
        self._qs_student = self._model.student.objects.filter(leet=self._leet).order_by('id')

    @with_update_message(UPDATE_MESSAGES['raw_score'])
    def update_raw_scores(self):
        return [self.update_score_model_for_raw_score()]

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        return [self.update_score_model_for_score()]

    @with_bulk_create_or_update()
    def update_score_model_for_raw_score(self):
        score_model = self._model.score
        answer_model = self._model.answer
        list_create, list_update = [], []

        for qs_s in self._qs_student:
            original_score_instance, _ = score_model.objects.get_or_create(student=qs_s)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self._sub_list):
                qs_answer = (
                    answer_model.objects.filter(student=qs_s, problem__subject=sub)
                    .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
                )
                if qs_answer:
                    correct_count = 0
                    for entry in qs_answer:
                        answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                        correct_count += 1 if entry.answer_student in answer_correct_list else 0
                    score_list.append(correct_count)
                    fields_not_match.append(getattr(original_score_instance, f'raw_subject_{idx}') != correct_count)

            score_raw_sum = sum(score_list[1:])
            fields_not_match.append(original_score_instance.raw_sum != score_raw_sum)

            if any(fields_not_match):
                for idx, score in enumerate(score_list):
                    setattr(original_score_instance, f'raw_subject_{idx}', score)
                original_score_instance.raw_sum = score_raw_sum
                list_update.append(original_score_instance)

        update_fields = ['raw_subject_0', 'raw_subject_1', 'raw_sum']
        return score_model, list_create, list_update, update_fields

    @with_bulk_create_or_update()
    def update_score_model_for_score(self):
        score_model = self._model.score
        list_create, list_update = [], []

        subject_fields = {
            0: ('raw_subject_0', 'subject_0', 45, 9),
            1: ('raw_subject_1', 'subject_1', 60, 9),
        }

        original = score_model.objects.filter(student__leet=self._leet)
        stats = original.aggregate(
            avg_0=Avg('raw_subject_0', filter=~Q(raw_subject_0=0)),
            stddev_0=StdDev('raw_subject_0', filter=~Q(raw_subject_0=0)),
            avg_1=Avg('raw_subject_1', filter=~Q(raw_subject_1=0)),
            stddev_1=StdDev('raw_subject_1', filter=~Q(raw_subject_1=0)),
        )

        for origin in original:
            fields_not_match = []
            score_list = []

            for idx, (raw_fld, fld, leet_avg, leet_stddev) in subject_fields.items():
                avg = stats[f'avg_{idx}']
                stddev = stats[f'stddev_{idx}']

                if avg is not None and stddev:
                    raw_score = getattr(origin, raw_fld)
                    score = round((raw_score - avg) / stddev * leet_stddev + leet_avg, 1)
                    score_list.append(score)

                    if getattr(origin, fld) != score:
                        fields_not_match.append(True)
                        setattr(origin, fld, score)

            score_sum = round(sum(score_list), 1)
            if any(fields_not_match):
                origin.sum = score_sum
                list_update.append(origin)

        update_fields = ['subject_0', 'subject_1', 'sum']
        return score_model, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminUpdateRankData:
    _leet: models.Leet

    def __post_init__(self):
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._subject_fields_sum = leet_context.subject_fields_sum
        self._qs_student = self._model.student.objects.filter(leet=self._leet).order_by('id')

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        return [
            self.update_rank_model('all', False),
            self.update_rank_model('aspiration_1', False),
            self.update_rank_model('aspiration_2', False),
            self.update_rank_model('all', True),
            self.update_rank_model('aspiration_1', True),
            self.update_rank_model('aspiration_2', True),
        ]

    @with_bulk_create_or_update()
    def update_rank_model(self, stat_type: str, is_filtered: bool):
        rank_model = self._model.rank_model_set.get(stat_type)
        qs_rank = rank_model.objects.filter(student__leet=self._leet)
        qs_rank_dict = {qs_r.student: qs_r for qs_r in qs_rank}

        prefix = ''
        qs_student = self._qs_student
        if is_filtered:
            prefix = 'filtered_'
            qs_student = self._qs_student.filter(is_filtered=is_filtered)

        list_create, list_update = [], []
        subject_fields_sum = [f'{prefix}{fld}' for fld in self._subject_fields_sum]

        score_np_data_dict = self.get_score_np_data_dict_for_rank(qs_student)
        for qs_s in qs_student:
            data = {}
            if stat_type == 'all':
                data = score_np_data_dict['all']
            if stat_type == 'aspiration_1' and qs_s.aspiration_1:
                data = score_np_data_dict[qs_s.aspiration_1]
            if stat_type == 'aspiration_2' and qs_s.aspiration_2:
                data = score_np_data_dict[qs_s.aspiration_2]

            rank_obj_exists = True
            rank_obj = qs_rank_dict.get(qs_s)
            if rank_obj is None:
                rank_obj_exists = False
                rank_obj = rank_model(student=qs_s)

            def set_rank_obj_field(target_list):
                ranks = {
                    f'{prefix}{fld}': rankdata(-data[fld], method='min') for fld in self._subject_fields_sum
                }  # 높은 점수가 1등
                participants = len(data['sum'])

                need_to_append = False
                for fld in self._subject_fields_sum:
                    score = getattr(qs_s.score, fld)
                    idx = np.where(data[fld] == score)[0][0]
                    new_rank = int(ranks[f'{prefix}{fld}'][idx])
                    if hasattr(rank_obj, fld):
                        if getattr(rank_obj, f'{prefix}{fld}') != new_rank or getattr(rank_obj, f'{prefix}participants') != participants:
                            need_to_append = True
                            setattr(rank_obj, f'{prefix}{fld}', new_rank)
                            setattr(rank_obj, f'{prefix}participants', participants)
                if need_to_append:
                    target_list.append(rank_obj)

            def set_rank_obj_field_to_null(target_list):
                need_to_append = False
                for fld in self._subject_fields_sum:
                    if hasattr(rank_obj, fld):
                        if getattr(rank_obj, fld) is not None or rank_obj.participants is not None:
                            need_to_append = True
                            setattr(rank_obj, fld, None)
                            rank_obj.participants = None
                if need_to_append:
                    target_list.append(rank_obj)

            if rank_obj_exists:
                if data:
                    set_rank_obj_field(list_update)
                else:
                    set_rank_obj_field_to_null(list_update)
            else:
                if data:
                    set_rank_obj_field(list_create)
                else:
                    set_rank_obj_field_to_null(list_create)

        update_fields = subject_fields_sum + ['participants', 'filtered_participants']
        return rank_model, list_create, list_update, update_fields

    def get_score_np_data_dict_for_rank(self, qs_student) -> dict[str: np.array]:
        """
        score_dict = {
            'all': {
                'subject_0': [...],
                'subject_1': [...],
                'sum': [...],
            },
            '서울대학교': {
                'subject_0': [...],
                'subject_1': [...],
                'sum': [...],
            },
        }
        """
        score_dict = defaultdict(dict)

        def update_score_dict(instance, aspiration):
            for field in self._subject_fields_sum:
                if field not in score_dict[aspiration]:
                    score_dict[aspiration][field] = []
                score_dict[aspiration][field].append(getattr(instance, field))

        for qs_s in qs_student:
            update_score_dict(qs_s.score, 'all')
            if qs_s.aspiration_1:
                update_score_dict(qs_s.score, qs_s.aspiration_1)
            if qs_s.aspiration_2:
                update_score_dict(qs_s.score, qs_s.aspiration_2)

        score_np_data_dict = defaultdict(dict)
        for key, value in score_dict.items():
            for fld, score_list in value.items():
                score_np_data_dict[key][fld] = np.array(score_list)

        return score_np_data_dict


@dataclass(kw_only=True)
class AdminUpdateStatisticsData:
    _leet: models.Leet

    def __post_init__(self):
        leet_context = LeetContext(_leet=self._leet)
        self._model = ModelData()
        self._all_subject_fields_sum = leet_context.all_subject_fields_sum
        self._qs_student = self._model.student.objects.filter(leet=self._leet).order_by('id')

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        total_data, filtered_data = self.get_statistics_data()
        return [
            self.update_statistics_model(total_data, False),
            self.update_statistics_model(filtered_data, True),
        ]

    def get_statistics_data(self) -> tuple[dict, dict]:
        total_data, filtered_data, total_scores, filtered_scores = self.get_default_data_and_scores()
        total_scores_np, filtered_scores_np = self.get_scores_np(total_scores, filtered_scores)

        for aspiration, score_dict in total_scores_np.items():
            for fld, scores in score_dict.items():
                scores_stat = get_stat_from_scores(scores)
                total_data[aspiration][fld].update(scores_stat)

        for aspiration, score_dict in filtered_scores_np.items():
            for fld, scores in score_dict.items():
                scores_stat = get_stat_from_scores(scores)
                filtered_data[aspiration][fld].update(scores_stat)

        return total_data, filtered_data

    def get_default_data_and_scores(self):
        aspirations = models.choices.get_aspirations()
        participants_dict = self.get_participants_dict()

        total_data, filtered_data = defaultdict(dict), defaultdict(dict)
        total_scores, filtered_scores = defaultdict(dict), defaultdict(dict)

        def get_empty_dict(aspiration):
            return {
                fld: {
                    'participants': participants_dict['sum'].get(aspiration, 0),
                    'participants_1': participants_dict['1'].get(aspiration, 0),
                    'participants_2': participants_dict['2'].get(aspiration, 0),
                    'max': 0, 't10': 0, 't25': 0, "t50": 0, 'avg': 0
                } for fld in self._all_subject_fields_sum
            }

        for aspir in aspirations:
            total_data[aspir] = get_empty_dict(aspir)
            filtered_data[aspir] = get_empty_dict(aspir)
            total_scores[aspir] = {fld: [] for fld in self._all_subject_fields_sum}
            filtered_scores[aspir] = {fld: [] for fld in self._all_subject_fields_sum}

        return total_data, filtered_data, total_scores, filtered_scores

    def get_participants_dict(self):
        def get_participants_distribution(aspiration_num: int):
            participants_distribution = (
                self._qs_student.exclude(**{f'aspiration_{aspiration_num}__isnull': True})
                .exclude(**{f'aspiration_{aspiration_num}': ''})
                .values(f'aspiration_{aspiration_num}').annotate(count=Count('id'))
            )
            data_dict = {row[f'aspiration_{aspiration_num}']: row['count'] for row in participants_distribution}
            data_dict['전체'] = sum(data_dict.values())
            return data_dict

        participants_dict = {
            '1': get_participants_distribution(1),
            '2': get_participants_distribution(2),
            'sum': {}
        }
        for key in set(participants_dict['1']) | set(participants_dict['2']):
            participants_dict['sum'][key] = participants_dict['1'].get(key, 0) + participants_dict['2'].get(key, 0)
        participants_dict['sum']['전체'] = self._qs_student.count()
        return participants_dict

    def get_scores_np(self, total_scores, filtered_scores):
        def append_score(score_dict: dict, student: models.PredictStudent, field: str, score):
            score_dict['전체'][field].append(score)
            if student.aspiration_1:
                score_dict[student.aspiration_1][field].append(score)
            if student.aspiration_2:
                score_dict[student.aspiration_2][field].append(score)

        for qs_s in self._qs_student:
            for fld in self._all_subject_fields_sum:
                sco = getattr(qs_s.score, fld)
                if sco is not None:
                    append_score(total_scores, qs_s, fld, sco)
                    if qs_s.is_filtered:
                        append_score(filtered_scores, qs_s, fld, sco)

        def get_np_dict(scores, aspiration):
            return {field: np.array(scores) for field, scores in scores[aspiration].items()}

        total_scores_np, filtered_scores_np = defaultdict(dict), defaultdict(dict)
        for aspir in models.choices.get_aspirations():
            total_scores_np[aspir] = get_np_dict(total_scores, aspir)
            filtered_scores_np[aspir] = get_np_dict(filtered_scores, aspir)

        return total_scores_np, filtered_scores_np

    @with_bulk_create_or_update()
    def update_statistics_model(self, data_statistics: dict, is_filtered: bool):
        prefix = 'filtered_' if is_filtered else ''
        list_create, list_update = [], []
        model = self._model.statistics

        for aspiration, data_stat in data_statistics.items():
            stat_dict = defaultdict()
            for fld in self._all_subject_fields_sum:
                stat_dict[f'{prefix}{fld}'] = {
                    'participants': data_stat[fld]['participants'],
                    'participants_1': data_stat[fld]['participants_1'],
                    'participants_2': data_stat[fld]['participants_2'],
                    'max': data_stat[fld]['max'],
                    't10': data_stat[fld]['t10'],
                    't25': data_stat[fld]['t25'],
                    't50': data_stat[fld]['t50'],
                    'avg': data_stat[fld]['avg'],
                }

            try:
                instance = model.objects.get(leet=self._leet, aspiration=aspiration)
                fields_not_match = any(getattr(instance, fld) != val for fld, val in stat_dict.items())
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except model.DoesNotExist:
                list_create.append(model(leet=self._leet, **stat_dict))
        update_fields = [
            f'{prefix}raw_subject_0', f'{prefix}raw_subject_1', f'{prefix}raw_sum',
            f'{prefix}subject_0', f'{prefix}subject_1', f'{prefix}sum',
        ]
        return model, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminUpdateAnswerCountData:
    _leet: models.Leet

    def __post_init__(self):
        self._model = ModelData()

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        return [
            self.update_answer_count_model(self._model.ac_all, False),
            self.update_answer_count_model(self._model.ac_top, False),
            self.update_answer_count_model(self._model.ac_mid, False),
            self.update_answer_count_model(self._model.ac_low, False),

            self.update_answer_count_model(self._model.ac_all, True),
            self.update_answer_count_model(self._model.ac_top, True),
            self.update_answer_count_model(self._model.ac_mid, True),
            self.update_answer_count_model(self._model.ac_low, True),
        ]

    @with_bulk_create_or_update()
    def update_answer_count_model(self, answer_count_model, is_filtered: bool):
        prefix = 'filtered_' if is_filtered else ''

        list_update = []
        list_create = []

        lookup_field = f'student__rank__{prefix}sum'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F(f'student__rank__{prefix}participants')

        lookup_exp = {}
        if is_filtered:
            lookup_exp['student__is_filtered'] = is_filtered
        if answer_count_model == self._model.ac_top:
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif answer_count_model == self._model.ac_mid:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif answer_count_model == self._model.ac_low:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        qs_answer = (
            self._model.answer.objects.filter(problem__leet=self._leet, **lookup_exp)
            .select_related('student', 'student__rank')
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
class AdminExportExcelData:
    _leet: models.Leet

    def __post_init__(self):
        leet_context = LeetContext(_leet=self._leet)

        self._subject_vars = leet_context.subject_vars
        self._subject_vars_avg = leet_context.subject_vars_sum
        self._sub_list = [sub for sub in self._subject_vars]

    def get_statistics_response(self) -> HttpResponse:
        qs_statistics = models.PredictStatistics.objects.filter(leet=self._leet).order_by('id')
        df = pd.DataFrame.from_records(qs_statistics.values())

        filename = f'{self._leet.full_reference}_성적통계.xlsx'
        drop_columns = ['id', 'leet_id']
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
        qs_student = models.PredictStudent.objects.filter(leet=self._leet).values(
            'id', 'created_at', 'name', 'prime_id').order_by('id')
        df = pd.DataFrame.from_records(qs_student)
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        filename = f'{self._leet.full_reference}_참여자명단.xlsx'
        column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        total_student_list = models.PredictStudent.objects.filtered_student_by_leet(self._leet)
        filtered_student_list = total_student_list.filter(is_filtered=True)
        filename = f'{self._leet.full_reference}_성적일람표.xlsx'

        df1 = self.get_catalog_df_for_excel(total_student_list)
        df2 = self.get_catalog_df_for_excel(filtered_student_list, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    def get_catalog_df_for_excel(self, student_list: QuerySet, is_filtered=False) -> pd.DataFrame:
        column_list = [
            'id', 'leet_id', 'category_id', 'user_id',
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
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_leet_and_subject(self._leet)
        filename = f'{self._leet.full_reference}_문항분석표.xlsx'

        df1 = self.get_answer_df_for_excel(qs_answer_count)
        df2 = self.get_answer_df_for_excel(qs_answer_count, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    @staticmethod
    def get_answer_df_for_excel(
            qs_answer_count: QuerySet[models.PredictAnswerCount], is_filtered=False) -> pd.DataFrame:
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
