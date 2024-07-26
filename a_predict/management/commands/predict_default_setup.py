import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from ..command_utils import CommandPredictExamVars


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Exam type')  # psat, police
        parser.add_argument('exam_year', type=str, help='Exam year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam name')  # 행시
        parser.add_argument('exam_round', type=str, help='Exam round')  # 0

    def handle(self, *args, **options):
        exam_type = options['exam_type']
        exam_year = options['exam_year']
        exam_exam = options['exam_exam']
        exam_round = options['exam_round']

        exam_vars = CommandPredictExamVars(None, exam_type, exam_year, exam_exam, exam_round)

        self.stdout.write('================')
        self.stdout.write(f'Create or update answer_count_model default instances')
        matching_fields = exam_vars.all_count_fields + ['all', 'filtered']
        answer_count_model_data = get_default_answer_count_model_data(exam_vars)
        create_or_update_model(exam_vars.answer_count_model, matching_fields, answer_count_model_data)

        self.stdout.write('================')
        self.stdout.write(f'Create or update exam_model default instances')
        matching_fields = ['participants', 'statistics']
        exam_model_data = get_default_exam_model_data(exam_vars, matching_fields)
        create_or_update_model(exam_vars.exam_model, matching_fields, exam_model_data)


def get_default_answer_count_model_data(exam_vars: CommandPredictExamVars):
    answer_count_model_data = get_empty_model_data()
    num_of_count_fields = len(exam_vars.count_fields) + 2
    rank_list = exam_vars.rank_list

    for field, count in exam_vars.problem_count.items():
        for number in range(1, count + 1):
            problem_info = exam_vars.get_problem_info(field, number)
            count_default = {fld: 0 for fld in exam_vars.all_count_fields}
            count_default.update(problem_info)
            count_default.update({
                'all': get_count_by_rank(num_of_count_fields, rank_list),
                'filtered': get_count_by_rank(num_of_count_fields, rank_list),
            })
            count_fields = [key for key in count_default.keys()]

            update_model_data(
                answer_count_model_data, exam_vars.answer_count_model, problem_info, count_default, count_fields)
    return answer_count_model_data


def get_count_by_rank(num_fields, rank_list):
    return {rank: [0 for _ in range(num_fields)] for rank in rank_list}


def get_default_exam_model_data(exam_vars: CommandPredictExamVars, matching_fields: list):
    exam_model_data = get_empty_model_data()
    matching_data = {
        'participants': get_default_dict(exam_vars, 0),
        'statistics': get_default_dict(exam_vars, {}),
    }
    update_model_data(
        exam_model_data, exam_vars.exam_model, exam_vars.exam_info, matching_data, matching_fields)
    return exam_model_data


def get_default_dict(exam_vars: CommandPredictExamVars, default):
    score_fields = exam_vars.score_fields
    qs_department = exam_vars.get_qs_department()
    department_dict = {department.name: department.id for department in qs_department}
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
