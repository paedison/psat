from collections import Counter

from django.db.models import QuerySet

from common.constants import icon_set_new


def get_empty_dict_list_from_fields(fields: list[str]) -> dict[str, list]:
    return {field: [] for field in fields}


def get_tuple_data_answer_official_student(
        answer_student: dict,
        answer_official: dict,
        qs_answer_count: QuerySet,
        subject_fields: list
) -> tuple:
    data_answer_official = get_empty_dict_list_from_fields(fields=subject_fields)
    data_answer_student = get_empty_dict_list_from_fields(fields=subject_fields)

    for qs in qs_answer_count:
        field = qs.subject
        ans_official = answer_official[field][qs.number - 1]
        ans_student = answer_student[field][qs.number - 1]

        if 1 <= ans_official <= 5:
            result = ans_student == ans_official
            rate_correct = getattr(qs, f'rate_{ans_official}')
        else:
            answer_official_list = [int(digit) for digit in str(ans_official)]
            result = ans_student in answer_official_list
            rate_correct = sum(getattr(qs, f'rate_{ans}') for ans in answer_official_list)
        rate_selection = getattr(qs, f'rate_{ans_student}')

        data_answer_official[field].append({
            'no': qs.number,
            'ans': ans_official,
            'rate_correct': rate_correct,
        })
        data_answer_student[field].append({
            'no': qs.number,
            'ans': ans_student,
            'rate_selection': rate_selection,
            'result': result,
        })

    data_answer_official = {key: value for key, value in data_answer_official.items() if value}
    data_answer_student = {key: value for key, value in data_answer_student.items() if value}
    return data_answer_official, data_answer_student


def get_dict_stat_data(student, statistics_type: str, field_vars: dict) -> dict:
    filter_exp = {'year': student.year, 'exam': student.exam, 'round': student.round}
    participants_dict = student.participants_total
    if statistics_type == 'department':
        filter_exp['department'] = student.department
        participants_dict = student.participants_department
    qs_student = student.__class__.objects.filter(**filter_exp).values('score')

    score = {}
    stat_data = {}
    for field, subject_tuple in field_vars.items():
        participants = participants_dict[field]
        score[field] = [qs['score'][field] for qs in qs_student if field in qs['score']]

        student_score = student.score[field]
        sorted_scores = sorted(score[field], reverse=True)
        rank = sorted_scores.index(student_score) + 1
        top_10_threshold = max(1, int(participants * 0.1))
        top_20_threshold = max(1, int(participants * 0.2))

        stat_data[field] = {
            'field': field,
            'is_confirmed': True,
            'sub': subject_tuple[0],
            'subject': subject_tuple[1],
            'icon': icon_set_new.ICON_SUBJECT[subject_tuple[0]],
            'rank': rank,
            'score': student_score,
            'participants': participants,
            'max_score': sorted_scores[0],
            'top_score_10': sorted_scores[top_10_threshold - 1],
            'top_score_20': sorted_scores[top_20_threshold - 1],
            'avg_score': sum(score[field]) / participants,
        }
    return stat_data


def get_dict_frequency_score(student, target_avg: str) -> dict:
    qs_student = student.__class__.objects.filter(
        year=student.year, round=student.round).values_list('score', flat=True)
    score_counts_list = [round(score[target_avg], 1) for score in qs_student]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_psat_avg = round(student.score[target_avg], 1)
    avg_colors = ['blue' if score == student_psat_avg else 'white' for score in score_counts.keys()]

    return {'avg_points': dict(score_counts), 'avg_colors': avg_colors}
