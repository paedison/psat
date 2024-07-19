import dataclasses
import traceback
from copy import deepcopy

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_predict.models import psat_models, police_models

SUB_LIST = ['헌법', '언어', '자료', '상황']
SUBJECT_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
SCORE_FIELDS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']


@dataclasses.dataclass
class PsatExamVars:
    exam_exam: str
    exam_info: dict = dataclasses.field(default_factory=dict)

    exam_model = psat_models.PsatExam
    department_model = psat_models.PsatDepartment
    answer_count_model = psat_models.PsatAnswerCount

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
    score_fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    answer_count_fields = [
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_total',
    ]

    @property
    def problem_count(self):
        default_count = 40
        if self.exam_exam == '칠급':
            self.sub_list.remove('헌법')
            self.subject_fields.remove('heonbeob')
            self.score_fields.remove('heonbeob')
            default_count = 25
        count: dict[str, int] = {
            fld: 25 if fld == 'heonbeob' else default_count for fld in self.subject_fields
        }
        return count


@dataclasses.dataclass
class PoliceExamVars:
    exam_info: dict = dataclasses.field(default_factory=dict)

    exam_model = police_models.PoliceExam
    department_model = police_models.PoliceDepartment
    answer_count_model = police_models.PoliceAnswerCount

    sub_list = ['형사', '헌법', '경찰', '범죄', '행법', '행학', '민법']
    subject_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'haengbeob', 'haenghag', 'minbeob',
    ]
    score_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'haengbeob', 'haenghag', 'minbeob', 'sum',
    ]
    answer_count_fields = [
        'count_1', 'count_2', 'count_3', 'count_4',
        'count_0', 'count_multiple', 'count_total',
    ]

    @property
    def problem_count(self):
        return {fld: 40 for fld in self.subject_fields}


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Year')  # psat, police
        parser.add_argument('exam_year', type=str, help='Year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam type')  # 행시
        parser.add_argument('exam_round', type=str, help='Round')  # 0

    def handle(self, *args, **options):
        exam_type = options['exam_year']
        exam_year = options['exam_year']
        exam_exam = options['exam_exam']
        exam_round = options['exam_round']

        exam_vars = PsatExamVars(exam_exam) if exam_type == 'psat' else PoliceExamVars()
        exam_vars.exam_info = {'year': exam_year, 'exam': exam_exam, 'round': exam_round}

        if exam_exam != '프모':
            answer_count_model_data = get_answer_count_model_data(exam_vars)
            create_or_update_model(
                exam_vars.answer_count_model, exam_vars.answer_count_fields, answer_count_model_data)

            exam_model_data = get_exam_model_data(exam_vars)
            create_or_update_model(exam_vars.exam_model, ['participants'], exam_model_data)


def get_answer_count_model_data(exam_vars: PsatExamVars | PoliceExamVars):
    problem_count = exam_vars.problem_count
    exam_info = exam_vars.exam_info
    model = exam_vars.answer_count_model
    answer_count_model_data = get_empty_model_data()
    answer_numbers = len(exam_vars.answer_count_fields) - 3

    for field, count in problem_count.items():
        for number in range(1, count + 1):
            lookup_dict = deepcopy(exam_info)
            lookup_dict.update({'subject': field, 'number': number})
            matching_data = {f'count_{i}': 0 for i in range(1, answer_numbers + 1)}
            matching_data.update({'count_0': 0, 'count_multiple': 0, 'count_total': 0})
            matching_data.update(lookup_dict)
            update_model_data(
                model_data=answer_count_model_data, model=model, lookup=lookup_dict,
                matching_data=matching_data, matching_fields=[key for key in matching_data.keys()],
            )
    return answer_count_model_data


def get_exam_model_data(exam_vars: PsatExamVars | PoliceExamVars):
    department_model = exam_vars.department_model
    exam_info = exam_vars.exam_info
    exam_model = exam_vars.exam_model
    score_fields = exam_vars.score_fields
    exam_model_data = get_empty_model_data()

    qs_department = department_model.objects.filter(exam=exam_info['exam']).order_by('id')
    department_dict = {department.name: department.id for department in qs_department}

    participants = {
        'all': {'total': {fld: 0 for fld in score_fields}},
        'filtered': {'total': {fld: 0 for fld in score_fields}},
    }
    participants['all'].update({
        d_id: {fld: 0 for fld in score_fields} for d_id in department_dict.values()
    })
    participants['filtered'].update({
        d_id: {fld: 0 for fld in score_fields} for d_id in department_dict.values()
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
