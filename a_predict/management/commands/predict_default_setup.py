import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_predict.models import PsatExam, PsatAnswerCount, PsatDepartment

SUB_LIST = ['헌법', '언어', '자료', '상황']
SUBJECT_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
SCORE_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']


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

        default_problem_count = 40
        if exam_exam == '칠급':
            SUB_LIST.remove('헌법')
            SUBJECT_FIELDS.remove('heonbeob')
            SCORE_FIELDS.remove('heonbeob')
            default_problem_count = 25
        problem_count: dict[str, int] = {
            field: 25 if field == 'heonbeob' else default_problem_count for field in SUBJECT_FIELDS
        }

        if exam_exam != '프모':
            answer_count_model_data = get_answer_count_model_data(
                model=PsatAnswerCount, problem_count=problem_count, exam_info=exam_info
            )
            answer_count_matching_fields = [
                'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
                'count_0', 'count_multiple', 'count_total',
            ]
            create_or_update_model(
                model=PsatAnswerCount, update_fields=answer_count_matching_fields,
                model_data=answer_count_model_data)

            exam_model_data = get_exam_model_data(
                exam_model=PsatExam, department_model=PsatDepartment, exam_info=exam_info)
            create_or_update_model(
                model=PsatExam, update_fields=['participants'], model_data=exam_model_data)


def get_answer_count_model_data(model, problem_count: dict, exam_info: dict):
    answer_count_model_data = get_empty_model_data()
    for field, count in problem_count.items():
        for number in range(1, count + 1):
            lookup_dict = exam_info.copy()
            lookup_dict.update({
                'subject': field,
                'number': number,
            })
            matching_data = {f'count_{i}': 0 for i in range(1, 6)}
            matching_data.update({'count_0': 0, 'count_multiple': 0, 'count_total': 0})

            update_model_data(
                model_data=answer_count_model_data, model=model, lookup=lookup_dict,
                matching_data=matching_data, matching_fields=[key for key in matching_data.keys()],
            )
    return answer_count_model_data


def get_exam_model_data(exam_model, department_model, exam_info):
    exam_model_data = get_empty_model_data()

    qs_department = department_model.objects.filter(exam=exam_info['exam']).order_by('id')
    department_dict = {department.name: department.id for department in qs_department}

    participants = {
        'all': {'total': {field: 0 for field in SCORE_FIELDS}},
        'filtered': {'total': {field: 0 for field in SCORE_FIELDS}},
    }
    participants['all'].update({
        d_id: {field: 0 for field in SCORE_FIELDS} for d_id in department_dict.values()
    })
    participants['filtered'].update({
        d_id: {field: 0 for field in SCORE_FIELDS} for d_id in department_dict.values()
    })

    update_model_data(
        model_data=exam_model_data, model=exam_model, lookup=exam_info,
        matching_data={'participants': participants}, matching_fields=['participants'],
    )
    return exam_model_data


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
