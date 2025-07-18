__all__ = [
    'ModelData', 'RequestContext', 'LeetContext', 'SubjectVariants',
    'get_prev_next_obj', 'get_stat_from_scores',
]

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from django.utils import timezone

from a_leet import filters, models
from common.utils import HtmxHttpRequest


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.leet = models.Leet
        self.problem = models.Problem

        self.predict_leet = models.PredictLeet
        self.statistics = models.PredictStatistics
        self.student = models.PredictStudent
        self.answer = models.PredictAnswer
        self.score = models.PredictScore

        self.rank = models.PredictRank
        self.rank_1 = models.PredictRankAspiration1
        self.rank_2 = models.PredictRankAspiration2
        self.rank_model_set = {'all': self.rank, 'aspiration_1': self.rank_1, 'aspiration_2': self.rank_2}

        self.ac_all = models.PredictAnswerCount
        self.ac_top = models.PredictAnswerCountTopRank
        self.ac_mid = models.PredictAnswerCountMidRank
        self.ac_low = models.PredictAnswerCountLowRank
        self.ac_model_set = {'all': self.ac_all, 'top': self.ac_top, 'mid': self.ac_mid, 'low': self.ac_low}

        self.aspirations = models.choices.get_aspirations()


@dataclass(kw_only=True)
class RequestContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        self.view_type = self._request.headers.get('View-Type', '')
        self.exam_year = self._request.GET.get('year', '')
        self.exam_exam = self._request.GET.get('exam', '')
        self.exam_subject = self._request.GET.get('subject', '')
        self.page_number = self._request.GET.get('page', 1)
        self.keyword = self._request.POST.get('keyword', '') or self._request.GET.get('keyword', '')
        self.student_name = self._request.GET.get('student_name', '')

    def get_filterset(self):
        problem_filter = filters.ProblemFilter if self._request.user.is_authenticated else filters.AnonymousProblemFilter
        return problem_filter(data=self._request.GET, request=self._request)

    def get_sub_title(self, end_string='기출문제') -> str:
        year = self.exam_year
        exam = self.exam_exam
        subject = self.exam_subject
        title_parts = []
        if year:
            title_parts.append(f'{year}년')
            if isinstance(year, str):
                year = int(year)

        title_parts.append(models.choices.exam_choice().get(exam, ''))
        title_parts.append(models.choices.subject_choice().get(subject, ''))

        if not year and not exam and not subject:
            title_parts.append('전체')
        else:
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} {end_string}'
        return sub_title


@dataclass(kw_only=True)
class LeetContext:
    _leet: models.Leet

    def __post_init__(self):
        self.subject_vars_sum_first = self.get_subject_vars_sum_first()
        self.subject_vars_sum = self.get_subject_vars_sum()
        self.subject_vars = self.get_subject_vars()
        self.subject_fields_sum_first = [fld for (_, fld, _, _) in self.subject_vars_sum_first.values()]
        self.subject_fields_sum = [fld for (_, fld, _, _) in self.subject_vars_sum.values()]
        self.subject_fields = [fld for (_, fld, _, _) in self.subject_vars.values()]
        self.all_subject_fields_sum = [f'raw_{fld}' for fld in self.subject_fields_sum] + self.subject_fields_sum
        self.sub_list = [sub for sub in self.subject_vars]

        has_predict = self.get_has_predict()
        self.predict_leet = self._leet.predict_leet if has_predict else None
        self.time_schedule = self.get_time_schedule() if has_predict else {}

    @staticmethod
    def get_subject_vars_sum_first() -> dict[str, tuple[str, str, int, int]]:
        return {
            '총점': ('총점', 'sum', 2, 70),
            '언어': ('언어이해', 'subject_0', 0, 30),
            '추리': ('추리논증', 'subject_1', 1, 40),
        }

    @staticmethod
    def get_subject_vars_sum() -> dict[str, tuple[str, str, int, int]]:
        return {
            '언어': ('언어이해', 'subject_0', 0, 30),
            '추리': ('추리논증', 'subject_1', 1, 40),
            '총점': ('총점', 'sum', 2, 70),
        }

    def get_subject_vars(self) -> dict[str, tuple[str, str, int, int]]:
        subject_vars = self.get_subject_vars_sum()
        subject_vars.pop('총점')
        return subject_vars

    def is_not_for_predict(self):
        return any([
            not self._leet,
            not hasattr(self._leet, 'predict_leet'),
            not self._leet.predict_leet.is_active if hasattr(self._leet, 'predict_leet') else True,
        ])

    def before_exam_start(self):
        return timezone.now() < self._leet.predict_leet.exam_started_at

    def get_has_predict(self):
        if hasattr(self._leet, 'predict_leet'):
            return all([self._leet, self._leet.predict_leet.is_active])

    def get_time_schedule(self) -> dict:
        start_time = self.predict_leet.exam_started_at
        subject_0_end_time = start_time + timedelta(minutes=70)  # 1교시 시험 종료 시각
        subject_1_start_time = subject_0_end_time + timedelta(minutes=35)  # 2교시 시험 시작 시각
        subject_2_end_time = subject_1_start_time + timedelta(minutes=125)  # 2교시 시험 종료 시각
        finish_time = self.predict_leet.exam_finished_at  # 3교시 시험 종료 시각
        return {
            '언어': (start_time, subject_0_end_time),
            '추리': (subject_1_start_time, subject_2_end_time),
            '총점': (start_time, finish_time),
        }


@dataclass(kw_only=True)
class SubjectVariants:
    def __post_init__(self):
        self.subject_vars, self.subject_vars_sum, self.subject_vars_sum_first, self.subject_vars_dict =\
            self.get_vars_all()

        self.sub_list, self.subject_list, self.subject_fields = self.get_all_list(self.subject_vars)
        self.sub_list_sum, self.subject_list_sum, self.subject_fields_sum = self.get_all_list(self.subject_vars_sum)
        self.sub_list_sum_first, self.subject_list_sum_first, self.subject_fields_sum_first = self.get_all_list(
            self.subject_vars_sum_first)

    def get_vars_all(self):
        sum_vars = {'총점': ('총점', 'sum', 2, 70)}
        subject_vars = {
            '언어': ('언어이해', 'subject_0', 0, 30),
            '추리': ('추리논증', 'subject_1', 1, 40),
        }
        subject_vars_sum = dict(subject_vars, **sum_vars)
        subject_vars_sum_first = dict(sum_vars, **subject_vars)
        subject_vars_dict = {
            'base': subject_vars, 'sum_last': subject_vars_sum, 'sum_first': subject_vars_sum_first
        }
        return subject_vars, subject_vars_sum, subject_vars_sum_first, subject_vars_dict

    @staticmethod
    def get_all_list(_vars: dict):
        sub = list(_vars.keys())
        tuple_lists = list(zip(*_vars.values()))
        subject = tuple_lists[0]
        field = tuple_lists[1]
        return sub, subject, field

    def get_subject_variable(self, subject_field) -> tuple[str, str, int, int]:
        for sub, (subject, fld, field_idx, problem_count) in self.subject_vars.items():
            if subject_field == fld:
                return sub, subject, field_idx, problem_count


def get_prev_next_obj(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_obj = next_obj = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_obj = custom_data[q - 1]
        if q != last_id:
            next_obj = custom_data[q + 1]
        return prev_obj, next_obj
    except ValueError:
        return None, None


def get_stat_from_scores(scores: np.array):
    _max = _t10 = _t25 = _t50 = _avg = 0
    if scores.any():
        _max = round(float(np.max(scores)), 1)
        _t10 = round(float(np.percentile(scores, 90)), 1)
        _t25 = round(float(np.percentile(scores, 75)), 1)
        _t50 = round(float(np.percentile(scores, 50)), 1)
        _avg = round(float(np.mean(scores)), 1)
    return {'max': _max, 't10': _t10, 't25': _t25, 't50': _t50, 'avg': _avg}
