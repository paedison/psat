from collections import Counter

from common.constants import icon_set_new
from ..views.base_info import ScorePrimePsatExamVars, ScorePrimePoliceExamVars, ScorePrimePoliceAdminExamVars

__all__ = [
    'get_exam_vars', 'get_admin_exam_vars',
    'get_tuple_data_answer_official_student', 'get_dict_stat_data',
    'get_dict_frequency_score',
]


def get_exam_vars(exam_type: str, exam_year: int, exam_round: int):
    if exam_type == 'psat':
        return ScorePrimePsatExamVars(exam_type, exam_year, exam_round)
    else:
        return ScorePrimePoliceExamVars(exam_type, exam_year, exam_round)


def get_admin_exam_vars(exam_type: str, exam_year: int, exam_round: int):
    if exam_type == 'psat':
        return ScorePrimePsatExamVars(exam_type, exam_year, exam_round)
    else:
        return ScorePrimePoliceAdminExamVars(exam_type, exam_year, exam_round)


def get_empty_dict_list_from_fields(fields: list[str]) -> dict[str, list]:
    return {field: [] for field in fields}


def get_tuple_data_answer_official_student(
        exam_vars: ScorePrimePsatExamVars | ScorePrimePoliceExamVars) -> tuple:
    answer_student = exam_vars.student.answer
    answer_official = exam_vars.exam.answer_official
    qs_answer_count = exam_vars.qs_answer_count
    subject_fields = exam_vars.subject_fields

    data_answer_official = get_empty_dict_list_from_fields(subject_fields)
    data_answer_student = get_empty_dict_list_from_fields(subject_fields)

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


def get_dict_stat_data(
        exam_vars: ScorePrimePsatExamVars | ScorePrimePoliceExamVars,
        statistics_type: str) -> dict:
    student = exam_vars.student
    field_vars = exam_vars.field_vars
    filter_exp = exam_vars.exam_info.copy()
    participants_dict = student.participants_total
    if statistics_type == 'department':
        filter_exp['department'] = student.department
        participants_dict = student.participants_department
    qs_student = exam_vars.student_model.objects.filter(**filter_exp).values('score')

    score = {}
    stat_data = {}
    for field, subject_tuple in field_vars.items():
        if field in participants_dict.keys():
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
    if exam_vars.exam_type == 'police':
        if 'minbeob' in stat_data.keys():
            stat_data['selection'] = stat_data['minbeob']
        elif 'haenghag' in stat_data.keys():
            stat_data['selection'] = stat_data['haenghag']
        stat_data['selection']['field'] = 'selection'

    return stat_data


def get_dict_frequency_score(
        exam_vars: ScorePrimePsatExamVars | ScorePrimePoliceExamVars, target_score: str) -> dict:
    qs_student = exam_vars.student_model.objects.filter(
        **exam_vars.exam_info).values_list('score', flat=True)
    score_counts_list = [round(score[target_score], 1) for score in qs_student]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_target_score = round(exam_vars.student.score[target_score], 1)
    score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

    return {'score_points': dict(score_counts), 'score_colors': score_colors}
