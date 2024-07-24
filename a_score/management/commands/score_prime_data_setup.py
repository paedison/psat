import traceback
from collections import Counter

import django.db.utils
import django.db.utils
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from ..exam_vars import CommandScoreExamVars


class Command(BaseCommand):
    help = 'Setup score data for prime'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Exam type')  # psat, police
        parser.add_argument('exam_year', type=str, help='Exam year')  # 2025
        parser.add_argument('exam_round', type=str, help='Exam round')  # 1
        parser.add_argument(
            'file_name', type=str, help='Excel file containing official answers and student data ')

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = int(kwargs['exam_year'])
        exam_round = int(kwargs['exam_round'])
        file_name = kwargs['file_name']

        # Set up exam_vars
        exam_vars = CommandScoreExamVars(exam_type, exam_year, exam_round, file_name)

        self.stdout.write('================')
        self.stdout.write(f'Create or update exam_model with answer official')
        create_or_update_exam_model(exam_vars, ['answer_official'])

        self.stdout.write('================')
        self.stdout.write(f'Create or update student_model for data(answer)')
        answer_lists = update_student_model_for_data(exam_vars, ['data'])

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for data(score)')
        score_lists = update_student_model_for_score(exam_vars, ['data'])

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for rank')
        update_student_model_for_rank(exam_vars, score_lists, ['rank'])

        self.stdout.write('================')
        self.stdout.write('Update exam_model for participants')
        update_exam_model_for_participants(exam_vars, ['participants'])

        self.stdout.write('================')
        self.stdout.write('Update exam_model for statistics')
        update_exam_model_for_statistics(exam_vars, score_lists, ['statistics'])

        self.stdout.write('================')
        self.stdout.write(f'Create or update answer_count_model')
        update_fields_for_answer_count = exam_vars.all_count_fields + ['answer']
        update_answer_count_model(exam_vars, update_fields_for_answer_count, answer_lists)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model by rank')
        answer_lists_by_category = get_answer_lists_by_category(exam_vars)
        all_count_dict = get_total_count_dict_by_category(exam_vars, answer_lists_by_category)
        update_answer_count_model_by_rank(exam_vars, all_count_dict, ['all'])


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def create_or_update_exam_model(exam_vars: CommandScoreExamVars, update_fields: list):
    exam_data = get_empty_model_data()
    exam_info = exam_vars.exam_info
    exam_info['answer_official'] = exam_vars.get_answer_official()
    update_model_data(exam_data, exam_vars.exam_model, exam_info, exam_info, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, exam_data)


def update_student_model_for_data(exam_vars: CommandScoreExamVars, update_fields: list):
    student_data = get_empty_model_data()
    answer_lists: dict[str, list] = {fld: [] for fld in exam_vars.all_answer_fields}

    df = pd.read_excel(exam_vars.file_name, sheet_name='문항별 표기', header=[0, 1])
    pd.set_option('future.no_silent_downcasting', True)
    df[('name', 0)] = df[('name', 0)].fillna('noname').astype('string')
    df[('department', 0)] = df[('department', 0)].fillna('noname').astype('string')
    df[('password', 0)] = df[('password', 0)].fillna(0).astype('int32')

    for _, student in df.iterrows():
        name = student.loc[('name', 0)] or 'noname'
        serial = student.loc[('serial', 0)] or ''
        password = student.loc[('password', 0)]

        student_score_fields = None
        student_info = {'name': name, 'serial': serial, 'password': password}
        if exam_vars.is_psat:
            student_info['department'] = student.loc[('department', 0)]
            student_score_fields = exam_vars.psat_all_score_fields
        if exam_vars.is_police:
            selection = student.loc[('selection', 0)]
            student_info['selection'] = selection
            student_score_fields = exam_vars.get_police_student_score_fields(selection)

        data = [[fld, True, 0, []] for fld in student_score_fields]
        for idx, fld in enumerate(student_score_fields[:-1]):
            subject = exam_vars.get_subject_name(fld)
            cs = student.xs(subject, level=0)
            answer_student = cs.fillna(0).infer_objects(copy=False).astype(int).tolist()

            data[idx][-1] = answer_student
            answer_lists[fld].append(answer_student)

        lookup = dict(exam_vars.exam_info, **student_info)
        update_info = dict(lookup, **{'data': data})
        update_fields = [key for key in update_info.keys()]
        update_model_data(student_data, exam_vars.student_model, lookup, update_info, update_fields)

    create_or_update_model(exam_vars.student_model, update_fields, student_data)
    return answer_lists


def update_student_model_for_score(exam_vars: CommandScoreExamVars, update_fields: list):
    score_data = get_empty_model_data()
    qs_student = exam_vars.qs_student
    answer_official = exam_vars.exam.answer_official
    score_lists: dict[str, dict[str, list]] = {
        'total': {fld: [] for fld in exam_vars.all_score_fields}
    }
    score_lists.update({
        dep: {fld: [] for fld in exam_vars.all_score_fields}
        for dep in exam_vars.all_departments
    })

    for student in qs_student:
        score_sum = 0
        score_final = 0
        for dt in student.data[:-1]:
            correct_count = 0
            score_unit = exam_vars.get_score_unit(dt[0])
            for idx, ans_student in enumerate(dt[-1]):
                ans_official = answer_official[dt[0]][idx]
                if 1 <= ans_official <= 5:
                    is_correct = ans_student == ans_official
                else:
                    ans_official_list = [int(digit) for digit in str(ans_official)]
                    is_correct = ans_student in ans_official_list
                correct_count += 1 if is_correct else 0

            score = correct_count * score_unit
            dt[2] = score
            score_lists['total'][dt[0]].append(score)
            score_lists[student.department][dt[0]].append(score)

            if exam_vars.is_psat:
                score_sum += score if dt[0] != 'heonbeob' else 0
            elif exam_vars.is_police:
                score_sum += score

        if exam_vars.is_psat:
            score_final = round(score_sum / 3, 1)
        elif exam_vars.is_police:
            score_final = score_sum
        student.data[-1][2] = score_final
        score_lists['total'][exam_vars.final_field].append(score_final)
        score_lists[student.department][exam_vars.final_field].append(score_final)

        score_data['update_list'].append(student)
        score_data['update_count'] += 1

    create_or_update_model(exam_vars.student_model, update_fields, score_data)
    return score_lists


def update_student_model_for_rank(
        exam_vars: CommandScoreExamVars, score_lists: dict, update_fields: list):
    rank_data = get_empty_model_data()
    for student in exam_vars.qs_student:
        rank = {
            'total': {fld: 0 for fld in exam_vars.all_score_fields},
            'department': {fld: 0 for fld in exam_vars.all_score_fields},
        }
        for idx, fld in enumerate(exam_vars.all_score_fields):
            for dt in student.data:
                if fld == dt[0]:
                    rank['total'][fld] = (score_lists['total'][fld].index(dt[2]) + 1)
                    rank['department'][fld] = (score_lists[student.department][fld].index(dt[2]) + 1)
        add_obj_to_model_update_data(
            rank_data, student, {'rank': rank}, update_fields)

    create_or_update_model(exam_vars.student_model, update_fields, rank_data)


def update_exam_model_for_participants(exam_vars: CommandScoreExamVars, update_fields: list):
    exam_model_data = get_empty_model_data()
    participants = {'total': 0}
    participants.update({d_id: 0 for d_id, _ in enumerate(exam_vars.all_departments)})

    for student in exam_vars.qs_student:
        d_id = exam_vars.all_departments.index(student.department)
        participants['total'] += 1
        participants[d_id] += 1
    add_obj_to_model_update_data(
        exam_model_data, exam_vars.exam, {'participants': participants}, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, exam_model_data)


def update_exam_model_for_statistics(
        exam_vars: CommandScoreExamVars, all_score_lists: dict, update_fields: list):
    statistics: dict[str, dict[str | int, dict]] = {
        'total': {fld: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for fld in exam_vars.all_score_fields},
    }
    statistics.update({
        dep: {
            fld: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for fld in exam_vars.all_score_fields
        } for dep in exam_vars.all_departments
    })

    for dep, val in all_score_lists.items():
        for fld, score_list in val.items():
            participants = len(score_list)
            top_10 = max(1, int(participants * 0.1))
            top_20 = max(1, int(participants * 0.2))

            if score_list:
                statistics[dep][fld]['max'] = round(score_list[0], 1)
                statistics[dep][fld]['t10'] = round(score_list[top_10 - 1], 1)
                statistics[dep][fld]['t20'] = round(score_list[top_20 - 1], 1)
                statistics[dep][fld]['avg'] = round(
                    sum(score_list) / participants if participants else 0, 1)

    statistics_data = get_empty_model_data()
    add_obj_to_model_update_data(
        statistics_data, exam_vars.exam, {'statistics': statistics}, update_fields)
    create_or_update_model(exam_vars.exam_model, update_fields, statistics_data)


def update_answer_count_model(
        exam_vars: CommandScoreExamVars, update_fields: list, total_answer_lists: dict):
    answer_official = exam_vars.exam.answer_official
    total_count: dict[str, list[dict[str, str | int]]] = {}

    for fld in exam_vars.all_answer_fields:
        ans_official = answer_official[fld] if fld in answer_official else None
        total_count[fld] = []
        problem_count = exam_vars.get_problem_count(fld)
        for i in range(1, problem_count + 1):
            answer = ans_official[i - 1] if ans_official else 0
            problem_info = exam_vars.get_problem_info(fld, i)
            count_fields_info = {fld: 0 for fld in exam_vars.all_count_fields}
            append_dict = dict(problem_info, **count_fields_info, **{'answer': answer})
            total_count[fld].append(append_dict)

    for fld, answer_lists in total_answer_lists.items():
        if answer_lists:
            problem_count = exam_vars.get_problem_count(fld)
            distributions = [Counter() for _ in range(problem_count)]
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
                total_count[fld][index].update(count_dict)

    answer_count_data = get_empty_model_data()
    for fld in exam_vars.all_answer_fields:
        for cnt in total_count[fld]:
            if cnt['count_total']:
                problem_info = exam_vars.get_problem_info(cnt['subject'], cnt['number'])
                update_model_data(
                    answer_count_data, exam_vars.answer_count_model,
                    problem_info, cnt, update_fields)
    create_or_update_model(exam_vars.answer_count_model, update_fields, answer_count_data)


def get_answer_lists_by_category(exam_vars: CommandScoreExamVars):
    answer_lists_by_category: dict[str, dict[str, list]] = {
        rnk: {fld: [] for fld in exam_vars.all_answer_fields} for rnk in exam_vars.rank_list
    }
    participants = exam_vars.exam.participants['total']

    for student in exam_vars.qs_student:
        rank_student = student.rank['total'][exam_vars.final_field]
        rank_ratio = None
        if participants:
            rank_ratio = rank_student / participants

        for idx, fld in enumerate(exam_vars.all_answer_fields):
            ans_student = student.data[idx][-1]
            top_rank_threshold = 0.27
            mid_rank_threshold = 0.73

            def append_answer(rnk: str):
                answer_lists_by_category[rnk][fld].append(ans_student)

            append_answer('all_rank')
            if rank_ratio and 0 <= rank_ratio <= top_rank_threshold:
                append_answer('top_rank')
            elif rank_ratio and top_rank_threshold < rank_ratio <= mid_rank_threshold:
                append_answer('mid_rank')
            elif rank_ratio and mid_rank_threshold < rank_ratio <= 1:
                append_answer('low_rank')

    return answer_lists_by_category


def get_total_count_dict_by_category(exam_vars: CommandScoreExamVars, total_answer_lists: dict):
    total_count_dict: dict[str, list[dict]] = {}
    for fld in exam_vars.all_answer_fields:
        total_count_dict[fld] = []
        for number in range(1, 41):
            problem_info = exam_vars.get_problem_info(fld, number)
            problem_info['all'] = {rank: [] for rank in exam_vars.rank_list}
            total_count_dict[fld].append(problem_info)

    for rank, value2 in total_answer_lists.items():
        for fld, answer_lists in value2.items():
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
                    total_count_dict[fld][idx]['all'][rank] = count_list

    return total_count_dict


def update_answer_count_model_by_rank(
        exam_vars: CommandScoreExamVars, all_count_dict: dict, matching_fields: list):
    answer_count_model_data = get_empty_model_data()
    for fld in exam_vars.all_answer_fields:
        for data in all_count_dict[fld]:
            problem_info = exam_vars.get_problem_info(data['subject'], data['number'])
            update_model_data(
                answer_count_model_data, exam_vars.answer_count_model,
                problem_info, data, matching_fields)
    create_or_update_model(exam_vars.answer_count_model, ['all'], answer_count_model_data)


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
