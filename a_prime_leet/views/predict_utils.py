import json
from collections import Counter
from datetime import timedelta

from django.db.models import Count

from .. import models


def get_sub_list() -> list:
    return ['언어', '추리']


def get_subject_list() -> list:
    return ['언어이해', '추리논증']


def get_answer_tab() -> list:
    return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(get_subject_list())]


def get_score_tab(is_filtered=False):
    suffix = 'Filtered' if is_filtered else ''
    score_template_table = 'a_prime_leet/snippets/predict_detail_sheet_score_table.html'
    return [
        {'id': '0', 'title': '내 성적', 'prefix': f'my{suffix}', 'template': score_template_table[0]},
        {'id': '1', 'title': '전체 기준', 'prefix': f'total{suffix}', 'template': score_template_table[1]},
        {'id': '2', 'title': '직렬 기준', 'prefix': f'department{suffix}', 'template': score_template_table[2]},
    ]


def get_subject_vars() -> dict[str, tuple[str, str, int]]:
    return {
        '언어': ('언어이해', 'subject_0', 0),
        '추리': ('추리논증', 'subject_1', 1),
        '총점': ('총점', 'sum', 2),
    }


def get_problem_count(exam):
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


def get_dict_stat_data(
        student: models.PredictStudent,
        is_confirmed_data: list,
        answer_data_set: dict,
        stat_type='total',
        is_filtered=False,
):
    subject_vars = get_subject_vars()
    problem_count = get_problem_count(student.leet.exam)
    problem_count['총점'] = sum(val for val in problem_count.values())
    stat_data = []
    for sub, (subject, fld, fld_idx) in subject_vars.items():
        url_answer_input = student.leet.get_predict_answer_input_url(fld) if sub != '총점' else ''
        answer_list = answer_data_set.get(fld)
        saved_answers = []
        if answer_list:
            saved_answers = [ans for ans in answer_list if ans]
        answer_count = max(student.answer_count.get(sub, 0), len(saved_answers))

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

            'rank': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0,
        })

    qs_answer = models.PredictAnswer.objects.prime_leet_qs_answer_by_student_and_stat_type_and_is_filtered(
        student, stat_type)
    participants_dict = {
        subject_vars[qs_a['problem__subject']][1]: qs_a['participant_count'] for qs_a in qs_answer
    }
    participants_dict['sum'] = participants_dict[min(participants_dict)] if participants_dict else 0

    field_vars = get_field_vars()
    scores = {fld: [] for fld in field_vars.keys()}
    qs_score = models.PredictScore.objects.prime_leet_qs_score_by_student_and_stat_type_and_is_filtered(
        student, stat_type, is_filtered)
    for stat in stat_data:
        fld = stat['field']
        if fld in participants_dict.keys():
            participants = participants_dict.get(fld, 0)
            stat.update({'participants': participants})
            if student.leet.is_answer_predict_opened:
                pass
            if student.leet.is_answer_official_opened:
                for qs_s in qs_score:
                    fld_score = qs_s[fld]
                    if fld_score is not None:
                        scores[fld].append(fld_score)

                student_score = getattr(student.score, fld)
                if scores[fld] and student_score:
                    sorted_scores = sorted(scores[fld], reverse=True)
                    rank = sorted_scores.index(student_score) + 1
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    avg_score = round(sum(scores[fld]) / participants, 1) if any(scores[fld]) else 0
                    stat.update({
                        'rank': rank,
                        'score': student_score,
                        'max_score': sorted_scores[0],
                        'top_score_10': sorted_scores[top_10_threshold - 1],
                        'top_score_20': sorted_scores[top_20_threshold - 1],
                        'avg_score': avg_score,
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
    sum = 0
    for stat in stat_data_total:
        sub = stat['sub']
        if sub != '총점':
            sum += score_predict[sub]
            stat['score_predict'] = score_predict[sub]
        else:
            stat['score_predict'] = sum


def get_dict_frequency_score(student) -> dict:
    score_frequency_list = models.PredictStudent.objects.filter(
        leet=student.leet).values_list('score__sum', flat=True)
    score_counts_list = [round(score, 1) for score in score_frequency_list if score]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_target_score = round(student.score.sum, 1) if student.score.sum else 0
    score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

    return {'score_points': dict(score_counts), 'score_colors': score_colors}


def get_chart_score(student, stat_data_total, stat_department):
    field_vars = get_field_vars(student.psat)
    student_score = [getattr(student.score, field) for field in field_vars]

    chart_score = {
        'my_score': student_score,
        'total_average': [],
        'total_score_20': [],
        'total_score_10': [],
        'total_top': [],
        'department_average': [],
        'department_score_20': [],
        'department_score_10': [],
        'department_top': [],
    }

    score_list = [score for score in student_score if score is not None]
    for stat in stat_data_total:
        score_list.extend([stat['avg_score'], stat['top_score_20'], stat['top_score_10'], stat['max_score']])
        chart_score['total_average'].append(stat['avg_score'])
        chart_score['total_score_20'].append(stat['top_score_20'])
        chart_score['total_score_10'].append(stat['top_score_10'])
        chart_score['total_top'].append(stat['max_score'])
    for stat in stat_department:
        score_list.extend([stat['avg_score'], stat['top_score_20'], stat['top_score_10'], stat['max_score']])
        chart_score['department_average'].append(stat['avg_score'])
        chart_score['department_score_20'].append(stat['top_score_20'])
        chart_score['department_score_10'].append(stat['top_score_10'])
        chart_score['department_top'].append(stat['max_score'])

    chart_score['min_score'] = (min(score_list) // 5) * 5
    return chart_score


def get_data_answers(qs_student_answer):
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
