from collections import Counter

import numpy as np
from django.db.models import F

from .. import models


def get_sub_list() -> list:
    return ['언어', '추리']


def get_subject_list() -> list:
    return ['언어이해', '추리논증']


def get_answer_tab() -> list:
    return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(get_subject_list())]


def get_score_tab() -> list:
    score_template_table = 'a_prime_leet/snippets/detail_sheet_score_table.html'
    return [
            {'id': '0', 'title': '전체', 'prefix': 'total', 'template': score_template_table},
            {'id': '1', 'title': '1지망', 'prefix': 'aspiration1', 'template': score_template_table},
            {'id': '2', 'title': '2지망', 'prefix': 'aspiration2', 'template': score_template_table},
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


def get_student_dict(user, exam_list):
    if user.is_authenticated:
        annotate_dict = {}
        field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = F(f'score__raw_{fld}')
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
        students = (
            models.ResultStudent.objects.filter(registries__user=user, leet__in=exam_list)
            .select_related('leet', 'score', 'rank').order_by('id').annotate(**annotate_dict)
        )
        return {student.leet: student for student in students}
    return {}


def get_student(leet, user):
    annotate_dict = {
        'score_sum': F('score__sum'),
        'rank_num': F(f'rank__participants'),
    }
    field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'sum'}
    for key, fld in field_dict.items():
        annotate_dict[f'score_{key}'] = F(f'score__{fld}')
        annotate_dict[f'rank_{key}'] = F(f'rank__{fld}')

    return (
        models.ResultStudent.objects.filter(registries__user=user, leet=leet)
        .select_related('leet', 'score', 'rank')
        .annotate(**annotate_dict).order_by('id').last()
    )


def get_dict_stat_data(student: models.ResultStudent, stat_type='total') -> dict:
    qs_answers = models.ResultAnswer.objects.get_filtered_qs_by_student_and_stat_type(student, stat_type)
    qs_score = models.ResultScore.objects.get_filtered_qs_by_student_and_stat_type(student, stat_type)
    sub_list = get_sub_list()
    subject_vars = get_subject_vars()
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }

    participants_dict = {
        subject_vars[entry['problem__subject']][1]: entry['participant_count']
        for entry in qs_answers
    }
    participants_dict['sum'] = max(
        participants_dict[f'subject_{idx}'] for idx, _ in enumerate(sub_list)
    )

    raw_scores = {}
    scores = {}
    stat_data = {}
    for fld, (sub, subject, _) in field_vars.items():
        if fld in participants_dict.keys():
            participants = participants_dict[fld]
            raw_scores[fld] = [qs[f'raw_{fld}'] for qs in qs_score]
            scores[fld] = [qs[fld] for qs in qs_score]
            student_score = getattr(student.score, fld)

            sorted_raw_scores = sorted(raw_scores[fld], reverse=True)
            sorted_scores = sorted(scores[fld], reverse=True)

            def get_top_score(_sorted_scores, percentage):
                if _sorted_scores:
                    threshold = max(1, int(participants * percentage))
                    return _sorted_scores[threshold - 1]

            stat_data[fld] = {
                'field': fld,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'raw_score': getattr(student.score, f'raw_{fld}'),
                'score': student_score,
                'rank': sorted_scores.index(student_score) + 1,
                'participants': participants,
                'max_raw_score': sorted_raw_scores[0],
                'top_raw_score_10': get_top_score(sorted_raw_scores, 0.10),
                'top_raw_score_25': get_top_score(sorted_raw_scores, 0.25),
                'top_raw_score_50': get_top_score(sorted_raw_scores, 0.50),
                'raw_score_avg': round(sum(raw_scores[fld]) / participants, 1),
                'raw_score_stddev': round(np.std(np.array(sorted_raw_scores), ddof=1), 1),
                'max_score': sorted_scores[0],
                'top_score_10': get_top_score(sorted_scores, 0.10),
                'top_score_25': get_top_score(sorted_scores, 0.25),
                'top_score_50': get_top_score(sorted_scores, 0.50),
            }
    return stat_data


def get_dict_frequency_score(student) -> dict:
    score_frequency_list = models.ResultStudent.objects.get_student_score_frequency_list(student)
    score_counts_list = [round(score, 1) for score in score_frequency_list]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_target_score = round(student.score.sum, 1)
    score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

    return {'score_points': dict(score_counts), 'score_colors': score_colors}


def get_data_answers(qs_answer):
    sub_list = get_sub_list()
    subject_vars = get_subject_vars()
    data_answers = [[] for _ in sub_list]

    for qs_a in qs_answer:
        sub = qs_a.problem.subject
        idx = sub_list.index(sub)
        field = subject_vars[sub][1]
        ans_official = qs_a.problem.answer
        ans_student = qs_a.answer

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_a.no = qs_a.problem.number
        qs_a.ans_official = ans_official
        qs_a.ans_official_circle = qs_a.problem.get_answer_display
        qs_a.ans_student = ans_student
        qs_a.ans_list = answer_official_list
        qs_a.field = field
        qs_a.result = ans_student in answer_official_list

        qs_a.rate_correct = qs_a.problem.result_answer_count.get_answer_rate(ans_official)
        qs_a.rate_correct_top = qs_a.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
        qs_a.rate_correct_mid = qs_a.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
        qs_a.rate_correct_low = qs_a.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            qs_a.rate_gap = qs_a.rate_correct_top - qs_a.rate_correct_low
        except TypeError:
            qs_a.rate_gap = None

        qs_a.rate_selection = qs_a.problem.result_answer_count.get_answer_rate(ans_student)
        qs_a.rate_selection_top = qs_a.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
        qs_a.rate_selection_mid = qs_a.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
        qs_a.rate_selection_low = qs_a.problem.result_answer_count_low_rank.get_answer_rate(ans_student)

        data_answers[idx].append(qs_a)
    return data_answers
