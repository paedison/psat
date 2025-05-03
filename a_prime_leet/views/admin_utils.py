import io
import traceback
import zipfile
from collections import defaultdict
from urllib.parse import quote

import django.db.utils
import numpy as np
import pandas as pd
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Count, F, Avg, StdDev, Q
from django.http import HttpResponse
from scipy.stats import rankdata

from .. import models, utils


def get_sub_list() -> list:
    return ['언어', '추리']


def get_subject_list() -> list:
    return ['언어이해', '추리논증']


def get_answer_tab() -> list:
    return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(get_subject_list())]


def get_subject_vars() -> dict[str, tuple[str, str, int]]:
    return {
        '언어': ('언어이해', 'subject_0', 0),
        '추리': ('추리논증', 'subject_1', 1),
        '총점': ('총점', 'sum', 2),
    }


def get_problem_count_dict(exam):
    if exam == '하프':
        return {'언어': 15, '추리': 20}
    return {'언어': 30, '추리': 40}


def get_field_vars(is_filtered=False) -> dict[str, tuple[str, str, int]]:
    if is_filtered:
        return {
            'filtered_subject_0': ('[필터링]언어', '[필터링]언어이해', 0),
            'filtered_subject_1': ('[필터링]추리', '[필터링]추리논증', 1),
            'filtered_sum': ('[필터링]총점', '[필터링]총점', 2),
            'filtered_raw_subject_0': ('[필터링]언어', '[필터링]언어이해', 0),
            'filtered_raw_subject_1': ('[필터링]추리', '[필터링]추리논증', 1),
            'filtered_raw_sum': ('[필터링]총점', '[필터링]총점', 2),
        }
    return {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
        'raw_subject_0': ('언어', '언어이해', 0),
        'raw_subject_1': ('추리', '추리논증', 1),
        'raw_sum': ('총점', '총점', 2),
    }


def get_total_field_vars() -> dict[str, tuple[str, str, int]]:
    return {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
        'raw_subject_0': ('언어', '언어이해', 0),
        'raw_subject_1': ('추리', '추리논증', 1),
        'raw_sum': ('총점', '총점', 2),
        'filtered_subject_0': ('[필터링]언어', '[필터링]언어이해', 0),
        'filtered_subject_1': ('[필터링]추리', '[필터링]추리논증', 1),
        'filtered_sum': ('[필터링]총점', '[필터링]총점', 2),
        'filtered_raw_subject_0': ('[필터링]언어', '[필터링]언어이해', 0),
        'filtered_raw_subject_1': ('[필터링]추리', '[필터링]추리논증', 1),
        'filtered_raw_sum': ('[필터링]총점', '[필터링]총점', 2),
    }


def get_target_model(model_name: str):
    try:
        return apps.get_model('a_prime_leet', model_name)
    except LookupError:
        raise ImproperlyConfigured(f'{model_name} 모델을 찾을 수 없습니다.')


def get_qs_statistics(leet, model_type='result'):
    model = get_target_model(f'{model_type.capitalize()}Statistics')
    return model.objects.filter(leet=leet).order_by('id')


def get_student_list(leet, model_type='result'):
    model = get_target_model(f'{model_type.capitalize()}Student')
    return model.objects.prime_leet_qs_student_list_by_leet(leet)


def get_qs_answer_count(leet, model_type='result', subject=None):
    model = get_target_model(f'{model_type.capitalize()}AnswerCount')
    return model.objects.prime_leet_qs_answer_count_by_leet_and_model_type_and_subject(leet, model_type, subject)


def get_dict_stat_chart(data_total):
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }
    stat_chart = defaultdict(list)
    for fld in field_vars:
        stat_chart['total_score_10'].append(getattr(data_total, fld)['t10'])
        stat_chart['total_score_25'].append(getattr(data_total, fld)['t25'])
        stat_chart['total_score_50'].append(getattr(data_total, fld)['t50'])
        stat_chart['total_top'].append(getattr(data_total, fld)['max'])
    return stat_chart


def frequency_table_by_bin(scores, bin_size=10):
    freq = defaultdict(int)
    for score in scores:
        bin_start = int((score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        bin_label = f'{bin_start}~{bin_end}'
        freq[bin_label] += 1
    sorted_freq = dict(sorted(freq.items(), key=lambda x: int(x[0].split('~')[0])))
    return sorted_freq


def get_dict_stat_frequency(score_frequency_list) -> dict:
    scores = [round(score, 1) for score in score_frequency_list if score is not None]
    sorted_freq = frequency_table_by_bin(scores)

    score_label, score_data, score_color = [], [], []
    for key, val in sorted_freq.items():
        score_label.append(key)
        score_data.append(val)
        color = 'rgba(54, 162, 235, 0.5)'
        score_color.append(color)

    return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}


def get_answer_page_data(qs_answer_count, page_number, model_type='result', per_page=10):
    subject_vars = get_subject_vars()
    qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

    for entry in qs_answer_count:
        if entry.subject not in qs_answer_count_group:
            qs_answer_count_group[entry.subject] = []
        qs_answer_count_group[entry.subject].append(entry)

    for subject, qs_answer_count in qs_answer_count_group.items():
        if subject not in answers_page_obj_group:
            answers_page_obj_group[subject] = []
            answers_page_range_group[subject] = []
        data_answers = get_data_answers(qs_answer_count, subject_vars, model_type)
        answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
            data_answers, page_number, per_page)

    return answers_page_obj_group, answers_page_range_group


def get_data_answers(qs_answer_count, subject_vars, model_type='result'):
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        field = subject_vars[sub][1]
        ans_official = qs_ac.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_ac.no = qs_ac.number
        qs_ac.ans_official = ans_official
        qs_ac.ans_official_circle = qs_ac.problem.get_answer_display
        qs_ac.ans_predict_circle = models.choices.answer_choice().get(qs_ac.ans_predict)
        qs_ac.ans_list = answer_official_list
        qs_ac.field = field

        if model_type == 'result':
            qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
            qs_ac.rate_correct_top = qs_ac.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_mid = qs_ac.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_low = qs_ac.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
        else:
            qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
            qs_ac.rate_correct_top = qs_ac.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_mid = qs_ac.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_low = qs_ac.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
        except TypeError:
            qs_ac.rate_gap = None

    return qs_answer_count


def get_qs_student(leet, model_type='result'):
    model = get_target_model(f'{model_type.capitalize()}Student')
    return model.objects.filter(leet=leet).order_by('id')


def update_problem_model_for_answer_official(leet, form, file) -> tuple:
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문제 정답을 업데이트했습니다.',
        False: '기존 정답 데이터와 일치합니다.',
    }
    list_create, list_update = [], []
    model = models.Problem
    qs_problem = model.objects.filter(leet=leet).order_by('subject', 'number')
    qs_problem_dict = {(qs_p.subject, qs_p.number): qs_p for qs_p in qs_problem}

    if form.is_valid():
        df = pd.read_excel(file, header=0, index_col=0)
        df = df.infer_objects(copy=False)
        df.fillna(value=0, inplace=True)

        for subject, rows in df.items():
            for number, answer in rows.items():
                if answer:
                    sub = subject[:2]
                    problem = qs_problem_dict.get((sub, number))
                    if problem and problem.answer != answer:
                        problem.answer = answer
                        list_update.append(problem)
                    if problem is None:
                        list_create.append(model(leet=leet, subject=sub, number=number, answer=answer))
                    else:
                        if problem.answer != answer:
                            problem.answer = answer
                            list_update.append(problem)
        is_updated = bulk_create_or_update(model, list_create, list_update, ['answer'])
    else:
        is_updated = None
        print(form)
    return is_updated, message_dict[is_updated]


def update_answer_student(leet, form, file, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '제출 답안을 업데이트했습니다.',
        False: '기존 정답 데이터와 일치합니다.',
    }

    if form.is_valid():
        is_updated_list = [update_answer_model(leet, file, model_type)]
    else:
        is_updated_list = [None]
        print(form)

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_answer_model(leet, file, model_type='result'):
    student_model = get_target_model(f'{model_type.capitalize()}Student')
    answer_model = get_target_model(f'{model_type.capitalize()}Answer')

    qs_problem = models.Problem.objects.prime_leet_qs_problem_by_leet(leet)
    qs_problem_dict = {(qs_p.subject, qs_p.number): qs_p for qs_p in qs_problem}

    qs_student = student_model.objects.filter(leet=leet)
    qs_student_dict = {qs_s.serial: qs_s for qs_s in qs_student}

    qs_answer = answer_model.objects.prime_leet_qs_answer_by_student_with_sub_number(student)
    qs_answer_dict = {(qs_a.sub, qs_a.number): qs_a for qs_a in qs_answer}

    label_name = ('성명', 'Unnamed: 1_level_1')
    label_password = ('비밀번호', 'Unnamed: 2_level_1')
    label_school = ('출신대학', 'Unnamed: 3_level_1')
    label_major = ('전공', 'Unnamed: 4_level_1')
    label_aspiration_1 = ('1지망', 'Unnamed: 5_level_1')
    label_aspiration_2 = ('2지망', 'Unnamed: 6_level_1')
    label_gpa_type = ('학점 (GPA)', '만점')
    label_gpa = ('학점 (GPA)', '학점')
    label_english_type = ('공인영어성적', '종류')
    label_english = ('공인영어성적', '성적')

    df = pd.read_excel(file, sheet_name='마킹데이터', header=[0, 1], index_col=0, dtype={label_password: str})
    df = df.infer_objects(copy=False)
    df.fillna(
        value={
            label_name: '', label_password: '0000',
            label_school: '', label_major: '',
            label_aspiration_1: '', label_aspiration_2: '',
            label_gpa_type: np.nan, label_gpa: np.nan,
            label_english_type: '', label_english: np.nan,
        },
        inplace=True
    )

    def clean_value(val):
        if pd.isna(val):
            return None
        elif val == ' .':
            return None
        return val

    is_updated_list = []
    for serial, row in df.iterrows():
        list_update = []
        list_create = []
        student_info = {
            'name': row[label_name], 'password': row[label_password],
            'school': row[label_school], 'major': row[label_major],
            'aspiration_1': row[label_aspiration_1], 'aspiration_2': row[label_aspiration_2],
            'gpa_type': clean_value(row[label_gpa_type]),
            'gpa': clean_value(row[label_gpa]),
            'english_type': clean_value(row[label_english_type]),
            'english': clean_value(row[label_english]),
        }

        student = qs_student_dict.get(str(serial))
        if student is None:
            student = student_model.objects.create(leet=leet, serial=serial, **student_info)
        else:
            fields_not_match = any(str(getattr(student, fld)) != val for fld, val in student_info.items())
            if fields_not_match:
                for fld, val in student_info.items():
                    setattr(student, fld, val)
                student.save()

        subject_vars = get_subject_vars()
        subject_vars.pop('총점')
        for sub, (subject, _, _) in subject_vars.items():
            problem_count = get_problem_count_dict(student.leet.exam)[sub]
            for number in range(1, problem_count + 1):
                answer = row[(subject, number)] if not np.isnan(row[(subject, number)]) else 0
                student_answer = qs_answer_dict.get((sub, number))
                if student_answer and student_answer.answer != answer:
                    student_answer.answer = answer
                    list_update.append(student_answer)
                if student_answer is None:
                    problem = qs_problem_dict.get((sub, number))
                    list_create.append(answer_model(student=student, problem=problem, answer=answer))
        update_fields = ['answer']
        is_updated_list.append(bulk_create_or_update(answer_model, list_create, list_update, update_fields))
    return is_updated_list


def update_raw_scores(qs_student, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = [update_score_model_for_raw_score(qs_student, model_type)]

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_score_model_for_raw_score(qs_student, model_type='result'):
    answer_model = get_target_model(f'{model_type.capitalize()}Answer')
    score_model = get_target_model(f'{model_type.capitalize()}Score')
    sub_list = get_sub_list()

    list_create, list_update = [], []

    qs_student = qs_student.exclude(serial__startswith='dummy')
    for qs_s in qs_student:
        original_score_instance, _ = score_model.objects.get_or_create(student=qs_s)

        score_list = []
        fields_not_match = []
        for idx, sub in enumerate(sub_list):
            qs_answer = (
                answer_model.objects.filter(student=qs_s, problem__subject=sub)
                .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
            )
            if qs_answer:
                correct_count = 0
                for qs_a in qs_answer:
                    answer_correct_list = [int(digit) for digit in str(qs_a.answer_correct)]
                    correct_count += 1 if qs_a.answer_student in answer_correct_list else 0
                score_list.append(correct_count)
                fields_not_match.append(getattr(original_score_instance, f'raw_subject_{idx}') != correct_count)

        score_raw_sum = sum(score_list)
        fields_not_match.append(original_score_instance.raw_sum != score_raw_sum)

        if any(fields_not_match):
            for idx, score in enumerate(score_list):
                setattr(original_score_instance, f'raw_subject_{idx}', score)
            original_score_instance.raw_sum = score_raw_sum
            list_update.append(original_score_instance)

    update_fields = ['raw_subject_0', 'raw_subject_1', 'raw_sum']
    return bulk_create_or_update(score_model, list_create, list_update, update_fields)


def update_scores(leet, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = [update_score_model_for_score(leet, model_type)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_score_model_for_score(leet, model_type='result'):
    list_create, list_update = [], []

    score_model = get_target_model(f'{model_type.capitalize()}Score')
    subject_fields = {
        0: ('raw_subject_0', 'subject_0', 45, 9),
        1: ('raw_subject_1', 'subject_1', 60, 9),
    }

    original = score_model.objects.filter(student__leet=leet)
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
    return bulk_create_or_update(score_model, list_create, list_update, update_fields)


def update_ranks(leet, qs_student, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '등수를 업데이트했습니다.',
        False: '기존 등수와 일치합니다.',
    }

    is_updated_list = [
        update_rank_model(leet, qs_student, model_type, ''),
        update_rank_model(leet, qs_student, model_type, 'Aspiration1'),
        update_rank_model(leet, qs_student, model_type, 'Aspiration2'),
    ]
    if model_type != 'result':
        is_updated_list.extend([
            update_rank_model(leet, qs_student, model_type, '', True),
            update_rank_model(leet, qs_student, model_type, 'Aspiration1', True),
            update_rank_model(leet, qs_student, model_type, 'Aspiration2', True),
        ])

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def get_data_dict_for_rank(qs_student, subject_fields: list, is_filtered=False) -> dict[str: np.array]:
    """
    score_dict = {
        'total': {
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
        for field in subject_fields:
            if field not in score_dict[aspiration]:
                score_dict[aspiration][field] = []
            score_dict[aspiration][field].append(getattr(instance, field))

    if is_filtered:
        qs_student = qs_student.filter(is_filtered=is_filtered)

    for qs_s in qs_student:
        update_score_dict(qs_s.score, 'total')
        if qs_s.aspiration_1:
            update_score_dict(qs_s.score, qs_s.aspiration_1)
        if qs_s.aspiration_2:
            update_score_dict(qs_s.score, qs_s.aspiration_2)

    data_dict = defaultdict(dict)
    for key, value in score_dict.items():
        for fld, score_list in value.items():
            data_dict[key][fld] = np.array(score_list)

    return data_dict


def update_rank_model(leet, qs_student, model_type='result', stat_type='', is_filtered=False):
    list_create, list_update = [], []
    subject_fields = [f'subject_{idx}' for idx in range(len(get_sub_list()))] + ['sum']

    rank_model = get_target_model(f'{model_type.capitalize()}Rank{stat_type.capitalize()}')
    qs_rank = rank_model.objects.filter(student__leet=leet)
    qs_rank_dict = {qs_r.student: qs_r for qs_r in qs_rank}

    data_dict = get_data_dict_for_rank(qs_student, subject_fields, is_filtered)
    for i, qs_s in enumerate(qs_student):
        data = []
        if stat_type == '':
            data = data_dict['total']
        if stat_type == 'Aspiration1' and qs_s.aspiration_1:
            data = data_dict[qs_s.aspiration_1]
        if stat_type == 'Aspiration2' and qs_s.aspiration_2:
            data = data_dict[qs_s.aspiration_2]

        rank_obj_exists = True
        rank_obj = qs_rank_dict.get(qs_s)
        if rank_obj is None:
            rank_obj_exists = False
            rank_obj = rank_model(student=qs_s)

        def set_rank_obj_field(target_list):
            ranks = {fld: rankdata(-data[fld], method='min') for fld in subject_fields}  # 높은 점수가 1등
            participants = len(data)

            for fld in subject_fields:
                score = getattr(qs_s.score, fld)
                idx = np.where(data[fld] == score)[0][0]
                new_rank = int(ranks[fld][idx])
                if hasattr(rank_obj, fld):
                    if getattr(rank_obj, fld) != new_rank:
                        setattr(rank_obj, fld, new_rank)
                        rank_obj.participants = participants
                        target_list.append(rank_obj)

        def set_rank_obj_field_to_null(target_list):
            for fld in subject_fields:
                if hasattr(rank_obj, fld):
                    if getattr(rank_obj, fld) is not None:
                        setattr(rank_obj, fld, None)
                        rank_obj.participants = None
                        target_list.append(rank_obj)

        if data:
            if rank_obj_exists:
                set_rank_obj_field(list_update)
            else:
                set_rank_obj_field(list_create)
        else:
            if rank_obj_exists:
                set_rank_obj_field_to_null(list_update)
            else:
                set_rank_obj_field_to_null(list_create)

    return bulk_create_or_update(rank_model, list_create, list_update, subject_fields)


def get_data_statistics(leet, model_type='result'):
    field_vars = get_field_vars()
    student_model = get_target_model(f'{model_type.capitalize()}Student')

    aspirations = models.choices.get_aspirations()
    data_statistics = []
    score_list = {}
    filtered_data_statistics = []
    filtered_score_list = {}
    for aspiration in aspirations:
        data_statistics.append({'aspiration': aspiration, 'participants': 0})
        score_list[aspiration] = {fld: [] for fld in field_vars}
        if model_type != 'result':
            filtered_data_statistics.append({'aspiration': aspiration, 'participants': 0})
            filtered_score_list[aspiration] = {fld: [] for fld in field_vars}

    qs_students = (
        student_model.objects.filter(leet=leet)
        .select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2')
        .annotate(
            raw_subject_0=F('score__raw_subject_0'),
            raw_subject_1=F('score__raw_subject_1'),
            raw_sum=F('score__raw_sum'),
            subject_0=F('score__subject_0'),
            subject_1=F('score__subject_1'),
            sum=F('score__sum'),
        )
    )
    for qs_s in qs_students:
        for fld in field_vars:
            score = getattr(qs_s, fld)
            if score is not None:
                score_list['전체'][fld].append(score)
                if qs_s.aspiration_1:
                    score_list[qs_s.aspiration_1][fld].append(score)
                if qs_s.aspiration_2:
                    score_list[qs_s.aspiration_2][fld].append(score)
                if model_type != 'result':
                    filtered_score_list['전체'][fld].append(score)
                    if qs_s.aspiration_1:
                        filtered_score_list[qs_s.aspiration_1][fld].append(score)
                    if qs_s.aspiration_2:
                        filtered_score_list[qs_s.aspiration_2][fld].append(score)

    update_data_statistics(data_statistics, score_list, field_vars, aspirations)
    update_data_statistics(filtered_data_statistics, filtered_score_list, field_vars, aspirations)
    return data_statistics, filtered_data_statistics


def update_data_statistics(data_statistics, score_list, field_vars, aspirations):
    for aspiration, score_dict in score_list.items():
        aspiration_idx = aspirations.index(aspiration)
        for fld, scores in score_dict.items():
            sub = field_vars[fld][0]
            subject = field_vars[fld][1]
            participants = len(scores)
            sorted_scores = sorted(scores, reverse=True)

            def get_top_score(percentage):
                if sorted_scores:
                    threshold = max(1, int(participants * percentage))
                    return sorted_scores[threshold - 1]

            data_statistics[aspiration_idx][fld] = {
                'field': fld,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'participants': participants,
                'max': sorted_scores[0] if sorted_scores else None,
                't10': get_top_score(0.10),
                't25': get_top_score(0.25),
                't50': get_top_score(0.50),
                'avg': round(sum(scores) / participants, 1) if sorted_scores else None,
            }


def update_statistics(leet, data_statistics, filtered_data_statistics, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    is_updated_list = [update_statistics_model(leet, data_statistics, model_type)]
    if model_type != 'result':
        is_updated_list.append([
            update_statistics_model(leet, filtered_data_statistics, model_type, True)
        ])
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_statistics_model(leet, data_statistics, model_type='result', is_filtered=False):
    model = get_target_model(f'{model_type.capitalize()}Statistics')

    field_vars = get_field_vars()
    prefix = 'filtered_' if is_filtered else ''

    list_update = []
    list_create = []

    for data_stat in data_statistics:
        aspiration = data_stat['aspiration']
        stat_dict = {'aspiration': aspiration}
        for fld in field_vars:
            stat_dict.update({
                fld: {
                    'participants': data_stat[fld]['participants'],
                    'max': data_stat[fld]['max'],
                    't10': data_stat[fld]['t10'],
                    't25': data_stat[fld]['t25'],
                    't50': data_stat[fld]['t50'],
                    'avg': data_stat[fld]['avg'],
                }
            })

        try:
            new_query = model.objects.get(leet=leet, aspiration=aspiration)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in stat_dict.items())
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except model.DoesNotExist:
            list_create.append(model(leet=leet, **stat_dict))
    update_fields = ['aspiration']
    update_fields.extend([f'{prefix}{key}' for key in field_vars])
    return bulk_create_or_update(model, list_create, list_update, update_fields)


def update_answer_counts(model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문항 분석표를 업데이트했습니다.',
        False: '기존 문항 분석표와 일치합니다.',
    }
    is_updated_list = [
        update_answer_count_model(model_type, ''),
        update_answer_count_model(model_type, 'TopRank'),
        update_answer_count_model(model_type, 'MidRank'),
        update_answer_count_model(model_type, 'LowRank'),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_answer_count_model(model_type='result', rank_type='', is_filtered=False):
    answer_model = get_target_model(f'{model_type.capitalize()}Answer')
    answer_count_model = get_target_model(f'{model_type.capitalize()}AnswerCount{rank_type.capitalize()}')
    prefix = 'filtered_' if is_filtered else ''

    list_update = []
    list_create = []

    lookup_field = f'student__rank__{prefix}sum'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants_function = F(f'student__rank__{prefix}participants')

    lookup_exp = {}
    if rank_type == 'TopRank':
        lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
    elif rank_type == 'MidRank':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
    elif rank_type == 'LowRank':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

    answer_distribution = (
        answer_model.objects.filter(**lookup_exp)
        .select_related('student', 'student__rank')
        .values('problem_id', 'answer')
        .annotate(count=Count('id')).order_by('problem_id', 'answer')
    )
    organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

    for entry in answer_distribution:
        problem_id = entry['problem_id']
        answer = entry['answer']
        count = entry['count']
        organized_distribution[problem_id][answer] = count

    count_fields = [
        'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
    ]
    for problem_id, answers_original in organized_distribution.items():
        answers = {'count_multiple': 0}
        for answer, count in answers_original.items():
            if answer <= 5:
                answers[f'count_{answer}'] = count
            else:
                answers['count_multiple'] = count
        answers['count_sum'] = sum(answers[fld] for fld in count_fields)

        try:
            new_query = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in answers.items())
            if fields_not_match:
                for fld, val in answers.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except answer_count_model.DoesNotExist:
            list_create.append(answer_count_model(problem_id=problem_id, **answers))
    update_fields = [
        'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_multiple', 'count_sum',
    ]
    return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def update_dummy_data(leet, form, file, model_type='result'):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '더미 데이터를 업데이트했습니다.',
        False: '기존 더미 데이터와 일치합니다.',
    }

    if form.is_valid():
        is_updated_list = update_student_and_score_model_for_dummy_data(leet, file, model_type)
    else:
        is_updated_list = [None]
        print(form)

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_student_and_score_model_for_dummy_data(leet, file, model_type='result'):
    student_model = get_target_model(f'{model_type.capitalize()}Student')
    score_model = get_target_model(f'{model_type.capitalize()}Score')

    df = pd.read_excel(file, sheet_name='score', header=[0, 1], index_col=0)

    qs_student = student_model.objects.filter(leet=leet)
    qs_student_dict = {(qs_s.serial, qs_s.name): qs_s for qs_s in qs_student}

    qs_score = score_model.objects.filter(student__leet=leet)
    qs_score_dict = {qs_s.student: qs_s for qs_s in qs_score}

    list_update_student, list_update_score = [], []
    for serial, row in df.iterrows():
        password = row[('student', 'password')]
        aspiration_1 = row[('student', 'aspiration_1')]
        aspiration_2 = row[('student', 'aspiration_2')]
        student_dict = {
            'password': password,
            'aspiration_1': aspiration_1,
            'aspiration_2': aspiration_2,
        }
        score_dict = {
            'raw_subject_0': row[('correct_count', 'subject_0')],
            'raw_subject_1': row[('correct_count', 'subject_1')],
            'raw_sum': row[('correct_count', 'total')],
            'subject_0': row[('standard_score', 'subject_0')],
            'subject_1': row[('standard_score', 'subject_1')],
            'sum': row[('standard_score', 'total')],
        }

        def _update_list(lst, instance, data):
            fields_not_match = []
            for key, val in data.items():
                fields_not_match.append(getattr(instance, key) != val)
            if any(fields_not_match):
                for key, val in data.items():
                    setattr(instance, key, val)
                lst.append(instance)

        student = qs_student_dict.get((serial, serial))
        if student is None:
            student = student_model.objects.create(
                leet=leet, serial=serial, name=serial, password=password,
                aspiration_1=aspiration_1, aspiration_2=aspiration_2,
            )
        else:
            _update_list(list_update_student, student, student_dict)

        score_instance = qs_score_dict.get(student)
        if score_instance is None:
            score_instance = score_model.objects.create(student=student)

        _update_list(list_update_score, score_instance, score_dict)

    update_fields_student = ['password', 'aspiration_1', 'aspiration_2']
    update_fields_score = ['raw_subject_0', 'raw_subject_1', 'raw_sum', 'subject_0', 'subject_1', 'sum']
    return [
        bulk_create_or_update(student_model, [], list_update_student, update_fields_student),
        bulk_create_or_update(score_model, [], list_update_score, update_fields_score)
    ]


def create_default_problems(leet):
    sub_list = get_sub_list()
    problem_count_dict = get_problem_count_dict(leet.exam)
    list_create = []
    for subject in sub_list:
        problem_count = problem_count_dict[subject]
        for number in range(1, problem_count + 1):
            problem_info = {'leet': leet, 'subject': subject, 'number': number}
            try:
                models.Problem.objects.get(**problem_info)
            except models.Problem.DoesNotExist:
                list_create.append(models.Problem(**problem_info))
    bulk_create_or_update(models.Problem, list_create, [], [])


def create_default_statistics(leet, model_type='result'):
    model = get_target_model(f'{model_type.capitalize()}Statistics')
    aspirations = models.choices.get_aspirations()
    list_create = []
    if model:
        for aspiration in aspirations:
            try:
                model.objects.get(leet=leet, aspiration=aspiration)
            except model.DoesNotExist:
                list_create.append(model(leet=leet, aspiration=aspiration))
    bulk_create_or_update(model, list_create, [], [])


def create_default_answer_counts(problems, model_type='result'):
    model_list = [
        get_target_model(f'{model_type.capitalize()}AnswerCount'),
        get_target_model(f'{model_type.capitalize()}AnswerCountTopRank'),
        get_target_model(f'{model_type.capitalize()}AnswerCountMidRank'),
        get_target_model(f'{model_type.capitalize()}AnswerCountLowRank'),
    ]
    for model in model_list:
        list_create = []
        if model:
            for problem in problems:
                try:
                    model.objects.get(problem=problem)
                except model.DoesNotExist:
                    list_create.append(model(problem=problem))
        bulk_create_or_update(model, list_create, [], [])


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated


def get_statistics_response(leet, model_type='result'):
    qs_statistics = get_qs_statistics(leet, model_type)
    df = pd.DataFrame.from_records(qs_statistics.values())

    filename = f'{leet.name}_성적통계.xlsx'
    drop_columns = ['id', 'leet_id']
    column_label = [('지망 대학', '')]
    is_filtered = False if model_type == 'result' else True
    field_vars = get_field_vars(is_filtered)

    for fld, (_, subject, _) in field_vars.items():
        drop_columns.append(fld)
        subject += ' (원점수)' if fld[:3] == 'raw' else ' (표준점수)'
        column_label.extend([
            (subject, '총 인원'), (subject, '최고'),
            (subject, '상위10%'), (subject, '상위25%'),
            (subject, '상위50%'), (subject, '평균'),
        ])
        df_subject = pd.json_normalize(df[fld])
        df = pd.concat([df, df_subject], axis=1)

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


def get_catalog_response(leet, model_type='result'):
    student_list = get_student_list(leet, model_type)
    df1, filename1 = get_catalog_dataframe_and_file_name(student_list, leet, model_type)

    df2, filename2 = None, None
    if model_type != 'result':
        filtered_student_list = student_list.filter(is_filtered=True)
        df2, filename2 = get_catalog_dataframe_and_file_name(filtered_student_list, leet, model_type, True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        excel_buffer1 = io.BytesIO()
        df1.to_excel(excel_buffer1, engine='xlsxwriter')
        zip_file.writestr(filename1, excel_buffer1.getvalue())

        if df2 and filename2:
            excel_buffer2 = io.BytesIO()
            df2.to_excel(excel_buffer2, engine='xlsxwriter')
            zip_file.writestr(filename2, excel_buffer2.getvalue())

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="catalog_files.zip"'
    return response


def get_catalog_dataframe_and_file_name(student_list, leet, model_type='result', is_filtered=False):
    filtered_type = '필터링' if is_filtered else '전체'
    filename = f'{leet.name}_성적일람표_{filtered_type}.xlsx'
    field_list = ['aspiration_1', 'aspiration_2']

    df = pd.DataFrame.from_records(student_list.values())
    if is_filtered:
        df['rank_sum'] = df['filtered_rank_sum']
        df['rank_0'] = df['filtered_rank_0']
        df['rank_1'] = df['filtered_rank_1']
        for fld in field_list:
            df[f'rank_sum_{fld}'] = df[f'filtered_rank_sum_{fld}']
            df[f'rank_0_{fld}'] = df[f'filtered_rank_0_{fld}']
            df[f'rank_1_{fld}'] = df[f'filtered_rank_1_{fld}']

    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    drop_columns = []
    if model_type != 'result':
        drop_columns.extend(['filtered_rank_num', 'filtered_rank_aspiration_1', 'filtered_rank_aspiration_2'])
        for fld in field_list:
            drop_columns.extend([f'filtered_rank_sum_{fld}', f'filtered_rank_0_{fld}', f'filtered_rank_1_{fld}'])

    column_label = [
        ('ID', ''), ('등록일시', ''), ('수험번호', ''), ('이름', ''), ('비밀번호', ''), ('1지망', ''), ('2지망', ''),
        ('출신대학', ''), ('전공', ''), ('학점 종류', ''), ('학점', ''), ('영어 종류', ''), ('영어 성적', ''),
        ('LEET ID', ''), ('최종답안 등록일시', ''), ('제출 답안수', ''),
        ('참여자 수', '전체'), ('참여자 수', '1지망'), ('참여자 수', '2지망'),
    ]
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }
    for _, (_, subject, _) in field_vars.items():
        column_label.extend([
            (subject, '원점수'),
            (subject, '표준점수'),
            (subject, '전체 등수'),
            (subject, '1지망 등수'),
            (subject, '2지망 등수'),
        ])

    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)
    df.reset_index(inplace=True)

    return df, filename


def get_answer_response(leet, model_type='result'):
    qs_answer_count = get_qs_answer_count(leet, model_type)
    df = pd.DataFrame.from_records(qs_answer_count.values())

    def move_column(col_name: str, loc: int):
        col = df.pop(col_name)
        df.insert(loc, col_name, col)

    move_column('problem_id', 1)
    move_column('subject', 2)
    move_column('number', 3)
    move_column('ans_official', 4)
    move_column('ans_predict', 5)

    filename = f'{leet.name}_문항분석표.xlsx'
    drop_columns = [
        'answer_predict',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0', 'count_multiple', 'count_sum',
    ]
    if model_type != 'result':
        drop_columns.extend([
            'filtered_count_1', 'filtered_count_2', 'filtered_count_3', 'filtered_count_4',
            'filtered_count_5', 'filtered_count_0', 'filtered_count_multiple', 'filtered_count_sum',
        ])

    column_label = [
        ('ID', '', ''), ('문제 ID', '', ''), ('과목', '', ''),
        ('번호', '', ''), ('정답', '', ''), ('예상 정답', '', ''),
    ]
    top_field = ['전체 데이터'] if model_type == 'result' else ['전체 데이터', '필터링 데이터']
    for top in top_field:
        for mid in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (top, mid, '①'), (top, mid, '②'), (top, mid, '③'),
                (top, mid, '④'), (top, mid, '⑤'), (top, mid, '합계'),
            ])

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


def get_response_for_excel_file(df, drop_columns, column_label, filename):
    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)
    df.reset_index(inplace=True)

    excel_data = io.BytesIO()
    df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
