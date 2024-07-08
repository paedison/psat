import traceback
from collections import Counter

import django.db.utils
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import (
    PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount,
    PrimePoliceExam, PrimePoliceStudent, PrimePoliceAnswerCount,
)

PSAT_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']

ONLY_PSAT_FIELDS = ['eoneo', 'jaryo', 'sanghwang']

POLICE_FIELDS = [
    'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'haengbeob', 'haenghag', 'minbeob',
    'sebeob', 'hoegye', 'sangbeob', 'gyeongje', 'tonggye', 'jaejeong',
    'jeongbo', 'sine', 'debe', 'tongsin', 'sowe',
]

PSAT_SUBJECT_FIELDS = {'헌법': 'heonbeob', '언어': 'eoneo', '자료': 'jaryo', '상황': 'sanghwang'}

POLICE_SUBJECT_FIELDS = {
    '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
    '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
    '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    '세법개론': 'sebeob', '회계학': 'hoegye',  # 세무회계 필수
    '상법총칙': 'sangbeob', '경제학': 'gyeongje', '통계학': 'tonggye', '재정학': 'jaejeong',  # 세무회계 선택
    '정보보호론': 'jeongbo', '시스템네트워크보안': 'sine',  # 사이버 필수
    '데이터베이스론': 'debe', '통신이론': 'tongsin', '소프트웨어공학': 'sowe',  # 사이버 선택

}


def get_models_and_field(exam_type: str) -> tuple:
    if exam_type == 'psat':
        return PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount, PSAT_FIELDS
    elif exam_type == 'police':
        return PrimePoliceExam, PrimePoliceStudent, PrimePoliceAnswerCount, POLICE_FIELDS
    else:
        raise Exception("exam_type should be one of 'psat' or 'police'.")


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def get_answer_official(file_name: str) -> dict[str, list]:
    df = pd.read_excel(file_name, sheet_name='정답', header=0)
    df.apply(pd.to_numeric, errors='coerce').fillna(0)
    df_filtered = df.iloc[:, 1:]

    answer_official = {}
    for subject, answers in df_filtered.items():
        answer_official.update({POLICE_SUBJECT_FIELDS[subject]: [int(ans) for ans in answers]})
    return answer_official


def create_or_update_exam_model(exam_data: dict, answer_official: dict):
    exam_model = exam_data['exam_model']
    qs_exam, created = exam_model.objects.get_or_create(year=exam_data['year'], round=exam_data['round'])
    model_name = exam_model._meta.model_name
    if created:
        qs_exam.answer_official = answer_official
        qs_exam.save()
        message = f'Successfully created {model_name} instance'
    else:
        if qs_exam.answer_official != answer_official:
            qs_exam.answer_official = answer_official
            qs_exam.save()
            message = f'Successfully updated {model_name} instance'
        else:
            message = f'No changes were made to {model_name} instances.'
    print(message)


def get_student_data(exam_data: dict) -> dict:
    student_data = get_empty_model_data()

    df = pd.read_excel(exam_data['file_name'], sheet_name='문항별 표기', header=[0, 1])
    df.apply(pd.to_numeric, errors='coerce').fillna(0)

    columns_to_keep = df.columns[:2].tolist() + df.columns[33:233].tolist()
    filtered_df = df.loc[:, columns_to_keep].fillna(0)
    labels = list(pd.unique(filtered_df.iloc[0:1, 2:].columns.get_level_values(0)))

    for _, student in filtered_df.iterrows():
        name = student.loc[('이름', 'Unnamed: 1_level_1')]
        serial = student.loc[('응시번호', 'Unnamed: 0_level_1')]
        answer = {
            POLICE_SUBJECT_FIELDS[labels[i]]:
                [int(answer) for answer in student.loc[labels[i]]] for i in range(len(labels))
        }
        answer_count = {POLICE_SUBJECT_FIELDS[labels[i]]: 40 for i in range(len(labels))}
        student_info = {
            'round': exam_data['round'],
            'name': name,
            'serial': serial,
            'answer': answer,
            'answer_count': answer_count,
        }

        try:
            target_student = PrimePoliceStudent.objects.get(
                round=exam_data['round'], name=name, serial=serial)
            fields_not_match = any([
                target_student.answer != answer,
                target_student.answer_count != answer_count
            ])
            if fields_not_match:
                target_student.answer = answer
                target_student.answer_count = answer_count
                student_data['update_list'].append(target_student)
                student_data['update_count'] += 1
        except PrimePoliceStudent.DoesNotExist:
            student_data['create_list'].append(PrimePoliceStudent(**student_info))
            student_data['create_count'] += 1
    return student_data


def get_total_answer_lists_and_score_data(exam_data: dict, qs_student, answer_official: dict) -> tuple:
    exam_type = exam_data['type']
    score_data = get_empty_model_data()
    total_answer_lists = {field: [] for field in exam_data['fields']}

    for student in qs_student:
        score = {}
        for field, answer in student.answer.items():
            total_answer_lists[field].append(answer)

            score_unit = 2.5
            if exam_type == 'psat' and field in ['heonbeob']:
                score_unit = 4
            elif exam_type == 'police':
                dict_score_unit = {
                    'hyeongsa': 3, 'gyeongchal': 3,
                    'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
                    'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
                }
                score_unit = dict_score_unit.get(field, 1.5)

            correct_count = 0
            for index, ans in enumerate(answer):
                if ans == answer_official[field][index]:
                    correct_count += 1
            score[field] = correct_count * score_unit

        if exam_type == 'psat':
            sum_list = [score[field] for field in ONLY_PSAT_FIELDS if field in score]
            score['psat_avg'] = sum(sum_list) / 3
        elif exam_type == 'police':
            score['sum'] = sum(s for s in score.values())

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


# def get_statistics_data(queryset, stat_type: str, student=None) -> dict:
#     if stat_type == 'total':
#         student = queryset.first()
#     score = {}
#     participants = {}
#     rank = {}
#
#     for field, value in student.score.items():
#         score[field] = []
#         if stat_type == 'total':
#             all_scores = queryset.values('score')
#             if field in all_scores['score'].keys():
#                 score[field].append(all_scores['score'][field])
#         else:
#             for qs in queryset:
#                 if field in qs['score'].keys():
#                     score[field].append(qs['score'][field])
#
#         participants[field] = len(score[field])
#         if field in student.score.keys():
#             sorted_score = sorted(score[field], reverse=True)
#             rank[field] = sorted_score.index(student.score[field]) + 1
#
#     return {
#         f'rank_{stat_type}': rank,
#         f'participants_{stat_type}': participants,
#     }
#
#
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
                'year': exam_data['year'], 'exam': '프모', 'round': exam_data['round'],
                'subject': field, 'number': i, 'answer': 0,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            }
            if exam_data['type'] == 'police':
                append_dict.pop('count_5')
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
                if exam_data['type'] == 'police':
                    total_count[field][index].pop('count_5')
    return total_count


def get_field_list_for_matching(exam_type: str) -> list:
    field_list_for_matching = [
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_total',
    ]
    if exam_type == 'police':
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
                        year=exam_data['year'], round=exam_data['round'],
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
        parser.add_argument('exam_type', type=str, help='Prime Exam type')  # psat, police
        parser.add_argument('year', type=str, help='Year')  # 2024
        parser.add_argument('round', type=str, help='Round')  # 1
        parser.add_argument(
            'file_name', type=str, help='Excel file containing official answers and student data ')

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['year']
        exam_round = kwargs['round']
        file_name = kwargs['file_name']

        # Set up default models, fields and empty_model_data
        exam_model, student_model, answer_count_model, fields = get_models_and_field(exam_type=exam_type)
        exam_data = {
            'type': exam_type, 'year': exam_year, 'round': exam_round, 'file_name': file_name,
            'exam_model': exam_model, 'student_model': student_model,
            'answer_count_model': answer_count_model, 'fields': fields,
        }

        # Create or update exam_model instances
        answer_official = get_answer_official(file_name=file_name)
        create_or_update_exam_model(exam_data=exam_data, answer_official=answer_official)

        # Create or update student_model instances
        student_data = get_student_data(exam_data=exam_data)
        create_or_update_model(model=student_model, update_fields=['score'], model_data=student_data)

        # Update student_model for score
        qs_student = student_model.objects.filter(year=exam_year, round=exam_round)
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

        # Create or update answer_count_model
        total_count = get_total_count(
            exam_data=exam_data,
            total_answer_lists=total_answer_lists
        )
        answer_count_matching_fields = get_field_list_for_matching(exam_type=exam_type)
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
