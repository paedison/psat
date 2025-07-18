__all__ = [
    'NormalRedirectContext', 'TemporaryAnswerContext', 'ChartContext',
    'NormalListContext', 'NormalDetailAnswerContext', 'NormalDetailStatisticsContext',
    'NormalRegisterContext', 'NormalAnswerInputContext', 'NormalAnswerConfirmContext',
]

import json
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db.models import Count, F
from django.shortcuts import render, redirect
from django_htmx.http import reswap

from a_leet.utils.common_utils import *
from common.utils import HtmxHttpRequest, update_context_data
from common.utils.export_excel_methods import *
from common.utils.modify_models_methods import *

_model = ModelData()

UPDATE_MESSAGES = {
    'raw_score': get_update_messages('원점수'),
    'score': get_update_messages('표준점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class NormalRedirectContext:
    _request: HtmxHttpRequest
    _context: dict

    def add_error_message(self, message: str):
        messages.error(self._request, message, extra_tags='alert-danger')

    def redirect_to_no_predict_psat(self):
        self.add_error_message('합격 예측 대상 시험이 아닙니다.')
        next_url = self._context['config'].url_list
        context = update_context_data(self._context, next_url=next_url)
        return render(self._request, 'redirect.html', context)

    def redirect_to_has_student(self):
        self.add_error_message('등록된 수험정보가 존재합니다.')
        next_url = self._context['config'].url_list
        context = update_context_data(self._context, next_url=next_url)
        return render(self._request, 'redirect.html', context)

    def redirect_to_no_student(self):
        self.add_error_message('등록된 수험정보가 없습니다.')
        next_url = self._context['config'].url_list
        context = update_context_data(self._context, next_url=next_url)
        return render(self._request, 'redirect.html', context)

    def redirect_to_before_exam_start(self):
        self.add_error_message('시험 시작 전입니다.')
        next_url = self._context['config'].url_detail
        context = update_context_data(self._context, next_url=next_url)
        return render(self._request, 'redirect.html', context)

    def redirect_to_already_submitted(self):
        self.add_error_message('이미 답안을 제출하셨습니다.')
        next_url = self._context['config'].url_detail
        context = update_context_data(self._context, next_url=next_url)
        return render(self._request, 'redirect.html', context)


@dataclass(kw_only=True)
class TemporaryAnswerContext:
    _request: HtmxHttpRequest
    _context: dict

    def get_total_answer_set(self) -> dict:
        subject_vars = self._context['subject_vars']
        empty_answer_data = {fld: [0 for _ in range(cnt)] for (_, fld, _, cnt) in subject_vars.values()}
        total_answer_set_cookie = self._request.COOKIES.get('total_answer_set', '{}')
        total_answer_set = json.loads(total_answer_set_cookie) or empty_answer_data
        return total_answer_set

    def get_answer_student_list_for_subject(self):
        subject_field = self._context.get('subject_field', '')
        total_answer_set = self.get_total_answer_set()
        answer_data = total_answer_set.get(subject_field, [])
        return [{'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)]

    def get_answer_student_for_subject(self):
        subject_field = self._context.get('subject_field', '')
        total_answer_set = self.get_total_answer_set()
        return total_answer_set.get(subject_field, [])


@dataclass(kw_only=True)
class ChartContext:
    _statistics_context: dict
    _student: _model.student | None

    def __post_init__(self):
        self._subject_variants = SubjectVariants()
        self._subject_vars = self._subject_variants.subject_vars
        self._subject_fields_sum = self._subject_variants.subject_fields_sum
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
        score_frequency_list = _model.student.objects.average_scores_over(self._student.leet, 50)
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
class NormalListContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        self.qs_leet = self.get_qs_leet()

    def get_qs_leet(self):
        qs_leet = _model.leet.objects.predict_leet_active()
        student_dict = {}
        if self._request.user.is_authenticated:
            qs_student = _model.student.objects.registered_leet_student(self._request.user, qs_leet)
            student_dict = {qs_s.leet: qs_s for qs_s in qs_student}
        for qs_p in qs_leet:
            qs_p.student = student_dict.get(qs_p, None)
        return qs_leet


@dataclass(kw_only=True)
class NormalDetailAnswerContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self.is_confirmed_data = self.get_is_confirmed_data()

    def get_is_confirmed_data(self) -> dict[str, bool]:
        is_confirmed_data = {sub: False for sub in self._context['subject_vars']}
        confirmed_sub_list = self._context['qs_student_answer'].values_list('subject', flat=True).distinct()
        for sub in confirmed_sub_list:
            is_confirmed_data[sub] = True
        is_confirmed_data['총점'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '총점'
        return is_confirmed_data

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._context['subject_vars']
        context = {
            sub: {
                'id': str(idx), 'title': subject, 'subject': subject, 'field': fld,
                'url_answer_input': self._context['student'].leet.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count) in subject_vars.items()
        }
        qs_student_answer = self._context['qs_student_answer']

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


@dataclass(kw_only=True)
class NormalDetailStatisticsContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']

    def is_analyzing(self):
        return True if self._student.score.sum is None else False

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
        subject_vars_sum = self._context['subject_vars_dict']['sum_last']
        time_schedule = self._context['time_schedule']
        predict_leet = self._context['predict_leet']
        is_confirmed_data = self._context['is_confirmed_data']
        student = self._student

        stat_data = {}
        for sub, (subject, fld, _, problem_count) in subject_vars_sum.items():
            url_answer_input = student.leet.get_predict_answer_input_url(fld) if sub != '총점' else ''
            answer_count = answer_count_dict[sub] if sub != '총점' else sum(answer_count_dict.values())

            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'start_time': time_schedule[sub][0],
                'end_time': time_schedule[sub][1],

                'is_confirmed': is_confirmed_data[sub],
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
                if predict_leet.is_answer_predict_opened:
                    pass
                if predict_leet.is_answer_official_opened:
                    raw_score = getattr(student.score, f'raw_{fld}')
                    score = getattr(student.score, fld)
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
        total_answer_set = self._context['total_answer_set']
        subject_vars = self._context['subject_vars_dict']['base']

        answer_count_dict = {}
        for sub, (_, fld, _, _) in subject_vars.items():
            answer_list = total_answer_set.get(fld)
            saved_answers = []
            if answer_list:
                saved_answers = [ans for ans in answer_list if ans]
            answer_count_dict[sub] = max(self._student.answer_count.get(sub, 0), len(saved_answers))
        return answer_count_dict

    def get_participants(self, stat_type: str, is_filtered: bool, sub: str):
        qs_answer = (
            _model.answer.objects.filter(problem__leet=self._student.leet)
            .order_by('student')
            .values(
                sub=F('problem__subject'), is_filtered=F('student__is_filtered'),
                aspiration_1=F('student__aspiration_1'), aspiration_2=F('student__aspiration_2'),
            ).distinct()
        )
        df = pd.DataFrame(qs_answer)

        if not df.empty:
            if stat_type != 'all':
                aspiration = getattr(self._student, stat_type)
                if aspiration:
                    df = df[df[stat_type] == aspiration]
            if is_filtered:
                df = df[df['is_filtered'] is True]
            if sub == '총점':
                return min([df[df['sub'] == _sub].shape[0] for _sub in self._context['subject_vars_dict']['base']])
            return df[df['sub'] == sub].shape[0]

    def get_score_np(self, stat_type: str, is_filtered: bool, fld: str):
        qs_score = (
            _model.score.objects.filter(student__leet=self._student.leet)
            .order_by('student')
            .values(
                'subject_0', 'subject_1', 'sum',
                is_filtered=F('student__is_filtered'),
                aspiration_1=F('student__aspiration_1'),
                aspiration_2=F('student__aspiration_2'),
            )
        )
        df = pd.DataFrame(qs_score)

        if stat_type != 'all':
            aspiration = getattr(self._student, stat_type)
            if aspiration:
                df = df[df[stat_type] == aspiration]
        if is_filtered:
            df = df[df['is_filtered'] is True]
        return df[[fld]].to_numpy()

    def update_score_predict(self, statistics_all: dict) -> None:
        predict_correct_count_list = self._context['qs_student_answer'].filter(predict_result=True).values(
            'subject').annotate(correct_counts=Count('predict_result'))
        leet_sum = 0
        for entry in predict_correct_count_list:
            sub = entry['subject']
            score = entry['correct_counts']
            leet_sum += score
            statistics_all[sub]['raw_score_predict'] = score
        statistics_all['총점']['raw_score_predict'] = leet_sum


@dataclass(kw_only=True)
class NormalRegisterContext:
    _request: HtmxHttpRequest
    _context: dict

    def process_register(self):
        form = self._context['form']
        leet = self._context['leet']
        student_model = _model.student

        if student_model.objects.filter(leet=leet, user=self._request.user).exists():
            form.add_error(None, '이미 수험정보를 등록하셨습니다.')
            form.add_error(None, '만약 수험정보를 등록하신 적이 없다면 관리자에게 문의해주세요.')
            context = update_context_data(self._context, form=form)
            return render(self._request, 'a_leet/predict_register.html', context)

        serial = form.cleaned_data['serial']
        if student_model.objects.filter(serial=serial).exists():
            form.add_error('serial', '이미 등록된 수험번호입니다.')
            form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')
            context = update_context_data(self._context, form=form)
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
            context = update_context_data(self._context, form=form)
            return render(self._request, 'a_leet/predict_register.html', context)

        student, is_created = student_model.objects.get_or_create(
            leet=leet, user=self._request.user, serial=serial,
            name=form.cleaned_data['name'],
            password=form.cleaned_data['password'],
            **additional_fields,
        )
        if is_created:
            _model.score.objects.create(student=student)
            _model.rank.objects.create(student=student)
            _model.rank_1.objects.create(student=student)
            _model.rank_2.objects.create(student=student)
        return redirect(leet.get_predict_detail_url())


@dataclass(kw_only=True)
class NormalAnswerInputContext:
    _request: HtmxHttpRequest
    _context: dict

    def already_submitted(self):
        student = self._context['student']
        sub = self._context['sub']
        cnt = self._context['problem_count']
        return _model.answer.objects.filter(student=student, problem__subject=sub).count() == cnt

    def process_post_request_to_answer_input(self):
        problem_count = self._context['problem_count']
        subject_field = self._context['subject_field']
        total_answer_set = self._context['total_answer_set']

        try:
            no = int(self._request.POST.get('number'))
            ans = int(self._request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(self._context, answer=answer_temporary)
        response = render(self._request, 'a_leet/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count and 1 <= ans <= 5:
            total_answer_set[subject_field][no - 1] = ans
            response.set_cookie('total_answer_set', json.dumps(total_answer_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')


@dataclass(kw_only=True)
class NormalAnswerConfirmContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']
        self._leet = self._context['leet']
        self._answer_official_opened = self._leet.predict_leet.is_answer_official_opened()
        self._answer_all_confirmed = self.get_answer_all_confirmed()

    def get_answer_all_confirmed(self) -> bool:
        answer_student_counts = _model.answer.objects.filter(student=self._student).count()
        problem_count_sum = sum([cnt for (_, _, _, cnt) in self._context['subject_vars_dict']['base'].values()])
        return answer_student_counts == problem_count_sum

    def get_header(self):
        subject = self._context['subject']
        return f'{subject} 답안 제출'

    def process_post_request_to_answer_confirm(self):
        answer_student = self._context['answer_student']
        is_confirmed = all(answer_student)
        if is_confirmed:
            self.create_confirmed_answers(answer_student)
            self.update_answer_counts_after_confirm(answer_student)
            self.update_participants_of_statistics()

            if self._answer_all_confirmed and not self._answer_official_opened:
                self._student.is_filtered = True
                self._student.save()
                print(f'{self._student} is now filtered as True.')

        # Load student instance after save
        next_url = self.get_next_url_for_answer_input()

        context = update_context_data(
            self._context, header=self.get_header(), is_confirmed=is_confirmed, next_url=next_url)
        return render(self._request, 'a_leet/snippets/modal_answer_confirmed.html', context)

    @with_bulk_create_or_update()
    def create_confirmed_answers(self, answer_student):
        list_create = []
        for number, answer in enumerate(answer_student, start=1):
            problem = _model.problem.objects.get(leet=self._leet, subject=self._context['sub'], number=number)
            list_create.append(_model.answer(student=self._student, problem=problem, answer=answer))
        return _model.answer, list_create, [], []

    def update_answer_counts_after_confirm(self, answer_student) -> None:
        qs_answer_count = _model.ac_all.objects.predict_filtered_by_leet(self._leet).filter(sub=self._context['sub'])

        count_all, count_filtered = 0, 0
        for qs_ac in qs_answer_count:
            ans_student = answer_student[qs_ac.problem.number - 1]
            setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)

            count_all += 1
            if not self._answer_official_opened:
                setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
                count_filtered += 1
            qs_ac.save()

        if count_all:
            print(f'{count_all} {_model.ac_all} instances saved.')
        if count_filtered:
            print(f'{count_filtered} {_model.ac_all} instances(filtered) saved.')

    def update_participants_of_statistics(self) -> None:
        subject_field = self._context['subject_field']

        aspirations = {'': '전체'}
        for suffix in ['_1', '_2']:
            aspiration = getattr(self._student, f'aspiration{suffix}')
            if aspiration:
                aspirations[suffix] = aspiration

        for suffix, aspiration in aspirations.items():
            target, _ = _model.statistics.objects.get_or_create(leet=self._leet, aspiration=aspiration)

            def update_participants(is_filtered: bool, is_sum: bool) -> None:
                prefix = 'filtered_' if is_filtered else ''
                field = 'sum' if is_sum else subject_field
                getattr(target, f'{prefix}{field}')[f'participants{suffix}'] += 1
                getattr(target, f'{prefix}raw_{field}')[f'participants{suffix}'] += 1

            # Update participants for each subject [All, Filtered]
            update_participants(False, False)
            if not self._answer_official_opened:
                update_participants(True, False)

            # Update participants for sum [All, Filtered]
            if self._answer_all_confirmed:
                update_participants(False, True)
                if not self._answer_official_opened:
                    update_participants(True, True)

            target.save()

    def get_next_url_for_answer_input(self) -> str:
        student = _model.student.objects.leet_student_with_answer_count(self._request.user, self._leet)
        for sub, (_, fld, _, _) in self._context['subject_vars_dict']['base'].items():
            if student.answer_count[sub] == 0:
                return self._leet.get_predict_answer_input_url(fld)
        return self._leet.get_predict_detail_url()
