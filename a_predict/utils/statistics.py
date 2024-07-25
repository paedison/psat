from .command_utils import get_default_dict
from .get_queryset import get_department_dict
from a_predict.views.old_base_info import PsatExamVars

__all__ = [
    'get_participants', 'get_rank_data', 'get_confirmed_scores', 'get_statistics',
]


def get_participants(exam_vars: PsatExamVars, qs_student):
    participants = get_default_dict(exam_vars, 0)
    department_dict = get_department_dict(exam_vars)

    for student in qs_student:
        d_id = department_dict[student.department]
        for field, is_confirmed in student.answer_confirmed.items():
            if is_confirmed:
                participants['all']['total'][field] += 1
                participants['all'][d_id][field] += 1

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam_vars.exam.answer_official_opened_at:
                participants['filtered']['total'][field] += 1
                participants['filtered'][d_id][field] += 1
    return participants


def get_rank_data(exam_vars: PsatExamVars, qs_student) -> dict:
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    scores_total = get_confirmed_scores(exam_vars, qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all'], 'department': {}},
        'filtered': {'total': scores_total['filtered'], 'department': {}},
    }

    rank_data = get_empty_model_data()
    for student in qs_student:
        scores_department = get_confirmed_scores(exam_vars, qs_student, student.department)
        scores['all']['department'] = scores_department['all']
        scores['filtered']['department'] = scores_department['filtered']

        rank = {
            'all': {
                'total': {field: 0 for field in score_fields},
                'department': {field: 0 for field in score_fields},
            },
            'filtered': {
                'total': {field: 0 for field in score_fields},
                'department': {field: 0 for field in score_fields},
            },
        }
        for field in score_fields:
            score_student = student.score[field]
            if student.answer_confirmed[field]:
                rank['all']['total'][field] = (
                        scores['all']['total'][field].index(score_student) + 1)
                rank['all']['department'][field] = (
                        scores['all']['department'][field].index(score_student) + 1)

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam_vars.exam.answer_official_opened_at:
                rank['filtered']['total'][field] = (
                        scores['filtered']['total'][field].index(score_student) + 1)
                rank['filtered']['department'][field] = (
                        scores['filtered']['department'][field].index(score_student) + 1)

        if student.rank != rank:
            student.rank = rank
            rank_data['update_list'].append(student)
            rank_data['update_count'] += 1

    return rank_data


def get_confirmed_scores(
        exam_vars: PsatExamVars, qs_student, department: str | None = None
) -> dict:
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    if department:
        qs_student = qs_student.filter(department=department)

    scores = {
        'all': {field: [] for field in score_fields},
        'filtered': {field: [] for field in score_fields},
    }
    for field in score_fields:
        for student in qs_student:
            if student.answer_confirmed[field]:
                scores['all'][field].append(student.score[field])

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam_vars.exam.answer_official_opened_at:
                scores['filtered'][field].append(student.score[field])

    sorted_scores = {
        'all': {field: sorted(scores['all'][field], reverse=True) for field in score_fields},
        'filtered': {field: sorted(scores['filtered'][field], reverse=True) for field in score_fields},
    }
    return sorted_scores


def get_statistics(exam_vars: PsatExamVars, qs_department, qs_student):
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    scores_total = get_confirmed_scores(exam_vars, qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all']},
        'filtered': {'total': scores_total['filtered']},
    }
    statistics: dict[str, dict[str | int, dict]] = {
        'all': {
            'total': {field: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for field in score_fields},
        },
        'filtered': {
            'total': {field: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for field in score_fields},
        },
    }
    for department in qs_department:
        scores_department = get_confirmed_scores(exam_vars, qs_student, department.name)
        scores['all'][department.id] = scores_department['all']
        scores['filtered'][department.id] = scores_department['filtered']
        statistics['all'][department.id] = {field: {} for field in score_fields}
        statistics['filtered'][department.id] = {field: {} for field in score_fields}

    for key, value in scores.items():
        for department, scores_dict in value.items():
            for field, score_list in scores_dict.items():
                participants = len(score_list)
                top_10 = max(1, int(participants * 0.1))
                top_20 = max(1, int(participants * 0.2))

                if score_list:
                    statistics[key][department][field]['max'] = round(score_list[0], 1)
                    statistics[key][department][field]['t10'] = round(score_list[top_10 - 1], 1)
                    statistics[key][department][field]['t20'] = round(score_list[top_20 - 1], 1)
                    statistics[key][department][field]['avg'] = round(
                        sum(score_list) / participants if participants else 0, 1)
    return statistics


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}
