import traceback
from collections import Counter

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from a_predict.models import PsatExam, PsatStudent, PsatAnswerCount
from predict import models as old_predict_models

PSAT_SUBJECTS = ['헌법', '언어', '자료', '상황']
PSAT_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
ONLY_PSAT_FIELDS = ['eoneo', 'jaryo', 'sanghwang']
PSAT_SUBJECT_FIELDS = {'헌법': 'heonbeob', '언어': 'eoneo', '자료': 'jaryo', '상황': 'sanghwang'}
PSAT_FIELDS_TO_SUBJECT = {'heonbeob': '헌법', 'eoneo': '언어', 'jaryo': '자료', 'sanghwang': '상황'}

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


def get_new_models_and_field(exam_exam: str) -> tuple:
    if exam_exam != '프모':
        return PsatExam, PsatStudent, PsatAnswerCount, PSAT_FIELDS
    else:
        raise Exception("exam_type should be one of 'psat' or 'police'.")


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def get_student_data(exam_data: dict) -> dict:
    student_data = get_empty_model_data()
    old_students = old_predict_models.Student.objects.filter(
        exam__ex=exam_data['exam_exam'], exam__round=exam_data['exam_round']).annotate(
        created_at=F('timestamp'),
    )
    student_model = exam_data['student_model']
    fields = exam_data['fields']

    for student in old_students:
        old_answers = [
            old_predict_models.Answer.objects.filter(student=student, sub=sub).first() for sub in PSAT_SUBJECTS
        ]
        unit = UNIT_DICT[student.unit_id]
        department = DEPARTMENT_DICT[student.department_id]

        answer_count_dict = {field: 0 for field in fields}
        answer_dict = {field: [] for field in fields}
        answer_confirmed_dict = {field: False for field in fields}
        answer_updated_at_dict = {field: None for field in fields}
        answer_all_confirmed_at = None

        for answer in old_answers:
            if answer:
                field = PSAT_SUBJECT_FIELDS[answer.sub]
                answer_confirmed_dict[field] = answer.is_confirmed
                answer_updated_at_dict[field] = answer.updated_at

                problem_count = 25 if answer.sub == '헌법' else 40
                for i in range(1, problem_count + 1):
                    ans = getattr(answer, f'prob{i}') or 0
                    if ans:
                        answer_count_dict[field] += 1
                    answer_dict[field].append(ans)

        if all([value for value in answer_confirmed_dict.values()]):
            try:
                answer_all_confirmed_at = max([value for value in answer_updated_at_dict.values()])
            except ValueError:
                pass

        student_info = {
            'user_id': student.user_id,
            'year': exam_data['exam_year'],
            'exam': exam_data['exam_exam'],
            'round': exam_data['exam_round'],

            'name': student.name,
            'serial': student.serial,
            'unit': unit,
            'department': department,

            'password': student.password,
            'prime_id': student.prime_id,

            'answer': answer_dict,
            'answer_count': answer_count_dict,
            'answer_confirmed': answer_confirmed_dict,
            'answer_all_confirmed_at': answer_all_confirmed_at,
        }

        try:
            target_student = student_model.objects.get(
                user_id=student.user_id, year=exam_data['exam_year'],
                exam=exam_data['exam_exam'],
                round=exam_data['exam_round'],
                name=student.name, serial=student.serial)
            fields_not_match = any([
                target_student.answer != answer_dict,
                target_student.answer_count != answer_count_dict,
                target_student.answer_confirmed != answer_confirmed_dict,
                target_student.answer_all_confirmed_at != answer_all_confirmed_at,
            ])
            if fields_not_match:
                target_student.answer = answer_dict
                target_student.answer_count = answer_count_dict
                target_student.answer_confirmed = answer_confirmed_dict
                target_student.answer_all_confirmed_at = answer_all_confirmed_at
                student_data['update_list'].append(target_student)
                student_data['update_count'] += 1
        except student_model.DoesNotExist:
            student_data['create_list'].append(student_model(**student_info))
            student_data['create_count'] += 1
        except student_model.MultipleObjectsReturned:
            print(student.id)
    return student_data


def get_total_answer_lists_and_score_data(exam_data: dict, qs_student, answer_official: dict) -> tuple:
    score_data = get_empty_model_data()
    total_answer_lists = {field: [] for field in exam_data['fields']}

    for student in qs_student:
        score = {}
        for field, answer in student.answer.items():
            total_answer_lists[field].append(answer)
            score_unit = 4 if field in ['heonbeob'] else 2.5

            correct_count = 0
            for index, ans in enumerate(answer):
                try:
                    if ans == answer_official[field][index]:
                        correct_count += 1
                except IndexError:
                    print(student.id)
            score[field] = correct_count * score_unit

        sum_list = [score[field] for field in ONLY_PSAT_FIELDS if field in score]
        if sum_list:
            score['psat_avg'] = sum(sum_list) / 3

        if student.score != score:
            student.score = score
            score_data['update_list'].append(student)
            score_data['update_count'] += 1

    return total_answer_lists, score_data


def get_statistics_data(qs_student, stat_type: str, student=None) -> dict:
    score = {}
    participants = {}
    rank = {}

    queryset = qs_student.values('score')
    if stat_type == 'department':
        queryset = qs_student.filter(department=student.department).values('score')

    for field, value in student.score.items():
        score[field] = []
        for qs in queryset:
            if field in qs['score']:
                score[field].append(qs['score'][field])

        participants[field] = len(score[field])
        if field in student.score:
            sorted_score = sorted(score[field], reverse=True)
            rank[field] = sorted_score.index(student.score[field]) + 1

    return {
        f'rank_{stat_type}': rank,
        f'participants_{stat_type}': participants,
    }


def get_rank_data(qs_student) -> dict:
    rank_data = get_empty_model_data()
    for student in qs_student:
        stat_dict = get_statistics_data(qs_student=qs_student, stat_type='total', student=student)
        qs_all_score_department = qs_student.filter(department=student.department)
        stat_dict.update(
            get_statistics_data(qs_student=qs_all_score_department, stat_type='department', student=student)
        )
        fields_not_match = any(getattr(student, fld) != val for fld, val in stat_dict.items())
        if fields_not_match:
            for fld, val in stat_dict.items():
                setattr(student, fld, val)
            rank_data['update_list'].append(student)
            rank_data['update_count'] += 1
    return rank_data


def get_total_count(exam_data: dict, total_answer_lists: dict) -> dict:
    total_count: dict[str, list[dict[str, str | int]]] = {}
    for field in exam_data['fields']:
        total_count[field] = []
        for i in range(1, 41):
            append_dict = {
                'year': exam_data['exam_year'], 'exam': exam_data['exam_exam'], 'round': exam_data['exam_round'],
                'subject': field, 'number': i, 'answer': 0,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            }
            total_count[field].append(append_dict)
    for field, answer_lists in total_answer_lists.items():
        if answer_lists:
            distributions = [Counter() for _ in range(40)]
            for lst in answer_lists:
                for i, value in enumerate(lst):
                    if value > 5:
                        distributions[i]['count_multiple'] += 1
                    else:
                        distributions[i][value] += 1

            for index, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                total_count[field][index].update(count_dict)
    return total_count


def get_field_list_for_matching(exam: str) -> list:
    field_list_for_matching = [
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_total',
    ]
    if exam == 'police':
        field_list_for_matching.remove('count_5')
    return field_list_for_matching


def get_answer_count_data(exam_data: dict, matching_fields: list, total_count: dict):
    answer_count_data = get_empty_model_data()
    model = exam_data['answer_count_model']
    for field in exam_data['fields']:
        for c in total_count[field]:
            if c['count_total']:
                try:
                    obj = model.objects.get(
                        year=exam_data['exam_year'],
                        exam=exam_data['exam_exam'],
                        round=exam_data['exam_round'],
                        subject=c['subject'], number=c['number'])
                    fields_not_match = any(
                        getattr(obj, fld) != c[fld] for fld in matching_fields)
                    if fields_not_match:
                        for fld in matching_fields:
                            setattr(obj, fld, c[fld])
                        answer_count_data['update_list'].append(obj)
                        answer_count_data['update_count'] += 1
                except model.DoesNotExist:
                    answer_count_data['create_list'].append(model(**c))
                    answer_count_data['create_count'] += 1
    return answer_count_data


def create_or_update_model(
        model,
        update_fields: list,
        model_data: dict,
):
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

        # Set up default models, fields and empty_model_data
        exam_model, student_model, answer_count_model, fields = get_new_models_and_field(exam_exam=exam_exam)
        exam_data = {
            'exam_year': exam_year, 'exam_exam': exam_exam, 'exam_round': exam_round,
            'exam_model': exam_model, 'student_model': student_model,
            'answer_count_model': answer_count_model, 'fields': fields,
        }

        answer_official = PsatExam.objects.get(year=exam_year, exam=exam_exam, round=exam_round).answer_official

        # Create or update student_model instances
        student_data = get_student_data(exam_data=exam_data)
        student_update_fields = ['answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        create_or_update_model(
            model=student_model, update_fields=student_update_fields, model_data=student_data)

        # Update student_model for score
        qs_student = student_model.objects.filter(year=exam_year, exam=exam_exam, round=exam_round)
        total_answer_lists, score_data = get_total_answer_lists_and_score_data(
            exam_data=exam_data,
            qs_student=qs_student,
            answer_official=answer_official,
        )
        create_or_update_model(model=student_model, update_fields=['score'], model_data=score_data)

        # Update student_model for rank
        rank_data = get_rank_data(qs_student=qs_student)
        rank_matching_fields_for = [
            'rank_total', 'participants_total', 'rank_department', 'participants_department']
        create_or_update_model(
            model=student_model,
            update_fields=rank_matching_fields_for,
            model_data=rank_data,
        )

        # Create or update student_model for answer count
        total_count = get_total_count(
            exam_data=exam_data,
            total_answer_lists=total_answer_lists
        )
        answer_count_matching_fields = [
            'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
            'count_0', 'count_multiple', 'count_total',
        ]
        answer_count_data = get_answer_count_data(
            exam_data=exam_data,
            matching_fields=answer_count_matching_fields,
            total_count=total_count,
        )
        create_or_update_model(
            model=answer_count_model,
            update_fields=answer_count_matching_fields,
            model_data=answer_count_data,
        )
