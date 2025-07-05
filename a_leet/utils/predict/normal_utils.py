__all__ = [
    'NormalListData', 'NormalDetailData',
    'NormalRegisterData', 'NormalAnswerInputData', 'NormalAnswerConfirmData',
]

import json
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F, Window
from django.db.models.functions import Rank
from django.shortcuts import render, get_object_or_404, redirect
from django_htmx.http import reswap

from a_leet import models, forms
from a_leet.utils.common_utils import RequestData, ModelData, LeetData, get_stat_from_scores
from common.utils import HtmxHttpRequest, update_context_data
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
class InputAnswerData:
    _request: HtmxHttpRequest
    _leet: models.Leet

    def __post_init__(self):
        self._leet_data = LeetData(_leet=self._leet)
        self._subject_vars = self._leet_data.subject_vars
        self.answer_data_set = self.get_input_answer_data_set()

    def get_input_answer_data_set(self) -> dict:
        empty_answer_data = {
            fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in self._subject_vars.items()
        }
        answer_data_set_cookie = self._request.COOKIES.get('answer_data_set', '{}')
        answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
        return answer_data_set


@dataclass(kw_only=True)
class ChartData:
    _statistics_context: dict
    _student: models.PredictStudent | None

    def __post_init__(self):
        leet_data = LeetData(_leet=self._student.leet)

        self._subject_vars = leet_data.subject_vars
        self._subject_fields_sum = leet_data.subject_fields_sum
        self._student_score_list = self.get_student_score_list()

    def get_student_score_list(self):
        if self._student:
            return [getattr(self._student.score, fld) or 0 for fld in self._subject_fields_sum]

    def get_dict_stat_chart(self) -> dict:
        chart_score = {
            'avg': [], 't50': [], 't25': [], 't10': [], 'max': [],
        }
        if self._student:
            chart_score['my_score'] = self._student_score_list

        for stat in self._statistics_context['all']['page_obj'].values():
            chart_score['avg'].append(stat['avg'])
            chart_score['t50'].append(stat['t50'])
            chart_score['t25'].append(stat['t25'])
            chart_score['t10'].append(stat['t10'])
            chart_score['max'].append(stat['max'])

        score_list = [score for score in self._student_score_list if score is not None]
        chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0
        return chart_score

    def get_dict_stat_frequency(self) -> dict:
        score_frequency_list = models.PredictStudent.objects.average_scores_over(self._student.leet, 50)
        scores = [round(score, 1) for score in score_frequency_list]
        sorted_freq, target_bin = self.frequency_table_by_bin(scores)

        score_label, score_data, score_color = [], [], []
        for key, val in sorted_freq.items():
            score_label.append(key)
            score_data.append(val)
            color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
            score_color.append(color)

        return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}

    def frequency_table_by_bin(self, scores: list, bin_size: int = 5) -> tuple[dict, str | None]:
        freq = defaultdict(int)
        for score in scores:
            bin_start = int((score // bin_size) * bin_size)
            bin_end = bin_start + bin_size
            bin_label = f'{bin_start}~{bin_end}'
            freq[bin_label] += 1

        # bin_start 기준으로 정렬
        sorted_freq = dict(sorted(freq.items(), key=lambda x: int(x[0].split('~')[0])))

        # 특정 점수의 구간 구하기
        target_bin = None
        if self._student and self._student.score.sum:  # noqa
            bin_start = int((self._student.score.sum // bin_size) * bin_size)  # noqa
            bin_end = bin_start + bin_size
            target_bin = f'{bin_start}~{bin_end}'

        return sorted_freq, target_bin


@dataclass(kw_only=True)
class NormalListData:
    _request: HtmxHttpRequest

    def __post_init__(self):
        self.qs_leet = self.get_qs_leet()

    def get_qs_leet(self):
        qs_leet = models.Leet.objects.predict_leet_active()
        student_dict = {}
        if self._request.user.is_authenticated:
            qs_student = models.PredictStudent.objects.registered_leet_student(self._request.user, qs_leet)
            student_dict = {qs_s.leet: qs_s for qs_s in qs_student}
        for qs_p in qs_leet:
            qs_p.student = student_dict.get(qs_p, None)
        return qs_leet


@dataclass(kw_only=True)
class NormalDetailData:
    _request: HtmxHttpRequest
    _student: models.PredictStudent

    def __post_init__(self):
        request_data = RequestData(_request=self._request)
        leet_data = LeetData(_leet=self._student.leet)
        self._model = ModelData()
        self._subject_vars = leet_data.subject_vars

        self.view_type = request_data.view_type
        self.is_analyzing = True if self._student.score.sum is None else False

        self.statistics = NormalDetailStatisticsData(_request=self._request, _student=self._student)
        self.is_confirmed_data = self.statistics.is_confirmed_data
        self.total_statistics_context = self.statistics.total_statistics_context
        self.filtered_statistics_context = self.statistics.filtered_statistics_context

        self.chart_data = ChartData(_statistics_context=self.total_statistics_context, _student=self._student)

    @staticmethod
    def get_loop_list(problem_count: int):
        loop_list = []
        quotient = problem_count // 10
        counter_list = [10] * quotient
        remainder = problem_count % 10
        if remainder:
            counter_list.append(remainder)
        loop_min = 0
        for idx, counter in enumerate(counter_list):
            loop_list.append({'counter': counter, 'min': loop_min})
            loop_min += 10
        return loop_list

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._subject_vars
        context = {
            sub: {
                'id': str(idx), 'title': subject, 'subject': subject, 'field': fld,
                'url_answer_input': self._student.leet.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count) in subject_vars.items()
        }
        qs_student_answer = self.statistics.qs_student_answer

        for qs_sa in qs_student_answer:
            sub = qs_sa.problem.subject
            ans_official = qs_sa.problem.answer
            ans_student = qs_sa.answer
            ans_predict = qs_sa.problem.predict_answer_count.answer_predict

            qs_sa.no = qs_sa.problem.number
            qs_sa.ans_official = ans_official
            qs_sa.ans_official_circle = qs_sa.problem.get_answer_display

            qs_sa.ans_student = ans_student
            qs_sa.field = subject_vars[sub][1]

            qs_sa.ans_predict = ans_predict
            qs_sa.rate_accuracy = qs_sa.problem.predict_answer_count.get_answer_predict_rate()

            qs_sa.rate_correct = qs_sa.problem.predict_answer_count.get_answer_rate(ans_official)
            qs_sa.rate_correct_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            if qs_sa.rate_correct_top is not None and qs_sa.rate_correct_low is not None:
                qs_sa.rate_gap = qs_sa.rate_correct_top - qs_sa.rate_correct_low
            else:
                qs_sa.rate_gap = 0

            qs_sa.rate_selection = qs_sa.problem.predict_answer_count.get_answer_rate(ans_student)
            qs_sa.rate_selection_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_student)

            context[sub]['page_obj'].append(qs_sa)
        return context


@dataclass(kw_only=True)
class NormalDetailStatisticsData:
    _request: HtmxHttpRequest
    _student: models.PredictStudent

    def __post_init__(self):
        self._model = ModelData()
        self._leet_data = LeetData(_leet=self._student.leet)
        self._input_answer = InputAnswerData(_request=self._request, _leet=self._student.leet)

        self._predict_leet = self._leet_data.predict_leet
        self._time_schedule = self._leet_data.time_schedule
        self._subject_vars = self._leet_data.subject_vars
        self._subject_vars_sum = self._leet_data.subject_vars_sum
        self._subject_fields_sum = self._leet_data.subject_fields_sum

        self._answer_data_set = self._input_answer.answer_data_set
        self._participants_df = self.get_participants_df()
        self._score_df = self.get_score_df()

        self.qs_student_answer = self._model.answer.objects.filtered_by_leet_student(self._student)
        self.is_confirmed_data = self.get_is_confirmed_data()
        self.is_analyzing = True if self._student.score.sum is None else False
        self.total_statistics_context = self.get_normal_statistics_context(False)
        self.filtered_statistics_context = self.get_normal_statistics_context(True)

    def get_participants_df(self):
        qs_answer = (
            self._model.answer.objects.filter(problem__leet=self._student.leet)
            .order_by('student')
            .values(
                sub=F('problem__subject'), is_filtered=F('student__is_filtered'),
                aspiration_1=F('student__aspiration_1'), aspiration_2=F('student__aspiration_2'),
            ).distinct()
        )
        return pd.DataFrame(qs_answer)

    def get_score_df(self):
        qs_score = (
            self._model.score.objects.filter(student__leet=self._student.leet)
            .order_by('student')
            .values(
                'subject_0', 'subject_1', 'sum',
                is_filtered=F('student__is_filtered'),
                aspiration_1=F('student__aspiration_1'),
                aspiration_2=F('student__aspiration_2'),
            )
        )
        return pd.DataFrame(qs_score)

    def get_is_confirmed_data(self) -> dict[str, bool]:
        is_confirmed_data = {sub: False for sub in self._subject_vars}
        confirmed_sub_list = self.qs_student_answer.values_list('subject', flat=True).distinct()
        for sub in confirmed_sub_list:
            is_confirmed_data[sub] = True
        is_confirmed_data['총점'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '총점'
        return is_confirmed_data

    def get_normal_statistics_context(self, is_filtered: bool) -> dict:
        if is_filtered and not self._student.is_filtered:
            return {}

        suffix = 'Filtered' if is_filtered else 'Total'
        statistics_all = self.get_statistics_data('all', is_filtered)
        statistics_1 = self.get_statistics_data('aspiration_1', is_filtered)
        statistics_2 = self.get_statistics_data('aspiration_2', is_filtered)
        self.update_score_predict(statistics_all)

        return {
            'all': {
                'id': '0', 'title': '전체', 'prefix': f'all{suffix}Score', 'page_obj': statistics_all,
            },
            'aspiration_1': {
                'id': '1', 'title': '1지망', 'prefix': f'aspiration1{suffix}Score', 'page_obj': statistics_1,
            },
            'aspiration_2': {
                'id': '2', 'title': '2지망', 'prefix': f'aspiration1{suffix}Score', 'page_obj': statistics_2,
            },
        }

    def get_statistics_data(self, stat_type: str, is_filtered: bool) -> dict:
        answer_count_dict = self.get_answer_count_dict()

        stat_data = {}
        for sub, (subject, fld, _, problem_count) in self._subject_vars_sum.items():
            url_answer_input = self._student.leet.get_predict_answer_input_url(fld) if sub != '총점' else ''
            answer_count = answer_count_dict[sub] if sub != '총점' else sum(answer_count_dict.values())

            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'start_time': self._time_schedule[sub][0],
                'end_time': self._time_schedule[sub][1],

                'is_confirmed': self.is_confirmed_data[sub],
                'url_answer_input': url_answer_input,

                'problem_count': problem_count,
                'answer_count': answer_count,

                'participants': 0,
                'raw_score_predict': 0, 'raw_score': 0, 'score': 0, 'rank': 0,
                'max': 0, 't10': 0, 't25': 0, 't50': 0, 'avg': 0,
            }

            participants = self.get_participants(stat_type, is_filtered, sub)
            if participants:
                score_np = self.get_score_np(stat_type, is_filtered, fld)
                if self._predict_leet.is_answer_predict_opened:
                    pass
                if self._predict_leet.is_answer_official_opened:
                    raw_score = getattr(self._student.score, f'raw_{fld}')
                    score = getattr(self._student.score, fld)
                    if score_np.size > 0 and score in score_np:
                        scores_stat = get_stat_from_scores(score_np)
                        sorted_scores = np.sort(score_np)[::-1]
                        flat_scores = sorted_scores.flatten()
                        rank = int(np.where(flat_scores == score)[0][0] + 1)
                        stat_data[sub].update(scores_stat | {
                            'participants': participants,
                            'raw_score': raw_score,
                            'score': score,
                            'rank': rank,
                        })
        return stat_data

    def get_answer_count_dict(self) -> dict[str, int]:
        answer_count_dict = {}
        for sub, (_, fld, _, _) in self._subject_vars.items():
            answer_list = self._answer_data_set.get(fld)
            saved_answers = []
            if answer_list:
                saved_answers = [ans for ans in answer_list if ans]
            answer_count_dict[sub] = max(self._student.answer_count.get(sub, 0), len(saved_answers))
        return answer_count_dict

    def get_participants(self, stat_type: str, is_filtered: bool, sub: str):
        df = self._participants_df
        if not df.empty:
            if stat_type != 'all':
                aspiration = getattr(self._student, stat_type)
                if aspiration:
                    df = df[df[stat_type] == aspiration]
            if is_filtered:
                df = df[df['is_filtered'] is True]
            if sub == '총점':
                return min([df[df['sub'] == _sub].shape[0] for _sub in self._subject_vars])
            return df[df['sub'] == sub].shape[0]

    def get_score_np(self, stat_type: str, is_filtered: bool, fld: str):
        df = self._score_df
        if stat_type != 'all':
            aspiration = getattr(self._student, stat_type)
            if aspiration:
                df = df[df[stat_type] == aspiration]
        if is_filtered:
            df = df[df['is_filtered'] is True]
        return df[[fld]].to_numpy()

    def update_score_predict(self, statistics_all: dict) -> None:
        predict_correct_count_list = self.qs_student_answer.filter(predict_result=True).values(
            'subject').annotate(correct_counts=Count('predict_result'))
        leet_sum = 0
        for entry in predict_correct_count_list:
            sub = entry['subject']
            score = entry['correct_counts']
            leet_sum += score
            statistics_all[sub]['raw_score_predict'] = score
        statistics_all['총점']['raw_score_predict'] = leet_sum


@dataclass(kw_only=True)
class NormalDetailAnswerData:
    _request: HtmxHttpRequest
    _student: models.PredictStudent

    def __post_init__(self):
        leet_data = LeetData(_leet=self._student.leet)
        self._model = ModelData()
        self._subject_vars = leet_data.subject_vars

        self.statistics = NormalDetailStatisticsData(_request=self._request, _student=self._student)
        self.is_confirmed_data = self.statistics.is_confirmed_data

    @staticmethod
    def get_loop_list(problem_count: int):
        loop_list = []
        quotient = problem_count // 10
        counter_list = [10] * quotient
        remainder = problem_count % 10
        if remainder:
            counter_list.append(remainder)
        loop_min = 0
        for idx, counter in enumerate(counter_list):
            loop_list.append({'counter': counter, 'min': loop_min})
            loop_min += 10
        return loop_list

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._subject_vars
        context = {
            sub: {
                'id': str(idx), 'title': sub, 'subject': subject, 'field': fld,
                'url_answer_input': self._student.leet.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count) in subject_vars.items()
        }
        qs_student_answer = self.statistics.qs_student_answer

        for qs_sa in qs_student_answer:
            sub = qs_sa.problem.subject
            ans_official = qs_sa.problem.answer
            ans_student = qs_sa.answer
            ans_predict = qs_sa.problem.predict_answer_count.answer_predict

            qs_sa.no = qs_sa.problem.number
            qs_sa.ans_official = ans_official
            qs_sa.ans_official_circle = qs_sa.problem.get_answer_display

            qs_sa.ans_student = ans_student
            qs_sa.field = subject_vars[sub][1]

            qs_sa.ans_predict = ans_predict
            qs_sa.rate_accuracy = qs_sa.problem.predict_answer_count.get_answer_predict_rate()

            qs_sa.rate_correct = qs_sa.problem.predict_answer_count.get_answer_rate(ans_official)
            qs_sa.rate_correct_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            if qs_sa.rate_correct_top is not None and qs_sa.rate_correct_low is not None:
                qs_sa.rate_gap = qs_sa.rate_correct_top - qs_sa.rate_correct_low
            else:
                qs_sa.rate_gap = 0

            qs_sa.rate_selection = qs_sa.problem.predict_answer_count.get_answer_rate(ans_student)
            qs_sa.rate_selection_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_student)

            context[sub]['page_obj'].append(qs_sa)
        return context


@dataclass(kw_only=True)
class NormalRegisterData:
    _request: HtmxHttpRequest
    _leet: models.Leet
    _form: forms.PredictStudentForm

    def __post_init__(self):
        self.model_data = ModelData()

    def process_register(self, context):
        form = self._form
        if models.PredictStudent.objects.filter(leet=self._leet, user=self._request.user).exists():
            form.add_error(None, '이미 수험정보를 등록하셨습니다.')
            form.add_error(None, '만약 수험정보를 등록하신 적이 없다면 관리자에게 문의해주세요.')
            context = update_context_data(context, form=form)
            return render(self._request, 'a_leet/predict_register.html', context)

        serial = form.cleaned_data['serial']
        if models.PredictStudent.objects.filter(serial=serial).exists():
            form.add_error('serial', '이미 등록된 수험번호입니다.')
            form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')
            context = update_context_data(context, form=form)
            return render(self._request, 'a_leet/predict_register.html', context)

        additional_fields = {}
        aspiration_1 = form.cleaned_data.get('aspiration_1', None)
        aspiration_2 = form.cleaned_data.get('aspiration_2', None)
        if aspiration_2:
            if not aspiration_1:
                form.add_error('aspiration_1', '1지망을 선택해주세요.')
            if aspiration_2 == aspiration_1:
                form.add_error('aspiration_2', '1지망과 2지망이 동일합니다.')
                form.add_error('aspiration_2', '1지망 또는 2지망을 변경해주세요.')
            additional_fields['aspiration_2'] = aspiration_2
            if aspiration_1:
                additional_fields['aspiration_1'] = aspiration_1

        def process_cleaned_data(field_1: str, field_2: str, error_message: str):
            value_1 = form.cleaned_data.get(field_1, None)
            value_2 = form.cleaned_data.get(field_2, None)
            if value_1 and not value_2:
                additional_fields[field_1] = value_1
                if value_2:
                    additional_fields[field_2] = value_2
                else:
                    form.add_error(field_2, error_message)

        process_cleaned_data('major', 'school', '출신대학을 선택해주세요.')
        process_cleaned_data('gpa', 'gpa_type', '학점(GPA) 종류를 선택해주세요.')
        process_cleaned_data('english', 'english_type', '공인 영어성적 종류를 선택해주세요.')

        if form.errors:
            context = update_context_data(context, form=form)
            return render(self._request, 'a_leet/predict_register.html', context)

        student, is_created = models.PredictStudent.objects.get_or_create(
            leet=self._leet, user=self._request.user, serial=serial,
            name=form.cleaned_data['name'],
            password=form.cleaned_data['password'],
            **additional_fields,
        )
        if is_created:
            models.PredictScore.objects.create(student=student)
            models.PredictRank.objects.create(student=student)
            models.PredictRankAspiration1.objects.create(student=student)
            models.PredictRankAspiration2.objects.create(student=student)
        return redirect(self._leet.get_predict_detail_url())


@dataclass(kw_only=True)
class NormalStudentData:
    _request: HtmxHttpRequest
    _leet: models.Leet
    _subject_field: str

    def __post_init__(self):
        self._model = ModelData()
        self._leet_data = LeetData(_leet=self._leet)
        self._subject_vars = self._leet_data.subject_vars

        self.sub, self.subject, self.field_idx, self.problem_count = (
            self.get_subject_variable(self._subject_field))
        self.student = self._model.student.objects.leet_student_with_answer_count(self._request.user, self._leet)

        self._input_answer = InputAnswerData(_request=self._request, _leet=self._leet)
        self.answer_data_set = self._input_answer.answer_data_set
        self.answer_data = self.answer_data_set[self._subject_field]

        self.answer_student = self.get_answer_student()
        self.answer_submitted = self.get_answer_submitted()
        self.answer_all_confirmed = self.get_answer_all_confirmed()

    def get_subject_variable(self, subject_field) -> tuple[str, str, int, int]:
        for sub, (subject, fld, fld_idx, problem_count) in self._subject_vars.items():
            if subject_field == fld:
                return sub, subject, fld_idx, problem_count

    def get_answer_student(self):
        return [{'no': no, 'ans': ans} for no, ans in enumerate(self.answer_data, start=1)]

    def get_answer_submitted(self):
        return self._model.answer.objects.filter(
            student=self.student, problem__subject=self.sub).count() == self.problem_count

    def get_answer_all_confirmed(self) -> bool:
        answer_student_counts = self._model.answer.objects.filter(student=self.student).count()
        problem_count_sum = sum([cnt for (_, _, _, cnt) in self._subject_vars.values()])
        return answer_student_counts == problem_count_sum


@dataclass(kw_only=True)
class NormalAnswerInputData:
    _request: HtmxHttpRequest
    _leet: models.Leet
    _subject_field: str

    def __post_init__(self):
        self._model = ModelData()
        self._leet_data = LeetData(_leet=self._leet)
        self._student_data = NormalStudentData(
            _request=self._request, _leet=self._leet, _subject_field=self._subject_field)

        self._answer_data_set = self._student_data.answer_data_set
        self._answer_data = self._answer_data_set[self._subject_field]

        self._subject_vars = self._leet_data.subject_vars
        self._subject = self._student_data.subject
        self._problem_count = self._student_data.problem_count

        self.subject_name = self._subject
        self.answer_student = self._student_data.answer_student
        self.answer_submitted = self._student_data.answer_submitted

    def process_post_request_to_answer_input(self):
        try:
            no = int(self._request.POST.get('number'))
            ans = int(self._request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(subject=self._subject, answer=answer_temporary, exam=self._leet)
        response = render(self._request, 'a_prime/snippets/predict_answer_button.html', context)

        if 1 <= no <= self._problem_count and 1 <= ans <= 5:
            self._answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(self._answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    def get_next_url_for_answer_input(self) -> str:
        student = self._model.student.objects.leet_student_with_answer_count(self._request.user, self._leet)
        for sub, (_, fld, _, _) in self._subject_vars.items():
            if student.answer_count[sub] == 0:
                return self._leet.get_predict_answer_input_url(fld)
        return self._leet.get_predict_detail_url()


@dataclass(kw_only=True)
class NormalAnswerConfirmData:
    _request: HtmxHttpRequest
    _leet: models.Leet
    _subject_field: str

    def __post_init__(self):
        self._model = ModelData()

        self._leet_data = LeetData(_leet=self._leet)
        self._student_data = NormalStudentData(
            _request=self._request, _leet=self._leet, _subject_field=self._subject_field)

        self._subject_vars = self._leet_data.subject_vars
        self._sub = self._student_data.sub
        self._subject = self._student_data.subject
        self._field_idx = self._student_data.field_idx

        self._predict_leet = self._leet.predict_leet
        self._student = self._student_data.student
        self._score = self._student.score
        self._answer_data = self._student_data.answer_data

        self.subject_name = self._subject
        self.answer_student = self._student_data.answer_student
        self.answer_all_confirmed = self._student_data.answer_all_confirmed

    def process_post_request_to_answer_confirm(self):
        is_confirmed = all(self._answer_data)
        if is_confirmed:
            self.create_confirmed_answers()
            self.update_answer_counts_after_confirm()
            if self._predict_leet.is_answer_official_opened():
                self.update_score_for_targeted_student()
                self.update_rank_for_each_student('all')
                self.update_rank_for_each_student('aspiration_1')
                self.update_rank_for_each_student('aspiration_2')
                self.update_statistics_by_aspiration('all')
                self.update_statistics_by_aspiration('aspiration_1')
                self.update_statistics_by_aspiration('aspiration_2')

            if self.answer_all_confirmed and not self._predict_leet.is_answer_official_opened():
                self._student.is_filtered = True
                self._student.save()

        # Load student instance after save
        next_url = self.get_next_url_for_answer_input()

        context = update_context_data(header=f'{self._subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(self._request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    @with_bulk_create_or_update()
    def create_confirmed_answers(self):
        list_create = []
        for no, ans in enumerate(self._answer_data, start=1):
            problem = self._model.problem.objects.get(leet=self._leet, subject=self._sub, number=no)
            list_create.append(self._model.answer(student=self._student, problem=problem, answer=ans))
        return self._model.answer, list_create, [], []

    def update_answer_counts_after_confirm(self) -> None:
        qs_answer_count = self._model.ac_all.objects.predict_filtered_by_leet(self._leet).filter(sub=self._sub)
        for qs_ac in qs_answer_count:
            ans = self._answer_data[qs_ac.problem.number - 1]
            setattr(qs_ac, f'count_{ans}', F(f'count_{ans}') + 1)
            setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
            if not self._predict_leet.is_answer_official_opened:
                setattr(qs_ac, f'filtered_count_{ans}', F(f'count_{ans}') + 1)
                setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
            qs_ac.save()

    def update_score_for_targeted_student(self) -> None:
        correct_count = 0
        qs_answer = self._model.answer.objects.filtered_by_leet_student_and_sub(self._student, self._sub)
        for qs_a in qs_answer:
            answer_official_list = [int(digit) for digit in str(qs_a.answer_official)]
            correct_count += 1 if qs_a.answer_student in answer_official_list else 0

        setattr(self._score, f'raw_{self._subject_field}', correct_count)
        score_list = [sco for sco in [self._score.raw_subject_0, self._score.raw_subject_1] if sco is not None]  # noqa
        self._score.raw_sum = sum(score_list) if score_list else None
        self._score.save()

    def update_rank_for_each_student(self, aspiration_type: str) -> None:
        rank_model = self._model.rank_model_set.get(aspiration_type)
        target, _ = rank_model.objects.get_or_create(student=self._student)

        rank_list = self.get_rank_list(aspiration_type)
        participants = rank_list.count()
        fields_not_match = [target.participants != participants]

        for entry in rank_list:
            if entry.id == self._student.id:
                score_for_field = getattr(entry, f'rank_{self._field_idx}')
                score_for_sum = getattr(entry, f'rank_sum')
                fields_not_match.append(getattr(target, self._subject_field) != score_for_field)
                fields_not_match.append(getattr(target, 'sum') != entry.rank_sum)

                if any(fields_not_match):
                    target.participants = participants
                    setattr(target, self._subject_field, score_for_field)
                    setattr(target, f'sum', score_for_sum)
                    target.save()

    def get_rank_list(self, aspiration_type: str):
        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        rank_list = (
            self._model.student.objects.filter(leet=self._leet).order_by('id')
            .annotate(**{
                f'rank_{self._field_idx}': rank_func(f'score__raw_{self._subject_field}'),
                'rank_sum': rank_func('score__raw_sum')
            })
        )
        if aspiration_type != 'all':
            aspiration = getattr(self._student, aspiration_type)
            rank_list = rank_list.filter(**{aspiration_type: aspiration})
        return rank_list

    def update_statistics_by_aspiration(self, aspiration_type: str) -> None:
        if aspiration_type == 'aspiration_1':
            aspiration = self._student.aspiration_1
        elif aspiration_type == 'aspiration_2':
            aspiration = self._student.aspiration_2
        else:
            aspiration = '전체'

        stat = get_object_or_404(self._model.statistics, leet=self._leet, aspiration=aspiration)

        # Update participants for each subject [All, Filtered]
        self.update_participants(stat, aspiration_type, False, False)
        if not self._predict_leet.is_answer_official_opened:
            self.update_participants(stat, aspiration_type, True, False)

        # Update participants for sum [All, Filtered]
        if self.answer_all_confirmed:
            self.update_participants(stat, aspiration_type, False, True)
            if not self._predict_leet.is_answer_official_opened:
                self.update_participants(stat, aspiration_type, True, True)
        stat.save()

    def update_participants(self, stat, aspiration_type: str, is_filtered: bool, is_sum: bool) -> None:
        prefix = 'filtered_' if is_filtered else ''
        subject_field = 'sum' if is_sum else self._subject_field

        getattr(stat, f'{prefix}raw_{subject_field}')['participants'] += 1
        if aspiration_type == 'aspiration_1':
            getattr(stat, f'{prefix}raw_{subject_field}')['participants_1'] += 1
        if aspiration_type == 'aspiration_2':
            getattr(stat, f'{prefix}raw_{subject_field}')['participants_2'] += 1

    def get_next_url_for_answer_input(self) -> str:
        student = self._model.student.objects.leet_student_with_answer_count(self._request.user, self._leet)
        for sub, (_, fld, _, _) in self._subject_vars.items():
            if student.answer_count[sub] == 0:
                return self._leet.get_predict_answer_input_url(fld)
        return self._leet.get_predict_detail_url()


def get_loop_list(problem_count: int):
    loop_list = []
    quotient = problem_count // 10
    counter_list = [10] * quotient
    remainder = problem_count % 10
    if remainder:
        counter_list.append(remainder)
    loop_min = 0
    for idx, counter in enumerate(counter_list):
        loop_list.append({'counter': counter, 'min': loop_min})
        loop_min += 10
    return loop_list
