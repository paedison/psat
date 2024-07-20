import logging
import traceback
from collections import Counter

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from a_predict import models
from predict import models as old_predict_models

# 로그 설정
formatter = logging.Formatter('%(message)s')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('data_setup_old.log', encoding='utf-8', mode='w')
file_handler.setFormatter(formatter)
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


PSAT_VARS = {
    'sub_list': ['헌법', '언어', '자료', '상황'],
    'subject_list': ['헌법', '언어논리', '자료해석', '상황판단'],
    'subject_fields': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang'],
    'score_fields': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg'],
    'psat_fields': ['eoneo', 'jaryo', 'sanghwang'],
    'subject_vars': {
        '헌법': ('헌법', 'heonbeob'),
        '언어': ('언어논리', 'eoneo'),
        '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'),
        '평균': ('PSAT 평균', 'psat_avg'),
    },
    'field_vars': {
        'heonbeob': ('헌법', '헌법'),
        'eoneo': ('언어', '언어논리'),
        'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'),
        'psat_avg': ('평균', 'PSAT 평균'),
    },
    'problem_count': {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40},
    'rank_list': ['all_rank', 'low_rank', 'mid_rank', 'top_rank'],
    'old_answer_model': old_predict_models.Answer
}


def get_exam_vars(exam_info: dict):
    exam_vars = {
        'year': exam_info['year'],
        'exam': exam_info['exam'],
        'round': exam_info['round'],
        'info': exam_info,
    }
    if exam_info['exam'] == '행시':
        exam_vars.update(PSAT_VARS)
        exam_vars.update({
            'exam_model': models.PsatExam,
            'student_model': models.PsatStudent,
            'answer_count_model': models.PsatAnswerCount,
            'department_model': models.PsatDepartment,
        })
    return exam_vars


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam type')  # 행시
        parser.add_argument('exam_round', type=str, help='Round')  # 0

    def handle(self, *args, **kwargs):
        exam_year = kwargs['exam_year']
        exam_exam = kwargs['exam_exam']
        exam_round = kwargs['exam_round']
        exam_info = {'year': exam_year, 'exam': exam_exam, 'round': exam_round}

        # Set up exam_vars
        exam_vars = get_exam_vars(exam_info=exam_info)
        exam_model = exam_vars['exam_model']
        department_model = exam_vars['department_model']
        student_model = exam_vars['student_model']
        answer_count_model = exam_vars['answer_count_model']

        answer_official = exam_model.objects.get(**exam_info).answer_official

        # Create or update student_model instances
        old_students = old_predict_models.Student.objects.filter(
            exam__ex=exam_exam, exam__round=exam_round).annotate(created_at=F('timestamp'))
        student_data = get_student_model_data(
            exam_vars=exam_vars, old_students=old_students)
        student_update_fields = ['answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        create_or_update_model(
            model=student_model, update_fields=student_update_fields, model_data=student_data)

        # Update exam_model for participants
        qs_student = student_model.objects.filter(**exam_info)
        exam = exam_model.objects.filter(**exam_info).first()
        participants = get_participants(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        exam_model_data = get_exam_model_data(exam=exam, participants=participants)
        create_or_update_model(
            model=exam_model, update_fields=['participants'], model_data=exam_model_data)

        # Update student_model for score
        total_answer_lists, score_data = get_total_answer_lists_and_score_data(
            exam_vars=exam_vars,
            qs_student=qs_student,
            answer_official=answer_official,
        )
        create_or_update_model(
            model=student_model, update_fields=['score'], model_data=score_data)

        # Update student_model for rank
        rank_data = get_rank_data(exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        create_or_update_model(
            model=student_model,
            update_fields=['rank'],
            model_data=rank_data,
        )

        # Create or update student_model for answer count
        all_count_dict = get_all_count_dict(
            exam_vars=exam_vars, total_answer_lists=total_answer_lists)
        answer_count_matching_fields = [
            'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
            'count_0', 'count_multiple', 'count_total',
        ]
        answer_count_data = get_answer_count_model_data(
            exam_vars=exam_vars,
            matching_fields=answer_count_matching_fields,
            all_count_dict=all_count_dict,
        )
        create_or_update_model(
            model=answer_count_model,
            update_fields=answer_count_matching_fields,
            model_data=answer_count_data,
        )

        # Update exam_model for statistics
        qs_department = department_model.objects.filter(exam=exam_vars['exam']).order_by('id')
        statistics = get_statistics(
            exam_vars=exam_vars, exam=exam, qs_department=qs_department, qs_student=qs_student)
        statistics_data = get_statistics_data(exam=exam, statistics=statistics)
        create_or_update_model(
            model=exam_model, update_fields=['statistics'], model_data=statistics_data)

        # Update answer_count_model by rank
        total_answer_lists = get_total_answer_lists_by_category(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        total_count_dict = get_total_count_dict_by_category(
            exam_vars=exam_vars, total_answer_lists=total_answer_lists)
        total_answer_count_data = get_total_answer_count_model_data(
            exam_vars=exam_vars,
            matching_fields=['all', 'filtered'],
            all_count_dict=total_count_dict,
        )
        create_or_update_model(
            model=answer_count_model,
            update_fields=['all', 'filtered'],
            model_data=total_answer_count_data,
        )


def get_all_count_dict(exam_vars: dict, total_answer_lists: dict) -> dict:
    problem_count = exam_vars['problem_count']
    all_count_dict: dict[str, list[dict[str, str | int]]] = {
        field: [
            {
                'year': exam_vars['year'], 'exam': exam_vars['exam'],
                'round': exam_vars['round'], 'subject': field, 'number': number, 'answer': 0,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            } for number in range(1, count + 1)
        ] for field, count in problem_count.items()
    }
    for field, answer_lists in total_answer_lists.items():
        p_count = problem_count[field]
        if answer_lists:
            distributions = [Counter() for _ in range(p_count)]
            for lst in answer_lists:
                for i, value in enumerate(lst):
                    if value > 5:
                        distributions[i]['count_multiple'] += 1
                    else:
                        distributions[i][value] += 1

            for idx, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                all_count_dict[field][idx].update(count_dict)
    return all_count_dict


def get_total_answer_lists_by_category(exam_vars: dict, exam, qs_student):
    subject_fields = exam_vars['subject_fields']
    rank_list = exam_vars['rank_list']
    total_answer_lists_by_category: dict[str, dict[str, dict[str, list]]] = {
        'all': {rank: {field: [] for field in subject_fields} for rank in rank_list},
        'filtered': {rank: {field: [] for field in subject_fields} for rank in rank_list},
    }
    participants_all = exam.participants['all']['total']['psat_avg']
    participants_filtered = exam.participants['filtered']['total']['psat_avg']

    for student in qs_student:
        rank_all_student = student.rank['all']['total']['psat_avg']
        rank_filtered_student = student.rank['filtered']['total']['psat_avg']
        rank_ratio_all = rank_all_student / participants_all if participants_all else None
        rank_ratio_filtered = rank_filtered_student / participants_filtered if participants_filtered else None

        for field in subject_fields:
            if student.answer_confirmed[field]:
                ans_student = student.answer[field]
                top_rank_threshold = 0.27
                mid_rank_threshold = 0.73

                def append_answer(catgry: str, rank: str):
                    total_answer_lists_by_category[catgry][rank][field].append(ans_student)

                append_answer('all', 'all_rank')
                if rank_ratio_all and 0 <= rank_ratio_all <= top_rank_threshold:
                    append_answer('all', 'top_rank')
                elif rank_ratio_all and top_rank_threshold < rank_ratio_all <= mid_rank_threshold:
                    append_answer('all', 'mid_rank')
                elif rank_ratio_all and mid_rank_threshold < rank_ratio_all <= 1:
                    append_answer('all', 'low_rank')

                if student.answer_all_confirmed_at and student.answer_all_confirmed_at < exam.answer_official_opened_at:
                    append_answer('filtered', 'all_rank')
                    if rank_ratio_filtered and 0 <= rank_ratio_filtered <= top_rank_threshold:
                        append_answer('filtered', 'top_rank')
                    elif rank_ratio_filtered and top_rank_threshold < rank_ratio_filtered <= mid_rank_threshold:
                        append_answer('filtered', 'mid_rank')
                    elif rank_ratio_filtered and mid_rank_threshold < rank_ratio_filtered <= 1:
                        append_answer('filtered', 'low_rank')
    return total_answer_lists_by_category


def get_total_count_dict_by_category(exam_vars: dict, total_answer_lists: dict):
    problem_count = exam_vars['problem_count']
    rank_list = exam_vars['rank_list']

    total_count_dict: dict[str, list[dict[str, str | dict[str, list]]]] = {
        field: [
            {
                'year': exam_vars['year'], 'exam': exam_vars['exam'],
                'round': exam_vars['round'], 'subject': field, 'number': number,
                'all': {rank: [] for rank in rank_list},
                'filtered': {rank: [] for rank in rank_list},
            } for number in range(1, count + 1)
        ] for field, count in problem_count.items()
    }
    for category, value1 in total_answer_lists.items():
        for rank, value2 in value1.items():
            for field, answer_lists in value2.items():
                p_count = problem_count[field]
                if answer_lists:
                    distributions = [Counter() for _ in range(p_count)]
                    for lst in answer_lists:
                        for i, value in enumerate(lst):
                            if value > 5:
                                distributions[i]['count_multiple'] += 1
                            else:
                                distributions[i][value] += 1

                    for idx, counter in enumerate(distributions):
                        count_list = [counter.get(i, 0) for i in range(6)]
                        count_total = sum(count_list[1:])
                        count_list.extend([counter.get('count_multiple', 0), count_total])
                        total_count_dict[field][idx][category][rank] = count_list

    return total_count_dict


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


def get_student_model_data(exam_vars: dict, old_students) -> dict:
    student_model_data = get_empty_model_data()
    student_model = exam_vars['student_model']

    for student in old_students:
        old_answer_data = get_old_answer_data(exam_vars=exam_vars, student=student)
        student_info = {
            'user_id': student.user_id,
            'year': exam_vars['year'],
            'exam': exam_vars['exam'],
            'round': exam_vars['round'],

            'name': student.name,
            'serial': student.serial,
            'unit': UNIT_DICT[student.unit_id],
            'department': DEPARTMENT_DICT[student.department_id],

            'password': student.password,
            'prime_id': student.prime_id,

            'answer': old_answer_data['answer'],
            'answer_count': old_answer_data['answer_count'],
            'answer_confirmed': old_answer_data['answer_confirmed'],
            'answer_all_confirmed_at': old_answer_data['answer_all_confirmed_at'],
        }

        lookup_dict = {
            'user_id': student.user_id,
            'year': exam_vars['year'],
            'exam': exam_vars['exam'],
            'round': exam_vars['round'],
            'name': student.name,
            'serial': student.serial,
        }
        matching_fields = ['answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        update_model_data(
            model_data=student_model_data, model=student_model, lookup=lookup_dict,
            matching_data=student_info, matching_fields=matching_fields,
        )
    return student_model_data


def get_old_answer_data(exam_vars: dict, student):
    sub_list: dict = exam_vars['sub_list']
    problem_count: dict = exam_vars['problem_count']
    subject_fields: list = exam_vars['subject_fields']
    subject_vars: list = exam_vars['subject_vars']
    old_answer_model = exam_vars['old_answer_model']

    old_answers = [
        old_answer_model.objects.filter(student=student, sub=sub).first() for sub in sub_list
    ]

    answer_dict = {field: [0 for _ in range(count)] for field, count in problem_count.items()}
    answer_count_dict = {field: 0 for field in subject_fields}
    answer_confirmed_dict = {field: False for field in subject_fields}
    answer_updated_at_dict = {field: None for field in subject_fields}
    answer_all_confirmed_at = None

    for answer in old_answers:
        if answer:
            field = subject_vars[answer.sub][1]
            answer_confirmed_dict[field] = answer.is_confirmed
            answer_updated_at_dict[field] = answer.updated_at

            for idx in range(problem_count[field]):
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


def get_exam_model_data(exam, participants):
    exam_model_data = get_empty_model_data()
    if exam.participants != participants:
        exam.participants = participants
        exam_model_data['update_list'].append(exam)
        exam_model_data['update_count'] += 1
    return exam_model_data


def get_total_answer_lists_and_score_data(exam_vars: dict, qs_student, answer_official: dict) -> tuple:
    score_data = get_empty_model_data()
    subject_fields = exam_vars['subject_fields']
    score_fields = exam_vars['score_fields']  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    psat_fields = exam_vars['psat_fields']
    total_answer_lists = {field: [] for field in subject_fields}

    for student in qs_student:
        score = {field: 0 for field in score_fields}
        for field, answer in student.answer.items():
            if student.answer_confirmed[field]:
                total_answer_lists[field].append(answer)

            score_unit = 4 if field in ['heonbeob'] else 2.5
            correct_count = 0
            for idx, ans in enumerate(answer):
                correct_count += 1 if ans == answer_official[field][idx] else 0
            score[field] = correct_count * score_unit

        sum_list = [score[field] for field in psat_fields if field in score]
        score['psat_avg'] = sum(sum_list) / 3 if sum_list else 0

        add_obj_to_model_update_data(
            model_data=score_data, obj=student,
            matching_data={'score': score}, matching_fields=['score'])

    return total_answer_lists, score_data


def get_answer_count_model_data(exam_vars: dict, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    answer_count_model = exam_vars['answer_count_model']
    subject_fields = exam_vars['subject_fields']
    for field in subject_fields:
        for count in all_count_dict[field]:
            if count['count_total']:
                lookup_dict = {
                    'year': exam_vars['year'],
                    'exam': exam_vars['exam'],
                    'round': exam_vars['round'],
                    'subject': count['subject'],
                    'number': count['number'],
                }
                update_model_data(
                    model_data=answer_count_model_data,
                    model=answer_count_model, lookup=lookup_dict,
                    matching_data=count, matching_fields=matching_fields,
                )
    return answer_count_model_data


def get_statistics_data(exam, statistics):
    statistics_data = get_empty_model_data()
    if exam.statistics != statistics:
        exam.statistics = statistics
        statistics_data['update_list'].append(exam)
        statistics_data['update_count'] += 1
    return statistics_data


def get_total_answer_count_model_data(exam_vars: dict, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    answer_count_model = exam_vars['answer_count_model']
    subject_fields = exam_vars['subject_fields']
    for field in subject_fields:
        for data in all_count_dict[field]:
            lookup_dict = {
                'year': exam_vars['year'],
                'exam': exam_vars['exam'],
                'round': exam_vars['round'],
                'subject': data['subject'],
                'number': data['number'],
            }
            update_model_data(
                model_data=answer_count_model_data,
                model=answer_count_model, lookup=lookup_dict,
                matching_data=data, matching_fields=matching_fields,
            )
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
        add_obj_to_model_update_data(
            model_data=model_data, obj=obj,
            matching_data=matching_data, matching_fields=matching_fields)
    else:
        try:
            obj = model.objects.get(**lookup)
            add_obj_to_model_update_data(
                model_data=model_data, obj=obj,
                matching_data=matching_data, matching_fields=matching_fields)
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
            logger.debug(f"{obj}-{fld}:[old]{getattr(obj, fld)} [new]{matching_data[fld]}")
            setattr(obj, fld, matching_data[fld])
        model_data['update_list'].append(obj)
        model_data['update_count'] += 1


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def get_participants(exam_vars: dict, exam, qs_student):
    department_model = exam_vars['department_model']
    score_fields = exam_vars['score_fields']  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']

    qs_department = department_model.objects.filter(exam=exam_vars['exam']).order_by('id')
    department_dict = {department.name: department.id for department in qs_department}

    participants = {
        'all': {'total': {field: 0 for field in score_fields}},
        'filtered': {'total': {field: 0 for field in score_fields}},
    }
    participants['all'].update({
        d_id: {field: 0 for field in score_fields} for d_id in department_dict.values()
    })
    participants['filtered'].update({
        d_id: {field: 0 for field in score_fields} for d_id in department_dict.values()
    })

    for student in qs_student:
        d_id = department_dict[student.department]
        for field, is_confirmed in student.answer_confirmed.items():
            if is_confirmed:
                participants['all']['total'][field] += 1
                participants['all'][d_id][field] += 1

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                participants['filtered']['total'][field] += 1
                participants['filtered'][d_id][field] += 1
    return participants


def get_rank_data(exam_vars: dict, exam, qs_student) -> dict:
    score_fields = exam_vars['score_fields']  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    scores_total = get_confirmed_scores(exam_vars=exam_vars, exam=exam, qs_student=qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all'], 'department': {}},
        'filtered': {'total': scores_total['filtered'], 'department': {}},
    }

    rank_data = get_empty_model_data()
    for student in qs_student:
        scores_department = get_confirmed_scores(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student, department=student.department)
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
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
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
        exam_vars: dict, exam, qs_student, department: str | None = None
) -> dict:
    score_fields = exam_vars['score_fields']  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
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
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                scores['filtered'][field].append(student.score[field])

    sorted_scores = {
        'all': {field: sorted(scores['all'][field], reverse=True) for field in score_fields},
        'filtered': {field: sorted(scores['filtered'][field], reverse=True) for field in score_fields},
    }
    return sorted_scores


def get_statistics(exam_vars: dict, exam, qs_department, qs_student):
    score_fields = exam_vars['score_fields']  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    scores_total = get_confirmed_scores(exam_vars=exam_vars, exam=exam, qs_student=qs_student)
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
        scores_department = get_confirmed_scores(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student, department=department.name)
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
