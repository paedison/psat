import json
from collections import defaultdict
from datetime import timedelta

import numpy as np
from django.db.models import Count, F, Window, Q
from django.db.models.functions import Rank

from .admin_utils import bulk_create_or_update
from .. import models


def get_sub_list() -> list:
    return ['언어', '추리']


def get_subject_list() -> list:
    return ['언어이해', '추리논증']


def get_subject_vars() -> dict[str, tuple[str, str, int]]:
    return {
        '언어': ('언어이해', 'subject_0', 0),
        '추리': ('추리논증', 'subject_1', 1),
        '총점': ('총점', 'sum', 2),
    }


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


def get_problem_count(exam):
    if exam == '하프':
        return {'언어': 15, '추리': 20}
    return {'언어': 30, '추리': 40}


def get_answer_tab(leet) -> list:
    problem_count = get_problem_count(leet.exam)
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    answer_tab = []
    for sub, (subject, _, idx) in subject_vars.items():
        loop_list = get_loop_list(problem_count[sub])
        answer_tab.append({'id': str(idx), 'title': subject, 'loop_list': loop_list})
    return answer_tab


def get_loop_list(problem_count):
    loop_list = []
    quotient = problem_count // 10
    counter = [10] * quotient
    remainder = problem_count % 10
    if remainder:
        counter.append(remainder)
    loop_min = 0
    for loop_idx in range(quotient):
        loop_list.append({'counter': counter[loop_idx], 'min': loop_min})
        loop_min += 10
    return loop_list


def get_score_tab(is_filtered=False):
    suffix = 'Filtered' if is_filtered else ''
    return [
        {'id': '0', 'title': '전체', 'prefix': f'total{suffix}'},
        {'id': '1', 'title': '1지망', 'prefix': f'aspiration1{suffix}'},
        {'id': '2', 'title': '2지망', 'prefix': f'aspiration2{suffix}'},
    ]


def get_is_confirmed_data(student) -> list:
    is_confirmed_data = [True if val else False for val in student.answer_count.values()]
    is_confirmed_data.append(all(is_confirmed_data))  # Add is_confirmed_data for '평균'
    return is_confirmed_data


def get_input_answer_data_set(leet, request) -> dict:
    problem_count = get_problem_count(leet.exam)
    subject_vars = get_subject_vars()
    empty_answer_data = {
        subject_vars[sub][1]: [0 for _ in range(cnt)] for sub, cnt in problem_count.items()
    }
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


def get_dict_stat_data_for_result(student: models.ResultStudent, stat_type='total') -> list:
    if stat_type == 'total' or getattr(student, stat_type):
        subject_vars = get_subject_vars()
        stat_data = get_empty_dict_stat_data_for_result(student, subject_vars)

        qs_answer = models.ResultAnswer.objects.prime_leet_qs_answer_by_student_and_stat_type_and_is_filtered(
            student, stat_type)
        qs_score = models.ResultScore.objects.prime_leet_qs_score_by_student_and_stat_type_and_is_filtered(
            student, stat_type)

        participants_dict = {subject_vars[qs_a['problem__subject']][1]: qs_a['participant_count'] for qs_a in qs_answer}
        participants_dict['sum'] = participants_dict[min(participants_dict)] if participants_dict else 0
        update_dict_stat_data(student, qs_score, stat_data, participants_dict)

        return stat_data
    return []


def get_dict_stat_data_for_fake(fake_student: models.ResultStudent, stat_type='total') -> list:
    if stat_type == 'total' or getattr(fake_student, stat_type):
        subject_vars = get_subject_vars()
        stat_data = get_empty_dict_stat_data_for_result(fake_student, subject_vars)

        qs_student = models.FakeStudent.objects.prime_leet_fake_qs_answer_by_student_and_stat_type(
            fake_student, stat_type)
        qs_score = models.FakeScore.objects.prime_leet_qs_score_by_student_and_stat_type_and_is_filtered(
            fake_student, stat_type)

        participants = qs_student.count()
        participants_dict = {subject: participants for _, (_, subject, _) in subject_vars.items()}
        participants_dict['sum'] = participants_dict[min(participants_dict)] if participants_dict else 0
        update_dict_stat_data(fake_student, qs_score, stat_data, participants_dict)

        return stat_data
    return []


def get_dict_stat_data_for_predict(
        student: models.PredictStudent,
        is_confirmed_data: list,
        answer_data_set: dict,
        stat_type='total',
        is_filtered=False,
):
    subject_vars = get_subject_vars()
    stat_data = get_empty_dict_stat_data_for_predict(student, is_confirmed_data, answer_data_set, subject_vars)
    qs_answer = models.PredictAnswer.objects.prime_leet_qs_answer_by_student_and_stat_type_and_is_filtered(
        student, stat_type)
    qs_score = models.PredictScore.objects.prime_leet_qs_score_by_student_and_stat_type_and_is_filtered(
        student, stat_type, is_filtered)

    participants_dict = {subject_vars[qs_a['problem__subject']][1]: qs_a['participant_count'] for qs_a in qs_answer}
    participants_dict['sum'] = participants_dict[min(participants_dict)] if participants_dict else 0
    update_dict_stat_data(student, qs_score, stat_data, participants_dict)

    return stat_data


def update_dict_stat_data(student, qs_score, stat_data: list, participants_dict: dict):
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }
    raw_scores = {fld: [] for fld in field_vars.keys()}
    scores = {fld: [] for fld in field_vars.keys()}
    for stat in stat_data:
        fld = stat['field']
        if fld in participants_dict.keys():
            participants = participants_dict.get(fld, 0)
            stat['participants'] = participants
            if student.leet.is_answer_predict_opened:
                pass
            if student.leet.is_answer_official_opened:
                for qs_s in qs_score:
                    fld_raw_score = qs_s[f'raw_{fld}']
                    if fld_raw_score is not None:
                        raw_scores[fld].append(fld_raw_score)
                    fld_score = qs_s[fld]
                    if fld_score is not None:
                        scores[fld].append(fld_score)

                student_score = getattr(student.score, fld)
                if raw_scores[fld] and scores[fld] and student_score:
                    sorted_raw_scores = sorted(raw_scores[fld], reverse=True)
                    sorted_scores = sorted(scores[fld], reverse=True)
                    raw_score_stddev = round(np.std(np.array(sorted_raw_scores), ddof=1), 1)
                    raw_score_stddev = None if np.isnan(raw_score_stddev) else raw_score_stddev

                    def get_top_score(_sorted_scores, percentage):
                        if _sorted_scores:
                            threshold = max(1, int(participants * percentage))
                            return _sorted_scores[threshold - 1]

                    stat.update({
                        'raw_score': getattr(student.score, f'raw_{fld}'),
                        'score': student_score,
                        'rank': sorted_scores.index(student_score) + 1,
                        'max_raw_score': sorted_raw_scores[0],
                        'top_raw_score_10': get_top_score(sorted_raw_scores, 0.10),
                        'top_raw_score_25': get_top_score(sorted_raw_scores, 0.25),
                        'top_raw_score_50': get_top_score(sorted_raw_scores, 0.50),
                        'raw_score_avg': round(sum(raw_scores[fld]) / participants, 1),
                        'raw_score_stddev': raw_score_stddev,
                        'max_score': sorted_scores[0],
                        'top_score_10': get_top_score(sorted_scores, 0.10),
                        'top_score_25': get_top_score(sorted_scores, 0.25),
                        'top_score_50': get_top_score(sorted_scores, 0.50),
                    })


def get_empty_dict_stat_data_for_result(student, subject_vars: dict) -> list[dict]:
    stat_data = []
    problem_count = get_problem_count(student.leet.exam)
    problem_count['총점'] = sum(val for val in problem_count.values())
    for sub, (subject, fld, fld_idx) in subject_vars.items():
        stat_data.append({
            'field': fld, 'sub': sub, 'subject': subject,
            'participants': 0, 'is_confirmed': True,
            'problem_count': problem_count.get(sub),
            'rank': 0, 'raw_score': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_25': 0, 'top_score_50': 0, 'avg_score': 0,
        })
    return stat_data


def get_empty_dict_stat_data_for_predict(
        student: models.PredictStudent,
        is_confirmed_data: list,
        answer_data_set: dict,
        subject_vars: dict,
) -> list[dict]:
    stat_data = []
    problem_count = get_problem_count(student.leet.exam)
    problem_count['총점'] = sum(val for val in problem_count.values())
    for sub, (subject, fld, fld_idx) in subject_vars.items():
        url_answer_input = student.leet.get_predict_answer_input_url(fld) if sub != '총점' else ''
        answer_list = answer_data_set.get(fld)
        saved_answers = []
        if answer_list:
            saved_answers = [ans for ans in answer_list if ans]
        answer_count = max(student.answer_count.get(fld, 0), len(saved_answers))

        stat_data.append({
            'field': fld, 'sub': sub, 'subject': subject,
            'start_time': get_time_schedule(student.leet)[sub][0],
            'end_time': get_time_schedule(student.leet)[sub][1],

            'participants': 0,
            'is_confirmed': is_confirmed_data[fld_idx],
            'url_answer_input': url_answer_input,

            'score_predict': 0,
            'problem_count': problem_count.get(sub),
            'answer_count': answer_count,

            'rank': 0, 'raw_score': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_25': 0, 'top_score_50': 0, 'avg_score': 0,
        })
    return stat_data


def get_time_schedule(leet):
    start_time = leet.exam_started_at
    exam_1_end_time = start_time + timedelta(minutes=70)  # 1교시 시험 종료 시각
    exam_2_start_time = exam_1_end_time + timedelta(minutes=35)  # 2교시 시험 시작 시각
    exam_2_end_time = exam_2_start_time + timedelta(minutes=125)  # 2교시 시험 종료 시각
    return {
        '언어': (start_time, exam_1_end_time),
        '추리': (exam_2_start_time, exam_2_end_time),
        '총점': (start_time, exam_2_end_time),
    }


def update_score_predict(stat_data_total, qs_student_answer):
    sub_list = get_sub_list()
    score_predict = {sub: 0 for sub in sub_list}
    predict_correct_count_list = qs_student_answer.filter(predict_result=True).values(
        'subject').annotate(correct_counts=Count('predict_result'))
    for entry in predict_correct_count_list:
        sub = entry['subject']
        score = entry['correct_counts']
        score_predict[sub] = score
    score_sum = 0
    for stat in stat_data_total:
        sub = stat['sub']
        if sub != '총점':
            score_sum += score_predict[sub]
            stat['score_predict'] = score_predict[sub]
        else:
            stat['score_predict'] = score_sum


def update_score_real(stat_data_total, qs_student_answer):
    sub_list = get_sub_list()
    score_real = {sub: 0 for sub in sub_list}
    predict_correct_count_list = qs_student_answer.filter(real_result=True).values(
        'subject').annotate(correct_counts=Count('real_result'))
    for entry in predict_correct_count_list:
        sub = entry['subject']
        score = entry['correct_counts']
        score_real[sub] = score
    score_sum = 0
    for stat in stat_data_total:
        sub = stat['sub']
        if sub != '총점':
            score_sum += score_real[sub]
            stat['score_real'] = score_real[sub]
        else:
            stat['score_real'] = score_sum


def get_dict_stat_chart(student, stat_data_total) -> dict:
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }
    return {
        'my_score': [getattr(student.score, fld) for fld in field_vars],
        'total_score_10': [stat['top_score_10'] for stat in stat_data_total],
        'total_score_25': [stat['top_score_25'] for stat in stat_data_total],
        'total_score_50': [stat['top_score_50'] for stat in stat_data_total],
        'total_top': [stat['max_score'] for stat in stat_data_total],
    }


def frequency_table_by_bin(scores, bin_size=10, target_score=None):
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
    if target_score is not None:
        bin_start = int((target_score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        target_bin = f'{bin_start}~{bin_end}'

    return sorted_freq, target_bin


def get_dict_stat_frequency(student, score_frequency_list) -> dict:
    scores = [round(score, 1) for score in score_frequency_list]
    sorted_freq, target_bin = frequency_table_by_bin(scores, target_score=student.score.sum)

    score_label = []
    score_data = []
    score_color = []
    for key, val in sorted_freq.items():
        score_label.append(key)
        score_data.append(val)
        color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
        score_color.append(color)

    return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}


def get_data_answers_for_result(qs_student_answer):
    sub_list = get_sub_list()
    subject_vars = get_subject_vars()
    data_answers = [[] for _ in sub_list]

    for qs_sa in qs_student_answer:
        sub = qs_sa.problem.subject
        subject = qs_sa.problem.get_subject_display()
        idx = sub_list.index(sub)
        field = subject_vars[sub][1]
        ans_official = qs_sa.problem.answer
        ans_student = qs_sa.answer
        answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_sa.no = qs_sa.problem.number
        qs_sa.sub = sub
        qs_sa.subject = subject
        qs_sa.ans_official = ans_official
        qs_sa.ans_official_circle = qs_sa.problem.get_answer_display

        qs_sa.ans_student = ans_student
        qs_sa.ans_list = answer_official_list

        qs_sa.field = field
        qs_sa.result = ans_student in answer_official_list

        qs_sa.rate_correct = qs_sa.problem.result_answer_count.get_answer_rate(ans_official)
        qs_sa.rate_correct_top = qs_sa.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
        qs_sa.rate_correct_mid = qs_sa.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
        qs_sa.rate_correct_low = qs_sa.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            qs_sa.rate_gap = qs_sa.rate_correct_top - qs_sa.rate_correct_low
        except TypeError:
            qs_sa.rate_gap = None

        if ans_student <= 5:
            qs_sa.rate_selection = qs_sa.problem.result_answer_count.get_answer_rate(ans_student)
            qs_sa.rate_selection_top = qs_sa.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_mid = qs_sa.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_low = qs_sa.problem.result_answer_count_low_rank.get_answer_rate(ans_student)

        data_answers[idx].append(qs_sa)
    return data_answers


def get_data_answers_for_predict(qs_student_answer):
    sub_list = get_sub_list()
    subject_vars = get_subject_vars()
    data_answers = [[] for _ in sub_list]

    for qs_sa in qs_student_answer:
        sub = qs_sa.problem.subject
        idx = sub_list.index(sub)
        field = subject_vars[sub][1]
        ans_official = qs_sa.problem.answer
        ans_student = qs_sa.answer
        ans_predict = qs_sa.problem.predict_answer_count.answer_predict

        qs_sa.no = qs_sa.problem.number
        qs_sa.ans_official = ans_official
        qs_sa.ans_official_circle = qs_sa.problem.get_answer_display

        qs_sa.ans_student = ans_student
        qs_sa.field = field

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

        data_answers[idx].append(qs_sa)
    return data_answers


def create_confirmed_answers(student, sub, answer_data):
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(leet=student.leet, subject=sub, number=no)
        list_create.append(models.PredictAnswer(student=student, problem=problem, answer=ans))
    bulk_create_or_update(models.PredictAnswer, list_create, [], [])


def update_answer_counts_after_confirm(leet, sub, answer_data):
    qs_answer_count = models.PredictAnswerCount.objects.prime_leet_qs_answer_count_by_leet(leet).filter(sub=sub)
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
        if not leet.is_answer_official_opened:
            setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
        qs_ac.save()


def update_predict_score_for_student(student, sub: str):
    raw_score_field = f'raw_{get_subject_vars()[sub][1]}'
    qs_student_answer = models.PredictAnswer.objects.prime_leet_qs_answer_by_student_with_predict_result(student)

    if student.leet.is_answer_official_opened:
        correct_count = qs_student_answer.filter(problem__subject=sub, real_result=True).count()
    else:
        correct_count = qs_student_answer.filter(problem__subject=sub, predict_result=True).count()

    setattr(student.score, raw_score_field, correct_count)
    score_list = [sco for sco in [student.score.subject_0, student.score.subject_1] if sco is not None]
    score_raw_sum = sum(score_list) if score_list else None

    student.score.sum = score_raw_sum
    student.score.save()


def update_predict_rank_for_each_student(qs_student, student, subject_field, field_idx, stat_type: str):
    rank_model = models.PredictRank
    if stat_type == 'aspiration_1':
        rank_model = models.PredictRankAspiration1
    elif stat_type == 'aspiration_2':
        rank_model = models.PredictRankAspiration2

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {
        f'rank_{field_idx}': rank_func(f'score__raw_{subject_field}'),
        'rank_sum': rank_func(f'score__raw_sum'),
    }

    rank_list = qs_student.annotate(**annotate_dict)
    if stat_type in ['aspiration_1', 'aspiration_2']:
        aspiration = getattr(student, stat_type)
        rank_list = rank_list.filter(Q(aspiration_1=aspiration) | Q(aspiration_2=aspiration))
    participants = rank_list.count()

    target_rank, _ = rank_model.objects.get_or_create(student=student)
    fields_not_match = [target_rank.participants != participants]

    for entry in rank_list:
        if entry.id == student.id:
            rank_for_field = getattr(entry, f'rank_{field_idx}')
            score_for_sum = getattr(entry, f'rank_sum')
            fields_not_match.append(getattr(target_rank, subject_field) != rank_for_field)
            fields_not_match.append(target_rank.sum != entry.rank_sum)

            if any(fields_not_match):
                target_rank.participants = participants
                setattr(target_rank, subject_field, rank_for_field)
                setattr(target_rank, 'sum', score_for_sum)
                target_rank.save()


def get_answer_all_confirmed(student) -> bool:
    answer_student_counts = models.PredictAnswer.objects.filter(student=student).count()
    problem_count = get_problem_count(student.leet.exam)
    return answer_student_counts == sum(problem_count.values())


def update_statistics_after_confirm(student, subject_field, answer_all_confirmed):
    qs_statistics = models.PredictStatistics.objects.filter(leet=student.leet)

    def get_statistics_and_edit_participants(aspiration: str):
        if aspiration:
            stat = qs_statistics.filter(aspiration=aspiration)

            # Update participants for each subject [All, Filtered]
            getattr(stat, subject_field)['participants'] += 1
            getattr(stat, f'raw_{subject_field}')['participants'] += 1
            if not student.leet.is_answer_official_opened:
                getattr(stat, f'filtered_{subject_field}')['participants'] += 1
                getattr(stat, f'filtered_raw_{subject_field}')['participants'] += 1

            # Update participants for average [All, Filtered]
            if answer_all_confirmed:
                stat.sum['participants'] += 1
                stat.raw_sum['participants'] += 1
                if not student.leet.is_answer_official_opened:
                    stat.filtered_sum['participants'] += 1
                    stat.filtered_raw_sum['participants'] += 1
                    student.is_filtered = True
                    student.save()
            stat.save()

    get_statistics_and_edit_participants('전체')
    get_statistics_and_edit_participants(student.aspiration_1)
    get_statistics_and_edit_participants(student.aspiration_2)


def get_next_url_for_answer_input(student):
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    for _, (_, subject_field, _) in subject_vars.items():
        if student.answer_count[subject_field] == 0:
            return student.leet.get_predict_answer_input_url(subject_field)
    return student.leet.get_predict_detail_url()
