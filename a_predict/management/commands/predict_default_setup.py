import dataclasses

from django.core.management.base import BaseCommand

from a_predict import utils
from a_predict.views.base_info import PsatExamVars, PoliceExamVars


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

        if exam_type == 'psat':
            exam_vars = CommandPsatExamVars(exam_year, exam_exam, exam_round)
        else:
            exam_vars = CommandPoliceExamVars(exam_year, exam_exam, exam_round)

        matching_fields = exam_vars.count_fields + ['all', 'filtered']
        answer_count_model_data = get_default_answer_count_model_data(exam_vars)
        utils.create_or_update_model(exam_vars.answer_count_model, matching_fields, answer_count_model_data)

        matching_fields = ['participants', 'statistics']
        exam_model_data = get_default_exam_model_data(exam_vars, matching_fields)
        utils.create_or_update_model(exam_vars.exam_model, matching_fields, exam_model_data)


@dataclasses.dataclass
class CommandPsatExamVars(PsatExamVars):
    pass


@dataclasses.dataclass
class CommandPoliceExamVars(PoliceExamVars):
    sub_list = ['형사', '헌법', '경찰', '범죄', '민법', '행학', '행법']
    subject_list = ['형사학', '헌법', '경찰학', '범죄학', '민법총칙', '행정학', '행정법']
    subject_vars = {
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum')
    }
    subject_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob',
    ]
    score_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob', 'sum',
    ]
    answer_count_fields = [
        'count_1', 'count_2', 'count_3', 'count_4',
        'count_0', 'count_multiple', 'count_total',
    ]
    admin_score_fields = [
        'sum', 'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob',
    ]
    field_vars = {
        'hyeongsa': ('형사', '형사학'), 'heonbeob': ('헌법', '헌법'),
        'gyeongchal': ('경찰', '경찰학'), 'beomjoe': ('범죄', '범죄학'),
        'minbeob': ('민법', '민법총칙'), 'haenghag': ('행학', '행정학'),
        'haengbeob': ('행법', '행정법'), 'sum': ('총점', '총점'),
    }


def get_default_answer_count_model_data(exam_vars: CommandPsatExamVars | PoliceExamVars):
    answer_count_model_data = utils.get_empty_model_data()
    num_of_count_fields = len(exam_vars.count_fields) + 2
    rank_list = exam_vars.rank_list

    for field, count in exam_vars.problem_count.items():
        for number in range(1, count + 1):
            lookup_dict = {key: value for key, value in exam_vars.exam_info.items()}
            lookup_dict.update({'subject': field, 'number': number})

            count_dict = {
                'all': {rank: [0 for _ in range(num_of_count_fields)] for rank in rank_list},
                'filtered': {rank: [0 for _ in range(num_of_count_fields)] for rank in rank_list},
            }
            count_dict.update(lookup_dict)
            count_fields = [key for key in count_dict.keys()]

            utils.update_model_data(
                answer_count_model_data, exam_vars.answer_count_model, lookup_dict, count_dict, count_fields)
    return answer_count_model_data


def get_default_exam_model_data(exam_vars: CommandPsatExamVars | PoliceExamVars, matching_fields: list):
    exam_model_data = utils.get_empty_model_data()
    matching_data = {
        'participants': get_default_dict(exam_vars, 0),
        'statistics': get_default_dict(exam_vars, {}),
    }
    utils.update_model_data(
        exam_model_data, exam_vars.exam_model, exam_vars.exam_info, matching_data, matching_fields)
    return exam_model_data


def get_default_dict(exam_vars: CommandPsatExamVars | PoliceExamVars, default):
    score_fields = exam_vars.score_fields
    department_dict = utils.get_department_dict(exam_vars)
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
