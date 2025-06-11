__all__ = [
    'NormalListData', 'NormalDetailData',
    'NormalRegisterData', 'NormalAnswerProcessData',
    'AdminListData', 'AdminDetailData',
    'AdminCreateData', 'AdminUpdateData',
    'AdminExportExcelData',
]

import json
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np
import pandas as pd
from django.db.models import Count, F, QuerySet, Window
from django.db.models.functions import Rank
from django.shortcuts import render, get_object_or_404, redirect
from django_htmx.http import reswap

from a_psat import models, forms
from a_psat.utils.variables import RequestData, PsatData
from common.utils import HtmxHttpRequest, get_paginator_context, update_context_data
from common.utils.export_excel_methods import *
from common.utils.modify_models_methods import *

UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.student = models.PredictStudent
        self.answer = models.PredictAnswer
        self.score = models.PredictScore
        self.rank_total = models.PredictRankTotal
        self.rank_category = models.PredictRankCategory
        self.answer_count_all = models.PredictAnswerCount
        self.answer_count_top = models.PredictAnswerCountTopRank
        self.answer_count_mid = models.PredictAnswerCountMidRank
        self.answer_count_low = models.PredictAnswerCountLowRank


@dataclass(kw_only=True)
class StudentAnswerData:
    psat_data: PsatData
    student: models.PredictStudent
    answer_data_set: dataclass_field(default_factory=dict)

    def __post_init__(self):
        self._predict_psat = self.psat_data.predict_psat
        self._subject_vars = self.psat_data.subject_vars
        self._subject_vars_avg = self.psat_data.subject_vars_avg
        self._time_schedule = self.psat_data.time_schedule
        self._subject_fields = self.psat_data.subject_fields

        self.qs_student_answer = models.PredictAnswer.objects.filtered_by_psat_student(self.student)
        self.is_confirmed_data = self.get_is_confirmed_data()

    def get_student_score_list(self):
        return [getattr(self.student.score, fld) for (_, fld, _, _) in self._subject_vars.values()]

    def get_is_confirmed_data(self) -> dict[str, bool]:
        is_confirmed_data = {sub: False for sub in self._subject_vars}
        confirmed_sub_list = self.qs_student_answer.values_list('subject', flat=True).distinct()
        for sub in confirmed_sub_list:
            is_confirmed_data[sub] = True
        is_confirmed_data['평균'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '평균'
        return is_confirmed_data

    def get_statistics_data(self, stat_type: str, is_filtered: bool) -> dict:
        participants_dict = self.get_participants_dict(stat_type, is_filtered)
        score_np_dict = self.get_score_np_dict(stat_type, is_filtered)
        answer_count_dict = self.get_answer_count_dict()

        is_confirmed_for_average = []
        stat_data = {}
        for sub, (subject, fld, _, problem_count) in self._subject_vars_avg.items():
            url_answer_input = self.student.psat.get_predict_answer_input_url(fld) if sub != '평균' else ''
            answer_count = answer_count_dict[sub] if sub != '평균' else sum(answer_count_dict.values())
            participants = 0
            rank = student_score = max_score = top_score_10 = top_score_20 = avg_score = 0
            if sub in participants_dict.keys():
                scores = score_np_dict[fld]
                participants = participants_dict[sub]
                is_confirmed_for_average.append(True)
                if self._predict_psat.is_answer_predict_opened:
                    pass
                if self._predict_psat.is_answer_official_opened:
                    student_score = getattr(self.student.score, fld)
                    if scores.any() and student_score:
                        sorted_scores = np.sort(scores)[::-1]
                        rank = int(np.where(sorted_scores == student_score)[0][0] + 1)
                        max_score = to_float(np.max(scores))
                        top_score_10 = to_float(np.percentile(scores, 90))
                        top_score_20 = to_float(np.percentile(scores, 80))
                        avg_score = to_float(np.mean(scores))
            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'start_time': self._time_schedule[sub][0],
                'end_time': self._time_schedule[sub][1],

                'participants': participants,
                'is_confirmed': self.is_confirmed_data[sub],
                'url_answer_input': url_answer_input,

                'score_predict': 0,
                'problem_count': problem_count,
                'answer_count': answer_count,

                'rank': rank, 'score': student_score, 'max_score': max_score,
                'top_score_10': top_score_10, 'top_score_20': top_score_20, 'avg_score': avg_score,
            }
        return stat_data

    def get_participants_dict(self, stat_type: str, is_filtered: bool) -> dict[str, int]:
        qs_answer = models.PredictAnswer.objects.filtered_by_psat_student_and_stat_type(
            self.student, stat_type, is_filtered)
        participants_dict = {qs_a['problem__subject']: qs_a['participant_count'] for qs_a in qs_answer}
        participants_dict['평균'] = participants_dict[min(participants_dict)] if participants_dict else 0
        return participants_dict

    def get_score_np_dict(self, stat_type: str, is_filtered: bool) -> dict[str, np.array]:
        qs_score = models.PredictScore.objects.predict_filtered_scores_of_student(self.student, stat_type, is_filtered)
        fields = self._subject_fields + ['average']
        subject_dict = {fld: [] for fld in fields}

        for row in qs_score:
            for fld in fields:
                subject_dict[fld].append(row[fld])

        return {fld: np.array(scores) for fld, scores in subject_dict.items()}

    def get_answer_count_dict(self) -> dict[str, int]:
        answer_count_dict = {}
        for sub, (subject, fld, _, problem_count) in self._subject_vars.items():
            answer_list = self.answer_data_set.get(fld)
            saved_answers = []
            if answer_list:
                saved_answers = [ans for ans in answer_list if ans]
            answer_count_dict[sub] = max(self.student.answer_count.get(sub, 0), len(saved_answers))
        return answer_count_dict


@dataclass(kw_only=True)
class ChartData:
    statistics_context: dict
    student: models.PredictStudent | None

    def __post_init__(self):
        psat_data = PsatData(psat=self.student.psat)

        self._subject_vars = psat_data.subject_vars
        self._student_score_list = self.get_student_score_list()

    def get_student_score_list(self):
        if self.student:
            return [getattr(self.student.score, fld) for (_, fld, _, _) in self._subject_vars.values()]

    def get_dict_stat_chart(self) -> dict:
        chart_score = {
            'all_avg': [], 'all_top_20': [], 'all_top_10': [], 'all_max': [],
            'dep_avg': [], 'dep_top_20': [], 'dep_top_10': [], 'dep_max': [],
        }
        if self.student:
            chart_score['my_score'] = self._student_score_list

        for stat in self.statistics_context['all']['page_obj'].values():
            chart_score['all_avg'].append(stat['avg_score'])
            chart_score['all_top_20'].append(stat['top_score_20'])
            chart_score['all_top_10'].append(stat['top_score_10'])
            chart_score['all_max'].append(stat['max_score'])
        for stat in self.statistics_context['department']['page_obj'].values():
            chart_score['dep_avg'].append(stat['avg_score'])
            chart_score['dep_top_20'].append(stat['top_score_20'])
            chart_score['dep_top_10'].append(stat['top_score_10'])
            chart_score['dep_max'].append(stat['max_score'])

        score_list = [score for score in self._student_score_list if score is not None]
        chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0
        return chart_score

    def get_dict_stat_frequency(self) -> dict:
        score_frequency_list = models.PredictStudent.objects.average_scores_over(self.student.psat, 50)
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
        if self.student and self.student.score.average:  # noqa
            bin_start = int((self.student.score.average // bin_size) * bin_size)  # noqa
            bin_end = bin_start + bin_size
            target_bin = f'{bin_start}~{bin_end}'

        return sorted_freq, target_bin


@dataclass(kw_only=True)
class NormalListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        self.qs_psat = self.get_qs_psat()

    def get_qs_psat(self):
        qs_psat = models.Psat.objects.predict_psat_active()
        student_dict = {}
        if self.request.user.is_authenticated:
            qs_student = models.PredictStudent.objects.registered_psat_student(self.request.user, qs_psat)
            student_dict = {qs_s.psat: qs_s for qs_s in qs_student}
        for qs_p in qs_psat:
            qs_p.student = student_dict.get(qs_p, None)
        return qs_psat


@dataclass(kw_only=True)
class NormalDetailData:
    request: HtmxHttpRequest
    student: models.PredictStudent

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        psat_data = PsatData(psat=self.student.psat)
        answer_data_set = get_input_answer_data_set(self.request, psat_data)

        self._subject_vars = psat_data.subject_vars
        self._student_answer_data = StudentAnswerData(
            psat_data=psat_data, student=self.student, answer_data_set=answer_data_set)
        self._qs_student_answer = self._student_answer_data.qs_student_answer

        self.view_type = request_data.view_type
        self.is_confirmed_data = self._student_answer_data.is_confirmed_data
        self.total_statistics_context = self.get_normal_statistics_context(False)
        self.filtered_statistics_context = self.get_normal_statistics_context(True)

        self.chart_data = ChartData(statistics_context=self.total_statistics_context, student=self.student)

    def get_normal_statistics_context(self, is_filtered: bool) -> dict:
        if is_filtered and not self.student.is_filtered:
            return {}

        suffix = 'Filtered' if is_filtered else 'Total'
        statistics_all = self._student_answer_data.get_statistics_data('all', is_filtered)
        statistics_department = self._student_answer_data.get_statistics_data('department', is_filtered)
        self.update_normal_score_predict(statistics_all)

        return {
            'all': {
                'id': '0', 'title': '전체 기준',
                'prefix': f'All{suffix}Score', 'page_obj': statistics_all,
            },
            'department': {
                'id': '1', 'title': '직렬 기준',
                'prefix': f'Department{suffix}Score', 'page_obj': statistics_department,
            },
        }

    def update_normal_score_predict(self, statistics_all: dict) -> None:
        score_predict = {sub: 0 for sub in self._subject_vars}
        predict_correct_count_list = self._qs_student_answer.filter(predict_result=True).values(
            'subject').annotate(correct_counts=Count('predict_result'))

        psat_sum = 0
        for entry in predict_correct_count_list:
            score = 0
            sub = entry['subject']
            problem_count = self._subject_vars[sub][3]
            if problem_count:
                score = entry['correct_counts'] * 100 / problem_count

            score_predict[sub] = score
            psat_sum += score if sub != '헌법' else 0
            statistics_all[sub]['score_predict'] = score
        statistics_all['평균']['score_predict'] = round(psat_sum / 3, 1)

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._subject_vars
        context = {
            sub: {
                'id': str(idx), 'title': sub, 'subject': subject, 'field': fld,
                'url_answer_input': self.student.psat.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count) in subject_vars.items()
        }

        for line in self._qs_student_answer:
            sub = line.problem.subject
            ans_official = line.problem.answer
            ans_student = line.answer
            ans_predict = line.problem.predict_answer_count.answer_predict

            line.no = line.problem.number
            line.ans_official = ans_official
            line.ans_official_circle = line.problem.get_answer_display

            line.ans_student = ans_student
            line.field = subject_vars[sub][1]

            line.ans_predict = ans_predict
            line.rate_accuracy = line.problem.predict_answer_count.get_answer_predict_rate()

            line.rate_correct = line.problem.predict_answer_count.get_answer_rate(ans_official)
            line.rate_correct_top = line.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            line.rate_correct_mid = line.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            line.rate_correct_low = line.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            if line.rate_correct_top is not None and line.rate_correct_low is not None:
                line.rate_gap = line.rate_correct_top - line.rate_correct_low
            else:
                line.rate_gap = 0

            line.rate_selection = line.problem.predict_answer_count.get_answer_rate(ans_student)
            line.rate_selection_top = line.problem.predict_answer_count_top_rank.get_answer_rate(ans_student)
            line.rate_selection_mid = line.problem.predict_answer_count_mid_rank.get_answer_rate(ans_student)
            line.rate_selection_low = line.problem.predict_answer_count_low_rank.get_answer_rate(ans_student)

            context[sub]['page_obj'].append(line)
        return context


@dataclass(kw_only=True)
class NormalRegisterData:
    request: HtmxHttpRequest
    psat: models.Psat

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.view_type = request_data.view_type

    def process_register(self, form, context):
        unit = form.cleaned_data['unit']
        department = form.cleaned_data['department']
        serial = form.cleaned_data['serial']
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        prime_id = form.cleaned_data['prime_id']

        categories = models.PredictCategory.objects.filtered_category_by_psat_unit(unit)
        context = update_context_data(context, categories=categories)

        category = models.PredictCategory.objects.filter(unit=unit, department=department).first()
        if category:
            qs_student = models.PredictStudent.objects.filter(psat=self.psat, user=self.request.user)
            if qs_student.exists():
                form.add_error(None, '이미 수험정보를 등록하셨습니다.')
                form.add_error(None, '만약 수험정보를 등록하신 적이 없다면 관리자에게 문의해주세요.')
                context = update_context_data(context, form=form)
                return render(self.request, 'a_psat/predict_register.html', context)

            qs_student = models.PredictStudent.objects.filter(serial=serial)
            if qs_student.exists():
                form.add_error('serial', '이미 등록된 수험번호입니다.')
                form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')
                context = update_context_data(context, form=form)
                return render(self.request, 'a_psat/predict_register.html', context)

            student = models.PredictStudent.objects.create(
                psat=self.psat, user=self.request.user, category=category,
                serial=serial, name=name, password=password, prime_id=prime_id,
            )
            models.PredictScore.objects.create(student=student)
            models.PredictRankTotal.objects.create(student=student)
            models.PredictRankCategory.objects.create(student=student)
            return redirect(self.psat.get_predict_detail_url())
        else:
            form.add_error(None, '직렬을 잘못 선택하셨습니다. 다시 선택해주세요.')
            context = update_context_data(context, form=form)
            return render(self.request, 'a_psat/predict_register.html', context)


@dataclass(kw_only=True)
class NormalAnswerProcessData:
    request: HtmxHttpRequest
    student: models.PredictStudent
    subject_field: str

    def __post_init__(self):
        psat_data = PsatData(psat=self.student.psat)

        self._psat = self.student.psat
        self._predict_psat = self.student.psat.predict_psat
        self._subject_vars = psat_data.subject_vars
        self._answer_data_set = get_input_answer_data_set(self.request, psat_data)
        self._answer_data = self._answer_data_set[self.subject_field]
        self._sub, self._subject, self._field_idx, self._problem_count = self.get_subject_variable()
        self._qs_answer = models.PredictAnswer.objects.filtered_by_psat_student_and_sub(self.student, self._sub)
        self._qs_answer_count = models.PredictAnswerCount.objects.predict_filtered_by_psat(
            self._psat).filter(sub=self._sub)

        self.subject_name = self._subject
        self.time_schedule = psat_data.time_schedule.get(self._sub)
        self.answer_student = self.get_answer_student()
        self.answer_submitted = self._qs_answer.exists()
        self.qs_student = models.PredictStudent.objects.filter(psat=self._psat).order_by('id')
        self.answer_all_confirmed = self.get_answer_all_confirmed()

    def get_subject_variable(self) -> tuple[str, str, int, int]:
        for sub, (subject, fld, fld_idx, problem_count) in self._subject_vars.items():
            if self.subject_field == fld:
                return sub, subject, fld_idx, problem_count

    def get_answer_student(self):
        return [{'no': no, 'ans': ans} for no, ans in enumerate(self._answer_data, start=1)]

    def process_post_request_to_answer_input(self):
        try:
            no = int(self.request.POST.get('number'))
            ans = int(self.request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(subject=self._subject, answer=answer_temporary, exam=self._psat)
        response = render(self.request, 'a_prime/snippets/predict_answer_button.html', context)

        if 1 <= no <= self._problem_count and 1 <= ans <= 5:
            self._answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(self._answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    def process_post_request_to_answer_confirm(self):
        is_confirmed = all(self._answer_data)
        if is_confirmed:
            self.create_confirmed_answers()
            self.update_answer_counts_after_confirm()
            self.update_score_for_each_student()
            self.update_rank_for_each_student('total')
            self.update_rank_for_each_student('department')
            self.update_statistics_by_department('전체')
            self.update_statistics_by_department(self.student.department)

            if self.answer_all_confirmed:
                if not self._predict_psat.is_answer_official_opened:
                    self.student.is_filtered = True
                    self.student.save()

        # Load student instance after save
        next_url = self.get_next_url_for_answer_input()

        context = update_context_data(header=f'{self._subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(self.request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    @with_bulk_create_or_update()
    def create_confirmed_answers(self):
        list_create, list_update = [], []
        for no, ans in enumerate(self._answer_data, start=1):
            problem = models.Problem.objects.get(psat=self._psat, subject=self._sub, number=no)
            list_create.append(models.PredictAnswer(student=self.student, problem=problem, answer=ans))
        return models.PredictAnswer, list_create, list_update, []

    def update_answer_counts_after_confirm(self) -> None:
        for qs_ac in self._qs_answer_count:
            ans_student = self._answer_data[qs_ac.problem.number - 1]
            setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
            if not self._predict_psat.is_answer_official_opened:
                setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
            qs_ac.save()

    def update_score_for_each_student(self) -> None:
        score = self.student.score
        correct_count = 0
        for qs_a in self._qs_answer:
            correct_count += 1 if qs_a.answer_student == qs_a.answer_correct else 0

        score_point = correct_count * 100 / self._problem_count
        setattr(score, self.subject_field, score_point)

        score_list = [sco for sco in [score.subject_1, score.subject_2, score.subject_3] if sco is not None]  # noqa
        score_sum = sum(score_list) if score_list else None
        score_average = round(score_sum / 3, 1) if score_sum else None

        score.sum = score_sum
        score.average = score_average
        score.save()

    def update_rank_for_each_student(self, stat_type: str) -> None:
        field_average = 'average'

        rank_model = models.PredictRankTotal
        if stat_type == 'department':
            rank_model = models.PredictRankCategory

        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        annotate_dict = {
            f'rank_{self._field_idx}': rank_func(f'score__{self.subject_field}'),
            'rank_average': rank_func(f'score__{field_average}')
        }

        rank_list = self.qs_student.annotate(**annotate_dict)
        if stat_type == 'department':
            rank_list = rank_list.filter(category=self.student.category)
        participants = rank_list.count()

        target, _ = rank_model.objects.get_or_create(student=self.student)
        fields_not_match = [target.participants != participants]

        for entry in rank_list:
            if entry.id == self.student.id:
                score_for_field = getattr(entry, f'rank_{self._field_idx}')
                score_for_average = getattr(entry, f'rank_average')
                fields_not_match.append(getattr(target, self.subject_field) != score_for_field)
                fields_not_match.append(target.average != entry.rank_average)

                if any(fields_not_match):
                    target.participants = participants
                    setattr(target, self.subject_field, score_for_field)
                    setattr(target, field_average, score_for_average)
                    target.save()

    def get_answer_all_confirmed(self) -> bool:
        answer_student_counts = models.PredictAnswer.objects.filter(student=self.student).count()
        problem_count_sum = sum([value[3] for value in self._subject_vars.values()])
        return answer_student_counts == problem_count_sum

    def update_statistics_by_department(self, department: str) -> None:
        stat = get_object_or_404(models.PredictStatistics, psat=self._psat, department=department)

        # Update participants for each subject [All, Filtered]
        getattr(stat, self.subject_field)['participants'] += 1
        if not self._predict_psat.is_answer_official_opened:
            getattr(stat, f'filtered_{self.subject_field}')['participants'] += 1

        # Update participants for average [All, Filtered]
        if self.answer_all_confirmed:
            stat.average['participants'] += 1
            if not self._predict_psat.is_answer_official_opened:
                stat.filtered_average['participants'] += 1
                self.student.is_filtered = True
                self.student.save()
        stat.save()

    def get_next_url_for_answer_input(self) -> str:
        self.student = models.PredictStudent.objects.psat_student_with_answer_count(self.request.user, self._psat)
        for sub, (_, fld, _, _) in self._subject_vars.items():
            if self.student.answer_count[sub] == 0:
                return self._psat.get_predict_answer_input_url(fld)
        return self._psat.get_predict_detail_url()


@dataclass(kw_only=True)
class AdminListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

    def get_predict_psat_context(self):
        predict_psat_list = models.PredictPsat.objects.select_related('psat')
        return get_paginator_context(predict_psat_list, self.page_number)


@dataclass(kw_only=True)
class AdminDetailData:
    request: HtmxHttpRequest
    psat: models.Psat

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        psat_data = PsatData(psat=self.psat)

        self._subject_vars = psat_data.subject_vars
        self._subject_vars_avg = psat_data.subject_vars_avg
        self._qs_problem = models.Problem.objects.filtered_problem_by_psat(self.psat)
        self._qs_answer_count = models.PredictAnswerCount.objects.predict_filtered_by_psat(self.psat)

        self.exam_subject = request_data.exam_subject
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.student_name = request_data.student_name

    def get_admin_problem_context(self):
        return {'problem_context': get_paginator_context(self._qs_problem, self.page_number)}

    def get_admin_statistics_context(self, per_page=10) -> dict:
        total_data, filtered_data = self.get_admin_statistics_data()
        total_context = get_paginator_context(total_data, self.page_number, per_page)
        filtered_context = get_paginator_context(filtered_data, self.page_number, per_page)
        total_context.update({
            'id': '0', 'title': '전체', 'prefix': 'TotalStatistics', 'header': 'total_statistics_list',
        })
        filtered_context.update({
            'id': '1', 'title': '필터링', 'prefix': 'FilteredStatistics', 'header': 'filtered_statistics_list',
        })
        return {'statistics_context': {'total': total_context, 'filtered': filtered_context}}

    def get_admin_statistics_data(self) -> tuple[list, list]:
        department_list = list(
            models.PredictCategory.objects.filter(exam=self.psat.exam).order_by('order')
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
            models.PredictStudent.objects.filter(psat=self.psat)
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

    def get_admin_catalog_context(self, for_search=False) -> dict:
        total_list = models.PredictStudent.objects.filtered_student_by_psat(self.psat)
        if for_search:
            total_list = total_list.filter(name=self.student_name)
        filtered_list = total_list.filter(is_filtered=True)
        total_context = get_paginator_context(total_list, self.page_number)
        filtered_context = get_paginator_context(filtered_list, self.page_number)

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

    def get_admin_answer_context(self, for_pagination=False, per_page=10) -> dict:
        sub_list = [sub for sub in self._subject_vars]
        qs_answer_count_group = {sub: [] for sub in self._subject_vars}
        answer_context = {}

        subject = self.exam_subject if for_pagination else None
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_psat_and_subject(self.psat, subject)
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            if sub not in qs_answer_count_group:
                qs_answer_count_group[sub] = []
            qs_answer_count_group[sub].append(qs_ac)

        for sub, qs_answer_count in qs_answer_count_group.items():
            if qs_answer_count:
                data_answers = self.get_admin_answer_data(qs_answer_count)
                context = get_paginator_context(data_answers, self.page_number, per_page)
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

    def get_admin_only_answer_context(self, queryset: QuerySet) -> dict:
        query_dict = defaultdict(list)
        for query in queryset.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for sub, (_, _, idx, _) in self._subject_vars.items()
        }

    def get_admin_answer_predict_context(self):
        return {'answer_predict_context': self.get_admin_only_answer_context(self._qs_answer_count)}

    def get_admin_answer_official_context(self):
        return {'answer_official_context': self.get_admin_only_answer_context(self._qs_problem)}


@dataclass(kw_only=True)
class AdminCreateData:
    form: forms.PredictPsatForm

    def __post_init__(self):
        year = self.form.cleaned_data['year']
        exam = self.form.cleaned_data['exam']
        self._psat = models.Psat.objects.get(year=year, exam=exam)

    def process_post_request(self):
        predict_psat, _ = models.PredictPsat.objects.get_or_create(psat=self._psat)
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
        problems = models.Problem.objects.filter(psat=self._psat).order_by('id')
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

    @with_bulk_create_or_update()
    def create_statistics_model_instances(self):
        department_list = list(
            models.PredictCategory.objects.filter(exam=self._psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        list_create = []
        for department in department_list:
            append_list_create(models.PredictStatistics, list_create, psat=self._psat, department=department)
        return models.PredictStatistics, list_create, [], []


@dataclass(kw_only=True)
class AdminUpdateData:
    request: HtmxHttpRequest
    psat: models.Psat

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        psat_data = PsatData(psat=self.psat)
        model_data = ModelData()

        self._subject_vars = psat_data.subject_vars
        self._subject_vars_avg = psat_data.subject_vars_avg
        self._sub_list = [sub for sub in self._subject_vars]
        self._qs_student = models.PredictStudent.objects.filter(psat=self.psat).order_by('id')

        self._answer_model = model_data.answer
        self._score_model = model_data.score
        self._rank_total_model = model_data.rank_total
        self._rank_category_model = model_data.rank_category
        self._answer_count_all_model = model_data.answer_count_all
        self._answer_count_top_model = model_data.answer_count_top
        self._answer_count_mid_model = model_data.answer_count_mid
        self._answer_count_low_model = model_data.answer_count_low

        self.view_type = request_data.view_type

    def update_problem_model_for_answer_official(self) -> tuple[bool | None, str]:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '정답을 업데이트했습니다.',
            False: '기존 정답과 일치합니다.',
        }
        list_create, list_update = [], []

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
                            problem = models.Problem.objects.get(psat=self.psat, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except models.Problem.DoesNotExist:
                            problem = models.Problem(
                                psat=self.psat, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(models.Problem, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        return [self.update_score_model()]

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        return [
            self.update_rank_model(self._rank_total_model, False),
            self.update_rank_model(self._rank_total_model, True),
            self.update_rank_model(self._rank_category_model, False),
            self.update_rank_model(self._rank_category_model, True),
        ]

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        total_data, filtered_data = self.get_statistics_data()
        return [
            self.update_statistics_model(total_data, False),
            self.update_statistics_model(filtered_data, True),
        ]

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        return [
            self.update_answer_count_model(self._answer_count_all_model, False),
            self.update_answer_count_model(self._answer_count_top_model, False),
            self.update_answer_count_model(self._answer_count_mid_model, False),
            self.update_answer_count_model(self._answer_count_low_model, False),

            self.update_answer_count_model(self._answer_count_all_model, True),
            self.update_answer_count_model(self._answer_count_top_model, True),
            self.update_answer_count_model(self._answer_count_mid_model, True),
            self.update_answer_count_model(self._answer_count_low_model, True),
        ]

    @with_bulk_create_or_update()
    def update_score_model(self):
        list_create, list_update = [], []

        for student in self._qs_student:
            original_score_instance, _ = self._score_model.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self._sub_list):
                problem_count = 25 if sub == '헌법' else 40
                correct_count = 0

                qs_answer = (
                    self._answer_model.objects.filter(student=student, problem__subject=sub)
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
        return self._score_model, list_create, list_update, update_fields

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
            if rank_model == self._rank_category_model:
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
            models.PredictCategory.objects.filter(exam=self.psat.exam).order_by('order')
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
            models.PredictStudent.objects.filter(psat=self.psat)
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
                instance = models.PredictStatistics.objects.get(psat=self.psat, department=department)
                fields_not_match = any(
                    getattr(instance, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except models.PredictStatistics.DoesNotExist:
                list_create.append(models.PredictStatistics(psat=self.psat, **stat_dict))
        update_fields = [
            'department', f'{prefix}subject_0', f'{prefix}subject_1',
            f'{prefix}subject_2', f'{prefix}subject_3', f'{prefix}average',
        ]
        is_updated = bulk_create_or_update(models.PredictStatistics, list_create, list_update, update_fields)
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
        if answer_count_model == self._answer_count_top_model:
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif answer_count_model == self._answer_count_mid_model:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif answer_count_model == self._answer_count_low_model:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        qs_answer = (
            self._answer_model.objects.filter(**lookup_exp)
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
class AdminExportExcelData:
    psat: models.Psat

    def __post_init__(self):
        psat_data = PsatData(psat=self.psat)

        self._subject_vars = psat_data.subject_vars
        self._subject_vars_avg = psat_data.subject_vars_avg
        self._sub_list = [sub for sub in self._subject_vars]

    def get_statistics_response(self) -> HttpResponse:
        qs_statistics = models.PredictStatistics.objects.filter(psat=self.psat).order_by('id')
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
        qs_student = models.PredictStudent.objects.filter(psat=self.psat).values(
            'id', 'created_at', 'name', 'prime_id').order_by('id')
        df = pd.DataFrame.from_records(qs_student)
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        filename = f'{self.psat.full_reference}_참여자명단.xlsx'
        column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        total_student_list = models.PredictStudent.objects.filtered_student_by_psat(self.psat)
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
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_psat_and_subject(self.psat)
        filename = f'{self.psat.full_reference}_문항분석표.xlsx'

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


def to_float(data, decimal=1):
    return round(float(data), decimal)


def get_input_answer_data_set(request: HtmxHttpRequest, psat_data: PsatData) -> dict:
    empty_answer_data = {
        fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in psat_data.subject_vars.items()
    }
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


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
