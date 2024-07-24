import dataclasses
import traceback
from collections import Counter
from datetime import datetime

import django.db.utils
import pandas as pd
import pytz
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import prime_police_models


@dataclasses.dataclass
class CommandScorePrimePoliceExamVars:
    exam_type = 'police'
    exam_year: int
    exam_round: int
    file_name: str

    exam_model = prime_police_models.PrimePoliceExam
    student_model = prime_police_models.PrimePoliceStudent
    answer_count_model = prime_police_models.PrimePoliceAnswerCount
    exam = None

    subject_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob',
    ]
    score_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob', 'sum',
    ]
    common_subject_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']
    subject_vars = {
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
    }
    police_subject_fields = {
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    all_count_fields = count_fields + ['count_multiple', 'count_total']
    dict_score_unit = {
        'hyeongsa': 3, 'gyeongchal': 3,
        'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
        'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
    }
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'round': self.exam_round}

    @property
    def answer_official(self) -> dict[str, list]:
        df = pd.read_excel(self.file_name, sheet_name='정답', header=0, index_col=0)
        df.dropna(inplace=True)
        answer_official = {}
        for subject, answers in df.items():
            answer_official.update({self.police_subject_fields[subject]: [int(ans) for ans in answers]})
        return answer_official

    @property
    def qs_student(self):
        return self.student_model.objects.filter(**self.exam_info)

    def get_problem_info(self, field: str, number: int):
        return {
            'year': self.exam_year, 'round': self.exam_round,
            'subject': field, 'number': number,
        }


class Command(BaseCommand):
    help = 'Setup score data for prime police'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Exam year')  # 2025
        parser.add_argument('exam_round', type=str, help='Exam round')  # 1
        parser.add_argument(
            'file_name', type=str, help='Excel file containing official answers and student data ')

    def handle(self, *args, **kwargs):
        exam_year = kwargs['exam_year']
        exam_round = kwargs['exam_round']
        file_name = kwargs['file_name']

        # Set up exam_vars
        exam_vars = CommandScorePrimePoliceExamVars(exam_year, exam_round, file_name)

        self.stdout.write('================')
        self.stdout.write(f'Create or update exam_model with answer official')
        update_fields_for_exam = ['answer_official']
        create_or_update_exam_model(exam_vars, update_fields_for_exam)

        exam_vars.exam = exam_vars.exam_model.objects.get(**exam_vars.exam_info)

        self.stdout.write('================')
        self.stdout.write(f'Create or update student_model')
        update_fields_for_answer = [
            'answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        update_student_data(exam_vars, update_fields_for_answer)

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for score')
        update_fields_for_score = ['score']
        total_answer_lists = get_total_answer_lists_and_update_score(exam_vars, update_fields_for_score)

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for rank')
        update_fields_for_rank = [
            'rank', 'rank_total', 'participants_total',
            'rank_department', 'participants_department']
        update_rank_data(exam_vars, update_fields_for_rank)

        update_fields_for_new_rank = ['rank']
        update_new_rank_data(exam_vars, update_fields_for_new_rank)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for participants')
        update_fields_for_participants = ['participants']
        update_participants(exam_vars, update_fields_for_participants)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for statistics')
        update_fields_for_statistics = ['statistics']
        update_statistics(exam_vars, update_fields_for_statistics)

        self.stdout.write('================')
        self.stdout.write(f'Create or update answer_count_model')
        update_fields_for_answer_count = exam_vars.all_count_fields + ['answer']
        update_answer_count(exam_vars, update_fields_for_answer_count, total_answer_lists)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model by rank')
        total_answer_lists = get_total_answer_lists_by_category(exam_vars, exam_vars.qs_student)
        total_count_dict = get_total_count_dict_by_category(exam_vars, total_answer_lists)
        update_total_answer_count_model_data(exam_vars, ['all'], total_count_dict)


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def create_or_update_exam_model(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    exam_data = get_empty_model_data()
    matching_data = {'answer_official': exam_vars.answer_official}
    update_model_data(
        exam_data, exam_vars.exam_model, exam_vars.exam_info, matching_data, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, exam_data)


def update_student_data(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    student_data = get_empty_model_data()
    student_model = exam_vars.student_model
    df = pd.read_excel(exam_vars.file_name, sheet_name='문항별 표기', header=[0, 1])
    pd.set_option('future.no_silent_downcasting', True)

    timezone = pytz.timezone('UTC')
    now = datetime.now(timezone)
    answer_all_confirmed_at = datetime(now.year, now.month, now.day, tzinfo=timezone)

    for _, student in df.iterrows():
        name = student.loc[('name', 0)]
        serial = student.loc[('serial', 0)]
        selection = student.loc[('selection', 0)]
        password = student.loc[('password', 0)]

        answer_count = {selection: 40}
        answer_confirmed = {selection: True, 'sum': True}
        selection_cs = student.xs(selection, level=0)
        answer = {selection: selection_cs.fillna(0).infer_objects(copy=False).astype(int).tolist()}
        for field in exam_vars.common_subject_fields:
            cs = student.xs(field, level=0)
            answer[field] = cs.fillna(0).infer_objects(copy=False).astype(int).tolist()
            answer_count[field] = 40
            answer_confirmed[field] = True

        lookup = {
            'round': exam_vars.exam_round, 'name': name, 'serial': serial,
            'selection': selection, 'password': password,
        }
        student_info = {
            'round': exam_vars.exam_round, 'name': name, 'serial': serial,
            'selection': selection, 'password': password,
            'answer': answer, 'answer_count': answer_count,
            'answer_confirmed': answer_confirmed,
            'answer_all_confirmed_at': answer_all_confirmed_at,
        }
        update_model_data(student_data, student_model, lookup, student_info, update_fields)
    create_or_update_model(exam_vars.student_model, update_fields, student_data)


def get_total_answer_lists_and_update_score(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    qs_student = exam_vars.qs_student
    answer_official = exam_vars.answer_official
    score_data = get_empty_model_data()
    total_answer_lists = {field: [] for field in exam_vars.subject_fields}

    for student in qs_student:
        score = {}
        for field, answer in student.answer.items():
            total_answer_lists[field].append(answer)
            correct_count = 0
            score_unit = exam_vars.dict_score_unit.get(field, 1.5)
            for idx, ans in enumerate(answer):
                correct_count += 1 if ans == answer_official[field][idx] else 0
            score[field] = correct_count * score_unit
        score['sum'] = sum(s for s in score.values())

        add_obj_to_model_update_data(
            score_data, student, {'score': score}, update_fields)

    create_or_update_model(exam_vars.student_model, update_fields, score_data)
    return total_answer_lists


def update_rank_data(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    rank_data = get_empty_model_data()
    qs_student = exam_vars.qs_student
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
    create_or_update_model(exam_vars.student_model, update_fields, rank_data)


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


def update_new_rank_data(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    qs_student = exam_vars.qs_student
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'sum']
    scores_total = get_confirmed_scores(exam_vars, qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all'], 'department': {}},
    }
    rank_data = get_empty_model_data()
    for student in qs_student:
        rank = {'all': {'total': {field: 0 for field in score_fields}}}
        for field in score_fields:
            if field in student.score:
                score_student = student.score[field]
                if student.answer_confirmed[field]:
                    rank['all']['total'][field] = (
                            scores['all']['total'][field].index(score_student) + 1)
        if student.rank != rank:
            student.rank = rank
            rank_data['update_list'].append(student)
            rank_data['update_count'] += 1
    create_or_update_model(exam_vars.student_model, update_fields, rank_data)


def get_confirmed_scores(
        exam_vars: CommandScorePrimePoliceExamVars, qs_student) -> dict:
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'sum']
    scores = {'all': {field: [] for field in score_fields}}
    for field in score_fields:
        for student in qs_student:
            if field in student.answer_confirmed and student.answer_confirmed[field]:
                scores['all'][field].append(student.score[field])
    sorted_scores = {
        'all': {field: sorted(scores['all'][field], reverse=True) for field in score_fields},
    }
    return sorted_scores


def update_participants(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    qs_student = exam_vars.qs_student
    exam_model_data = get_empty_model_data()
    participants = {'all': {'total': {fld: 0 for fld in exam_vars.score_fields}}}
    for student in qs_student:
        for field, is_confirmed in student.answer_confirmed.items():
            if is_confirmed:
                participants['all']['total'][field] += 1
    add_obj_to_model_update_data(
        exam_model_data, exam_vars.exam, {'participants': participants}, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, exam_model_data)


def update_statistics(exam_vars: CommandScorePrimePoliceExamVars, update_fields):
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'sum']
    scores_total = get_confirmed_scores(exam_vars, exam_vars.qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all']},
    }
    statistics: dict[str, dict[str | int, dict]] = {
        'all': {
            'total': {field: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for field in score_fields},
        },
    }

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

    statistics_data = get_empty_model_data()
    add_obj_to_model_update_data(
        statistics_data, exam_vars.exam, {'statistics': statistics}, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, statistics_data)


def update_answer_count(exam_vars: CommandScorePrimePoliceExamVars, update_fields, total_answer_lists):
    answer_official = exam_vars.answer_official
    total_count: dict[str, list[dict[str, str | int]]] = {}
    for field in exam_vars.subject_fields:
        ans_official = answer_official[field] if field in answer_official else None
        total_count[field] = []
        for i in range(1, 41):
            answer = ans_official[i - 1] if ans_official else 0
            append_dict = {
                'year': exam_vars.exam_year, 'exam': '프모', 'round': exam_vars.exam_round,
                'subject': field, 'number': i, 'answer': answer,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0,
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
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(5)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                total_count[field][index].update(count_dict)

    answer_count_data = get_empty_model_data()
    for field in exam_vars.subject_fields:
        for count in total_count[field]:
            if count['count_total']:
                problem_info = exam_vars.get_problem_info(count['subject'], count['number'])
                update_model_data(
                    answer_count_data, exam_vars.answer_count_model,
                    problem_info, count, update_fields)
    create_or_update_model(exam_vars.answer_count_model, update_fields, answer_count_data)


def get_total_answer_lists_by_category(exam_vars: CommandScorePrimePoliceExamVars, qs_student):
    subject_fields = exam_vars.subject_fields
    rank_list = exam_vars.rank_list
    participants = exam_vars.exam.participants
    total_answer_lists_by_category: dict[str, dict[str, dict[str, list]]] = {
        'all': {rnk: {fld: [] for fld in subject_fields} for rnk in rank_list},
    }
    participants_all = participants['all']['total']['sum']

    for student in qs_student:
        rank_all_student = student.rank['all']['total']['sum']
        rank_ratio_all = None
        if participants_all:
            rank_ratio_all = rank_all_student / participants_all

        for field in subject_fields:
            if field in student.answer_confirmed and student.answer_confirmed[field]:
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

    return total_answer_lists_by_category


def get_total_count_dict_by_category(exam_vars: CommandScorePrimePoliceExamVars, total_answer_lists: dict):
    total_count_dict = {}
    for field in exam_vars.subject_fields:
        total_count_dict[field] = []
        for number in range(1, 41):
            problem_info = exam_vars.get_problem_info(field, number)
            problem_info['all'] = {rank: [] for rank in exam_vars.rank_list}
            total_count_dict[field].append(problem_info)

    for category, value1 in total_answer_lists.items():
        for rank, value2 in value1.items():
            for field, answer_lists in value2.items():
                if answer_lists:
                    distributions = [Counter() for _ in range(40)]
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


def update_total_answer_count_model_data(
        exam_vars: CommandScorePrimePoliceExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for field in exam_vars.subject_fields:
        for data in all_count_dict[field]:
            problem_info = exam_vars.get_problem_info(data['subject'], data['number'])
            update_model_data(
                answer_count_model_data, exam_vars.answer_count_model,
                problem_info, data, matching_fields)
    create_or_update_model(
        exam_vars.answer_count_model, ['all'], answer_count_model_data)


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
