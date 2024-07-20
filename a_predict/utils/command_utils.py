import traceback

import django.db.utils
from django.db import transaction

from .get_queryset import get_department_dict
from ..views.base_info import PsatExamVars, PoliceExamVars

__all__ = [
    'get_default_dict',
    'get_student_model_data', 'get_old_answer_data', 'get_exam_model_data',
    'get_total_answer_lists_and_score_data', 'get_answer_count_model_data',
    'get_statistics_data', 'get_total_answer_count_model_data',
    'create_or_update_model', 'update_model_data',
    'add_obj_to_model_update_data', 'get_empty_model_data',
]

UNIT_DICT = {
    1: '5급 행정(전국)',
    2: '5급 행정(지역)',
    3: '5급 기술(전국)',
    4: '5급 기술(지역)',
    5: '외교관후보자',
    6: '지역인재 7급',
    7: '입법고시',
    8: '7급 국가직(일반)',
    9: '7급 국가직(장애인)',
    10: '민간경력',
    11: '프라임 모의고사',
}
DEPARTMENT_DICT = {
    1: '5급 행정(전국)-일반행정',
    2: '5급 행정(전국)-인사조직',
    3: '5급 행정(전국)-법무행정',
    4: '5급 행정(전국)-재경',
    5: '5급 행정(전국)-국제통상',
    6: '5급 행정(전국)-교육행정',
    7: '5급 행정(전국)-사회복지',
    8: '5급 행정(전국)-교정',
    9: '5급 행정(전국)-보호',
    10: '5급 행정(전국)-검찰',
    11: '5급 행정(전국)-출입국관리',
    12: '5급 행정(지역)-서울',
    13: '5급 행정(지역)-부산',
    14: '5급 행정(지역)-대구',
    15: '5급 행정(지역)-인천',
    16: '5급 행정(지역)-광주',
    17: '5급 행정(지역)-대전',
    18: '5급 행정(지역)-울산',
    19: '5급 행정(지역)-세종',
    20: '5급 행정(지역)-경기',
    132: '5급 행정(지역)-강원',
    21: '5급 행정(지역)-충북',
    22: '5급 행정(지역)-충남',
    23: '5급 행정(지역)-전북',
    24: '5급 행정(지역)-전남',
    25: '5급 행정(지역)-경북',
    26: '5급 행정(지역)-경남',
    27: '5급 행정(지역)-제주',
    28: '5급 기술(전국)-일반기계',
    29: '5급 기술(전국)-전기',
    30: '5급 기술(전국)-화공',
    31: '5급 기술(전국)-일반농업',
    32: '5급 기술(전국)-산림자원',
    33: '5급 기술(전국)-일반수산',
    34: '5급 기술(전국)-일반환경',
    35: '5급 기술(전국)-기상',
    36: '5급 기술(전국)-일반토목',
    37: '5급 기술(전국)-건축',
    38: '5급 기술(전국)-시설조경',
    39: '5급 기술(전국)-방재안전',
    40: '5급 기술(전국)-전산개발',
    41: '5급 기술(전국)-데이터',
    42: '5급 기술(전국)-정보보호',
    43: '5급 기술(전국)-통신기술',
    44: '5급 기술(지역)-서울',
    45: '5급 기술(지역)-부산',
    46: '5급 기술(지역)-대구',
    47: '5급 기술(지역)-인천',
    48: '5급 기술(지역)-광주',
    49: '5급 기술(지역)-대전',
    50: '5급 기술(지역)-울산',
    51: '5급 기술(지역)-세종',
    52: '5급 기술(지역)-경기',
    53: '5급 기술(지역)-충북',
    54: '5급 기술(지역)-충남',
    55: '5급 기술(지역)-전북',
    56: '5급 기술(지역)-전남',
    57: '5급 기술(지역)-경북',
    58: '5급 기술(지역)-경남',
    59: '5급 기술(지역)-제주',
    60: '외교관후보자-일반외교',
    61: '지역인재 7급-행정',
    133: '지역인재 7급-기술',
}


def get_default_dict(exam_vars: PsatExamVars | PoliceExamVars, default):
    score_fields = exam_vars.score_fields
    department_dict = get_department_dict(exam_vars)
    default_dict = {
        'all': {'total': {fld: default for fld in score_fields}},
        'filtered': {'total': {fld: default for fld in score_fields}},
    }
    default_dict['all'].update({
        d_id: {fld: default for fld in score_fields} for d_id in department_dict.values()
    })
    default_dict['filtered'].update({
        d_id: {fld: default for fld in score_fields} for d_id in department_dict.values()
    })
    return default_dict


def get_student_model_data(exam_vars, old_students) -> dict:
    student_model_data = get_empty_model_data()

    for student in old_students:
        old_answer_data = get_old_answer_data(exam_vars, student)
        student_info = {}
        base_info = {
            'user_id': student.user_id, 'year': exam_vars.exam_year,
            'exam': exam_vars.exam_exam, 'round': exam_vars.exam_round,
            'name': student.name, 'serial': student.serial,
        }
        extra_info = {
            'unit': UNIT_DICT[student.unit_id],
            'department': DEPARTMENT_DICT[student.department_id],
            'password': student.password,
            'prime_id': student.prime_id,
        }
        answer_info = {
            'answer': old_answer_data['answer'],
            'answer_count': old_answer_data['answer_count'],
            'answer_confirmed': old_answer_data['answer_confirmed'],
            'answer_all_confirmed_at': old_answer_data['answer_all_confirmed_at'],
        }
        student_info.update(base_info)
        student_info.update(extra_info)
        student_info.update(answer_info)

        answer_fields = [key for key in answer_info.keys()]
        update_model_data(
            student_model_data, exam_vars.student_model, base_info, student_info, answer_fields)
    return student_model_data


def get_old_answer_data(exam_vars, student):
    subject_fields: list = exam_vars.subject_fields

    old_answers = [
        exam_vars.old_answer_model.objects.filter(student=student, sub=sub).first() for sub in exam_vars.sub_list
    ]

    answer_dict = {
        field: [0 for _ in range(count)] for field, count in exam_vars.problem_count.items()
    }
    answer_count_dict = {field: 0 for field in subject_fields}
    answer_confirmed_dict = {field: False for field in subject_fields}
    answer_updated_at_dict = {field: None for field in subject_fields}
    answer_all_confirmed_at = None

    for answer in old_answers:
        if answer:
            field = exam_vars.subject_vars[answer.sub][1]
            answer_confirmed_dict[field] = answer.is_confirmed
            answer_updated_at_dict[field] = answer.updated_at

            for idx in range(exam_vars.problem_count[field]):
                no = idx + 1
                ans = getattr(answer, f'prob{no}') or 0
                answer_dict[field][idx] = ans
                answer_count_dict[field] += 1 if ans else 0
    answer_count_dict['psat_avg'] = sum([i for i in answer_count_dict.values()])
    answer_confirmed_dict['psat_avg'] = all([b for b in answer_confirmed_dict.values()])

    if all([val for val in answer_confirmed_dict.values()]):
        try:
            answer_all_confirmed_at = max([val for val in answer_updated_at_dict.values()])
        except ValueError:
            pass

    return {
        'answer': answer_dict,
        'answer_count': answer_count_dict,
        'answer_confirmed': answer_confirmed_dict,
        'answer_all_confirmed_at': answer_all_confirmed_at,
    }


def get_exam_model_data(exam_vars: PsatExamVars, participants):
    exam = exam_vars.exam
    exam_model_data = get_empty_model_data()
    if exam.participants != participants:
        exam.participants = participants
        exam_model_data['update_list'].append(exam)
        exam_model_data['update_count'] += 1
    return exam_model_data


def get_total_answer_lists_and_score_data(exam_vars: PsatExamVars, qs_student) -> tuple:
    answer_official = exam_vars.exam.answer_official
    score_data = get_empty_model_data()
    total_answer_lists = {field: [] for field in exam_vars.subject_fields}

    for student in qs_student:
        score = {field: 0 for field in exam_vars.score_fields}
        for field, answer in student.answer.items():
            if student.answer_confirmed[field]:
                total_answer_lists[field].append(answer)

            score_unit = 4 if field in ['heonbeob'] else 2.5
            correct_count = 0
            for idx, ans in enumerate(answer):
                correct_count += 1 if ans == answer_official[field][idx] else 0
            score[field] = correct_count * score_unit

        sum_list = [score[field] for field in exam_vars.sum_fields if field in score]
        score['psat_avg'] = sum(sum_list) / 3 if sum_list else 0

        add_obj_to_model_update_data(
            score_data, student, {'score': score}, ['score'])

    return total_answer_lists, score_data


def get_answer_count_model_data(
        exam_vars: PsatExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for field in exam_vars.subject_fields:
        for count in all_count_dict[field]:
            if count['count_total']:
                problem_info = exam_vars.get_problem_info(
                    count['subject'], count['number'])
                update_model_data(
                    answer_count_model_data, exam_vars.answer_count_model,
                    problem_info, count, matching_fields)
    return answer_count_model_data


def get_statistics_data(exam_vars: PsatExamVars, statistics):
    exam = exam_vars.exam
    statistics_data = get_empty_model_data()
    if exam.statistics != statistics:
        exam.statistics = statistics
        statistics_data['update_list'].append(exam)
        statistics_data['update_count'] += 1
    return statistics_data


def get_total_answer_count_model_data(
        exam_vars: PsatExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for field in exam_vars.subject_fields:
        for data in all_count_dict[field]:
            problem_info = exam_vars.get_problem_info(data['subject'], data['number'])
            update_model_data(
                answer_count_model_data, exam_vars.answer_count_model,
                problem_info, data, matching_fields)
    return answer_count_model_data


def create_or_update_model(model, update_fields: list, model_data: dict):
    model_name = model._meta.model_name
    update_list = model_data['update_list']
    create_list = model_data['create_list']
    update_count = model_data['update_count']
    create_count = model_data['create_count']

    try:
        with transaction.atomic():
            if update_list:
                model.objects.bulk_update(update_list, update_fields)
                message = f'Successfully updated {update_count} {model_name} instances.'
            elif create_list:
                model.objects.bulk_create(create_list)
                message = f'Successfully created {create_count} {model_name} instances.'
            elif not update_list and not create_list:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = 'An error occurred during the transaction.'
    print(message)


def update_model_data(
        model_data: dict, model, lookup: dict,
        matching_data: dict, matching_fields: list,
        obj=None,
):
    if obj:
        add_obj_to_model_update_data(model_data, obj, matching_data, matching_fields)
    else:
        try:
            obj = model.objects.get(**lookup)
            add_obj_to_model_update_data(model_data, obj, matching_data, matching_fields)
        except model.DoesNotExist:
            model_data['create_list'].append(model(**matching_data))
            model_data['create_count'] += 1
        except model.MultipleObjectsReturned:
            print(f'Instance is duplicated.')


def add_obj_to_model_update_data(
        model_data: dict, obj,
        matching_data: dict, matching_fields: list,
):
    fields_not_match = any(
        getattr(obj, fld) != matching_data[fld] for fld in matching_fields)
    if fields_not_match:
        for fld in matching_fields:
            setattr(obj, fld, matching_data[fld])
        model_data['update_list'].append(obj)
        model_data['update_count'] += 1


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}
