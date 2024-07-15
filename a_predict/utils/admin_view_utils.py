from copy import deepcopy

from django.db.models import F


def get_admin_stat_data(exam_vars: dict, exam):
    score_fields = exam_vars['score_fields']
    field_vars = exam_vars['field_vars']
    department_model = exam_vars['department_model']

    admin_score_fields = ['department'] + [score_fields[-1]]
    admin_score_fields.extend(score_fields[:-1])
    admin_score_field_vars = deepcopy(field_vars)
    admin_score_field_vars['department'] = ('전체', 'department')

    qs_department = department_model.objects.filter(exam=exam.exam).order_by('id')
    departments = [{'id': 'total', 'unit': '', 'department': '전체'}]
    departments.extend(qs_department.values('id', 'unit', department=F('name')))
    participants = exam.participants
    statistics = exam.statistics

    stat_data: dict[str, list[list[dict]]] = {
        'all': [[{} for _ in admin_score_fields] for _ in departments],
        'filtered': [[{} for _ in admin_score_fields] for _ in departments],
    }
    for category in ['all', 'filtered']:
        for department_idx, department in enumerate(departments):
            for field_idx, field in enumerate(admin_score_fields):
                sub, subject = admin_score_field_vars[field]
                department_id = str(department['id'])
                if field == 'department':
                    stat_data[category][department_idx][field_idx] = department
                else:
                    if statistics[category][department_id][field]:
                        stat_data[category][department_idx][field_idx] = {
                            'field': field, 'sub': sub, 'subject': subject,
                            'participants': participants[category][department_id][field],
                            'max': statistics[category][department_id][field]['max'],
                            't10': statistics[category][department_id][field]['t10'],
                            't20': statistics[category][department_id][field]['t20'],
                            'avg': statistics[category][department_id][field]['avg'],
                        }
    return stat_data


def get_admin_answer_count_data(exam_vars: dict, exam, answer_predict):
    answer_count_model = exam_vars['answer_count_model']
    problem_count = exam_vars['problem_count']
    subject_fields = exam_vars['subject_fields']
    exam_info = {'year': exam.year, 'exam': exam.exam, 'round': exam.round}

    rank_list = exam_vars['rank_list']
    qs_answer_count = answer_count_model.objects.filter(
        **exam_info).order_by('subject', 'number')
    answer_count_data: dict[str, list[list[dict[str, int | list]]]] = {
        'all': [[
            {
                'field': field, 'no': no,
                'ans_official': exam.answer_official[field][no - 1],
                'ans_predict': answer_predict[field_idx][no - 1]['ans'],
                'all_rank': [], 'top_rank': [], 'mid_rank': [], 'low_rank': [],
            } for no in range(1, problem_count[field] + 1)
        ] for field_idx, field in enumerate(subject_fields)],
        'filtered': [[
            {
                'field': field, 'no': no, 'ans_official': 1, 'ans_predict': 1,
                'all_rank': [], 'top_rank': [], 'mid_rank': [], 'low_rank': [],
            } for no in range(1, problem_count[field] + 1)
        ] for field in subject_fields],
    }
    for category in ['all', 'filtered']:
        for answer_count in qs_answer_count:
            no = answer_count.number
            field = answer_count.subject
            field_idx = subject_fields.index(field)
            target_count =answer_count_data[category][field_idx][no - 1]

            count = getattr(answer_count, category)
            target_count.update({
                field: count[field] for field in rank_list
            })

            ans_official = exam.answer_official[field][no - 1]
            target_count.update({
                f'rate_{field}': round(count[field][ans_official] * 100 / count[field][-1], 1) for field in rank_list
            })
            target_count.update({
                'rate_gap': target_count['rate_top_rank'] - target_count['rate_low_rank']
            })

    return answer_count_data
