__all__ = [
    'NormalRedirectContext', 'TemporaryAnswerContext',
    'NormalListContext', 'NormalDetailContext', 'NormalRegisterContext',
    'NormalAnswerInputContext', 'NormalAnswerConfirmContext',
    'ChartContext',
]

import json
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django_htmx.http import reswap

from a_psat.utils.predict.common_utils import ModelData
from a_psat.utils.variables import SubjectVariants
from common.utils import HtmxHttpRequest, update_context_data
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
class NormalRedirectContext:
    _request: HtmxHttpRequest
    _context: dict

    def redirect_to_no_predict_psat(self):
        next_url = self._context['config'].url_list
        context = update_context_data(
            self._context, message='합격 예측 대상 시험이 아닙니다.', next_url=next_url)
        return render(self._request, 'a_psat/redirect.html', context)

    def redirect_to_has_student(self):
        next_url = self._context['config'].url_list
        context = update_context_data(
            self._context, message='등록된 수험정보가 존재합니다.', next_url=next_url)
        return render(self._request, 'a_psat/redirect.html', context)

    def redirect_to_no_student(self):
        next_url = self._context['config'].url_list
        context = update_context_data(
            self._context, message='등록된 수험정보가 없습니다.', next_url=next_url)
        return render(self._request, 'a_psat/redirect.html', context)

    def redirect_to_before_exam_start(self):
        next_url = self._context['config'].url_detail
        context = update_context_data(
            self._context, message='시험 시작 전입니다.', next_url=next_url)
        return render(self._request, 'a_psat/redirect.html', context)

    def redirect_to_already_submitted(self):
        next_url = self._context['config'].url_detail
        context = update_context_data(
            self._context, message='이미 답안을 제출하셨습니다.', next_url=next_url)
        return render(self._request, 'a_psat/redirect.html', context)


@dataclass(kw_only=True)
class TemporaryAnswerContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._psat = self._context['psat']
        self._subject_field = self._context.get('subject_field', '')
        self._student = self._context['student']

    def get_total_answer_set(self) -> dict:
        subject_vars = self._context['subject_vars']
        empty_answer_set = {fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in subject_vars.items()}
        total_answer_set_cookie = self._request.COOKIES.get('total_answer_set', '{}')
        total_answer_set = json.loads(total_answer_set_cookie) or empty_answer_set
        return total_answer_set

    def get_answer_student_list_for_subject(self):
        total_answer_set = self.get_total_answer_set()
        answer_data = total_answer_set.get(self._subject_field, [])
        return [{'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)]

    def get_answer_student_for_subject(self):
        total_answer_set = self.get_total_answer_set()
        return total_answer_set.get(self._subject_field, [])


@dataclass(kw_only=True)
class NormalListContext:
    _request: HtmxHttpRequest

    def get_psats_context(self):
        qs_psat = _model.psat.objects.predict_psat_active()
        psat_list = qs_psat.values_list('id', flat=True)
        student_dict = {}
        if self._request.user.is_authenticated:
            qs_student = _model.student.objects.registered_psat_student(self._request.user, psat_list)
            student_dict = {qs_s.psat: qs_s for qs_s in qs_student}
        for qs_p in qs_psat:
            qs_p.student = student_dict.get(qs_p, None)
        return qs_psat

    def get_login_url_context(self):
        return reverse_lazy('account_login') + '?next=' + self._request.get_full_path()


@dataclass(kw_only=True)
class NormalDetailContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student_answer_context = StudentAnswerContext(_context=self._context)
        self._qs_student_answer = self._student_answer_context.qs_student_answer

        self.is_confirmed_data = self._student_answer_context.is_confirmed_data

    def get_normal_statistics_context(self, is_filtered: bool) -> dict:
        student = self._context['student']
        if is_filtered and not student.is_filtered:
            return {}

        suffix = 'Filtered' if is_filtered else 'Total'
        statistics_all = self._student_answer_context.get_statistics_data('all', is_filtered)
        statistics_department = self._student_answer_context.get_statistics_data('department', is_filtered)

        self.update_normal_statistics_context_for_score(statistics_all, 'result')
        self.update_normal_statistics_context_for_score(statistics_department, 'predict')

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

    def update_normal_statistics_context_for_score(self, statistics_all: dict, score_type: str) -> None:
        subject_vars = self._context['subject_vars']
        correct_count_list = (
            self._qs_student_answer
            .filter(**{f'is_{score_type}_correct': True})
            .values('subject').annotate(correct_counts=Count(f'is_{score_type}_correct'))
        )

        psat_sum = 0
        for entry in correct_count_list:
            score = 0
            sub = entry['subject']
            problem_count = subject_vars[sub][3]
            if problem_count:
                score = entry['correct_counts'] * 100 / problem_count

            psat_sum += score if sub != '헌법' else 0
            statistics_all[sub][f'score_{score_type}'] = score
        statistics_all['평균'][f'score_{score_type}'] = round(psat_sum / 3, 1)

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._context['subject_vars']
        student = self._context['student']

        sub_list = [sub for sub in subject_vars]
        context = {sub: {'id': str(idx)} for idx, sub in enumerate(sub_list)}

        for sub, (subject, fld, idx, problem_count) in subject_vars.items():
            context[sub].update({
                'title': sub, 'subject': subject, 'field': fld,
                'url_answer_input': student.psat.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            })

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
class NormalRegisterContext:
    _request: HtmxHttpRequest
    _psat: _model.psat

    def process_register(self, form, context):
        psat = self._psat
        user = self._request.user

        unit = form.cleaned_data['unit']
        department = form.cleaned_data['department']
        serial = form.cleaned_data['serial']
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        prime_id = form.cleaned_data['prime_id']

        categories = _model.category.objects.filtered_category_by_psat_unit(unit)
        context = update_context_data(context, categories=categories)

        category = _model.category.objects.filter(unit=unit, department=department).first()
        if category:
            qs_student = _model.student.objects.filter(psat=psat, user=user)
            if qs_student.exists():
                return self.redirect_to_already_registered(form, context)

            qs_student = _model.student.objects.filter(serial=serial)
            if qs_student.exists():
                return self.redirect_to_duplicated_serial(form, context)

            self.create_model_instances(
                category=category, serial=serial, name=name, password=password, prime_id=prime_id)

            return redirect(psat.get_predict_detail_url())
        else:
            return self.redirect_to_no_category(form, context)

    def create_model_instances(self, **kwargs):
        student = _model.student.objects.create(psat=self._psat, user=self._request.user, **kwargs)
        _model.score.objects.create(student=student)
        _model.rank_total.objects.create(student=student)
        _model.rank_category.objects.create(student=student)

    def redirect_to_already_registered(self, form, context):
        form.add_error(None, '이미 수험정보를 등록하셨습니다.')
        form.add_error(None, '만약 수험정보를 등록하신 적이 없다면 관리자에게 문의해주세요.')
        context = update_context_data(context, form=form)
        return render(self._request, 'a_psat/predict_register.html', context)

    def redirect_to_duplicated_serial(self, form, context):
        form.add_error('serial', '이미 등록된 수험번호입니다.')
        form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')
        context = update_context_data(context, form=form)
        return render(self._request, 'a_psat/predict_register.html', context)

    def redirect_to_no_category(self, form, context):
        form.add_error(None, '직렬을 잘못 선택하셨습니다.')
        form.add_error(None, '다시 선택해주세요.')
        context = update_context_data(context, form=form)
        return render(self._request, 'a_psat/predict_register.html', context)


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
        response = render(self._request, 'a_prime/snippets/predict_answer_button.html', context)

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
        self._student: _model.student = self._context['student']
        self._psat: _model.psat = self._context['psat']
        self._predict_psat = self._psat.predict_psat

        self._subject_vars = self._context['subject_vars']
        self._subject_field = self._context['subject_field']
        self._subject = self._context['subject']
        self._sub = self._context['sub']

        self._answer_all_confirmed = self.get_answer_all_confirmed()

    def get_answer_all_confirmed(self) -> bool:
        confirmed_answers_count = _model.answer.objects.filter(student=self._student).count()
        all_problems_count = sum([value[3] for value in self._subject_vars.values()])
        return confirmed_answers_count == all_problems_count

    def get_header(self):
        return f'{self._subject} 답안을 제출하시겠습니까?'

    def get_score_df(self):
        return pd.DataFrame(
            _model.score.objects.filter(student__psat=self._psat).order_by('student').values(
                'student_id', self._subject_field, 'average',
                category_id=F('student__category_id'),
                is_filtered=F('student__is_filtered'),
            )
        )

    def process_post_request_to_answer_confirm(self):
        answer_student = self._context['answer_student']
        is_confirmed = all(answer_student)
        if is_confirmed:
            self.create_confirmed_answers(answer_student)
            self.update_answer_counts_after_confirm(answer_student)
            self.update_score_of_student()

            score_df = self.get_score_df()
            self.update_rank_of_student(score_df, 'total')
            self.update_rank_of_student(score_df, 'category')

            self.update_participants_of_statistics('전체')
            self.update_participants_of_statistics(self._student.department)

            if self._answer_all_confirmed:
                if not self._predict_psat.is_answer_official_opened:
                    self._student.is_filtered = True
                    self._student.save()
                    print(f'{self._student} is now filtered as True.')

        # Load student instance after save
        next_url = self.get_next_url_for_answer_input()

        context = update_context_data(header=f'{self._subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(self._request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    @with_bulk_create_or_update()
    def create_confirmed_answers(self, answer_student):
        list_create = []
        for number, answer in enumerate(answer_student, start=1):
            problem = _model.problem.objects.get(psat=self._psat, subject=self._sub, number=number)
            list_create.append(_model.answer(student=self._student, problem=problem, answer=answer))
        return _model.answer, list_create, [], []

    def update_answer_counts_after_confirm(self, answer_student) -> None:
        qs_answer_count = _model.ac_all.objects.predict_filtered_by_psat(self._psat).filter(sub=self._sub)

        count_all, count_filtered = 0, 0
        for qs_ac in qs_answer_count:
            ans_student = answer_student[qs_ac.number - 1]
            setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
            if self._predict_psat.is_answer_official_opened:
                count_all += 1
            else:
                setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
                count_filtered += 1
            qs_ac.save()

        if count_all:
            print(f'{count_all} {_model.ac_all} instances saved.')
        if count_filtered:
            print(f'{count_filtered} {_model.ac_all} instances(filtered) saved.')

    def update_score_of_student(self) -> None:
        target, _ = _model.score.objects.get_or_create(student=self._student)
        correct_count = 0

        qs_answer = _model.answer.objects.filtered_by_psat_student_and_sub(self._student, self._sub)
        for qs_a in qs_answer:
            answer_official_list = [int(digit) for digit in str(qs_a.answer_official)]
            correct_count += 1 if qs_a.answer_student in answer_official_list else 0

        problem_count = self._context['problem_count']
        score_point = correct_count * 100 / problem_count
        setattr(target, self._subject_field, score_point)

        target.save()
        print(f'{target} saved.')

    def update_rank_of_student(self, df, stat_type: str):
        if stat_type == 'total':
            model = _model.rank_total
        else:
            model = _model.rank_category
            df = df[df['category_id'] == self._student.category_id].copy()

        target, _ = model.objects.get_or_create(student=self._student)

        self.update_rank_stats_and_get_participants(df, target)
        if self._student.is_filtered:
            df_filtered = df[df['is_filtered'] == True].copy()
            self.update_rank_stats_and_get_participants(df_filtered, target)

        target.save()
        print(f'{target} saved.')

    def update_rank_stats_and_get_participants(self, df, target):
        df['rank_average'] = df['average'].rank(ascending=False, method='min').astype(int)
        df['rank_subject'] = df[self._subject_field].rank(ascending=False, method='min').astype(int)

        participants = int(df['student_id'].count())
        rank_average = int(df[df['student_id'] == target.student_id]['rank_average'].iloc[0])
        rank_subject = int(df[df['student_id'] == target.student_id]['rank_subject'].iloc[0])

        if target.participants != participants:
            target.participants = participants
        if target.average != rank_average:
            target.average = rank_average
        if getattr(target, self._subject_field) != rank_subject:
            setattr(target, self._subject_field, rank_subject)

    def update_participants_of_statistics(self, department: str) -> None:
        target, _ = _model.statistics.objects.get_or_create(psat=self._psat, department=department)

        # Update participants for each subject [All, Filtered]
        getattr(target, self._subject_field)['participants'] += 1
        if not self._predict_psat.is_answer_official_opened:
            getattr(target, f'filtered_{self._subject_field}')['participants'] += 1

        # Update participants for average [All, Filtered]
        if self._answer_all_confirmed:
            target.average['participants'] += 1
            if not self._predict_psat.is_answer_official_opened:
                target.filtered_average['participants'] += 1

        target.save()

    def get_next_url_for_answer_input(self) -> str:
        qs_answer = (
            _model.answer.objects.filter(student=self._student)
            .values(subject=F('problem__subject'))
            .annotate(answer_count=Count('id'))
            .order_by('subject')
        )
        answer_count_dict = {entry['subject']: entry['answer_count'] for entry in qs_answer}

        for sub, (_, fld, _, _) in self._subject_vars.items():
            if not answer_count_dict.get(sub):
                return self._psat.get_predict_answer_input_url(fld)
        return self._psat.get_predict_detail_url()


@dataclass(kw_only=True)
class StudentAnswerContext:
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']
        self._subject_vars = self._context['subject_vars']
        self._subject_variants = SubjectVariants(_psat=self._context['psat'])

        self.qs_student_answer = _model.answer.objects.filtered_by_psat_student(self._student)
        self.is_confirmed_data = self.get_is_confirmed_data()

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

        time_schedule = self._context['time_schedule']
        predict_psat = self._student.psat.predict_psat

        is_confirmed_for_average = []
        stat_data = {}
        for sub, (subject, fld, _, problem_count) in self._subject_variants.subject_vars_avg.items():
            url_answer_input = self._student.psat.get_predict_answer_input_url(fld) if sub != '평균' else ''
            answer_count = answer_count_dict[sub] if sub != '평균' else sum(answer_count_dict.values())
            participants = 0
            rank = student_score = max_score = top_score_10 = top_score_20 = avg_score = 0

            if sub in participants_dict.keys():
                scores = score_np_dict[fld]
                participants = participants_dict[sub]
                is_confirmed_for_average.append(True)

                if predict_psat.is_answer_predict_opened:
                    pass

                if predict_psat.is_answer_official_opened:
                    student_score = getattr(self._student.score, fld)
                    if scores.any() and student_score:
                        sorted_scores = np.sort(scores)[::-1]
                        rank = int(np.where(sorted_scores == student_score)[0][0] + 1)
                        max_score = to_float(np.max(scores))
                        top_score_10 = to_float(np.percentile(scores, 90))
                        top_score_20 = to_float(np.percentile(scores, 80))
                        avg_score = to_float(np.mean(scores))

            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'start_time': time_schedule[sub][0],
                'end_time': time_schedule[sub][1],

                'participants': participants,
                'is_confirmed': self.is_confirmed_data[sub],
                'url_answer_input': url_answer_input,

                'score_result': student_score,
                'score_predict': 0,
                'problem_count': problem_count,
                'answer_count': answer_count,

                'rank': rank,
                'max': max_score,
                't10': top_score_10,
                't20': top_score_20,
                'avg': avg_score,
            }
        return stat_data

    def get_participants_dict(self, stat_type: str, is_filtered: bool) -> dict[str, int]:
        qs_answer = _model.answer.objects.filtered_by_psat_student_and_stat_type(
            self._student, stat_type, is_filtered)
        participants_dict = {qs_a['problem__subject']: qs_a['participant_count'] for qs_a in qs_answer}
        participants_dict['평균'] = participants_dict[min(participants_dict)] if participants_dict else 0
        return participants_dict

    def get_score_np_dict(self, stat_type: str, is_filtered: bool) -> dict[str, np.array]:
        qs_score = _model.score.objects.predict_filtered_scores_of_student(self._student, stat_type, is_filtered)
        subject_fields_avg = self._subject_variants.subject_fields_avg
        subject_dict = {fld: [] for fld in subject_fields_avg}

        for qs_s in qs_score:
            for fld in subject_fields_avg:
                score = qs_s[fld]
                if score is not None:
                    subject_dict[fld].append(score)

        return {fld: np.array(scores) for fld, scores in subject_dict.items()}

    def get_answer_count_dict(self) -> dict[str, int]:
        total_answer_set = self._context['total_answer_set']
        answer_count_dict = {}
        for sub, (subject, fld, _, problem_count) in self._subject_vars.items():
            answer_list = total_answer_set.get(fld)
            saved_answers = []
            if answer_list:
                saved_answers = [ans for ans in answer_list if ans]
            answer_count_dict[sub] = max(self._student.answer_count.get(sub, 0), len(saved_answers))
        return answer_count_dict


@dataclass(kw_only=True)
class ChartContext:
    _statistics_context: dict
    _student: _model.student | None

    def __post_init__(self):
        self._subject_variants = SubjectVariants(_psat=self._student.psat)

    def get_dict_stat_chart(self) -> dict:
        chart_score = {
            'min_score': 50,
            'all_avg': [], 'all_t20': [], 'all_t10': [], 'all_max': [],
            'dep_avg': [], 'dep_t20': [], 'dep_t10': [], 'dep_max': [],
        }
        if self._student:
            student_score_list = [
                getattr(self._student.score, fld) for fld in self._subject_variants.subject_fields_avg
            ]
            chart_score['my_score'] = student_score_list
            score_list = [score for score in student_score_list if score is not None]
            chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0

        for stat in self._statistics_context['all']['page_obj'].values():
            chart_score['all_avg'].append(stat['avg'])
            chart_score['all_t20'].append(stat['t20'])
            chart_score['all_t10'].append(stat['t10'])
            chart_score['all_max'].append(stat['max'])
        for stat in self._statistics_context['department']['page_obj'].values():
            chart_score['dep_avg'].append(stat['avg'])
            chart_score['dep_t20'].append(stat['t20'])
            chart_score['dep_t10'].append(stat['t10'])
            chart_score['dep_max'].append(stat['max'])

        return chart_score

    def get_dict_stat_frequency(self) -> dict:
        score_frequency_list = _model.student.objects.average_scores_over(self._student.psat, 50)
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
        if self._student and self._student.score.average:  # noqa
            bin_start = int((self._student.score.average // bin_size) * bin_size)  # noqa
            bin_end = bin_start + bin_size
            target_bin = f'{bin_start}~{bin_end}'

        return sorted_freq, target_bin


def to_float(data, decimal=1):
    return round(float(data), decimal)


def get_input_answer_data_set(request: HtmxHttpRequest, subject_vars: dict) -> dict:
    empty_answer_data = {
        fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in subject_vars.items()
    }
    answer_data_set_cookie = request.COOKIES.get('total_answer_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set
