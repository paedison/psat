import traceback
from collections import defaultdict
from functools import wraps
from typing import Callable

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models import QuerySet
from django.db.models.functions import Rank

from a_psat import models
from . import common_utils, get_data_utils


def get_update_messages(target: str, final_syllable=False) -> dict:
    particle_1 = '을' if final_syllable else '를'
    particle_2 = '과' if final_syllable else '와'
    return {
        None: '에러가 발생했습니다.',
        True: f'{target}{particle_1} 업데이트했습니다.',
        False: f'기존 {target}{particle_2} 일치합니다.',
    }


UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


def create_predict_answer_count_model_instances(original_psat: models.Psat) -> None:
    problems = models.Problem.objects.filter(psat=original_psat).order_by('id')
    model_list = [
        models.PredictAnswerCount,
        models.PredictAnswerCountTopRank,
        models.PredictAnswerCountMidRank,
        models.PredictAnswerCountLowRank,
    ]
    for model in model_list:
        list_create = []
        for problem in problems:
            append_list_create(model, list_create, problem=problem)
        bulk_create_or_update(model, list_create, [], [])


def create_predict_statistics_model_instances(original_psat: models.Psat) -> None:
    department_list = list(
        models.PredictCategory.objects.filter(exam=original_psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    list_create = []
    for department in department_list:
        append_list_create(
            models.PredictStatistics, list_create, psat=original_psat, department=department)
    bulk_create_or_update(models.PredictStatistics, list_create, [], [])


def update_problem_model_for_answer_official(psat: models.Psat, form, file) -> tuple[bool | None, str]:
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문제 정답을 업데이트했습니다.',
        False: '기존 정답 데이터와 일치합니다.',
    }
    list_update = []
    list_create = []

    if form.is_valid():
        df = pd.read_excel(file, sheet_name='정답', header=0, index_col=0)
        df = df.infer_objects(copy=False)
        df.fillna(value=0, inplace=True)

        for subject, rows in df.items():
            for number, answer in rows.items():
                if answer:
                    try:
                        problem = models.Problem.objects.get(psat=psat, subject=subject[0:2], number=number)
                        if problem.answer != answer:
                            problem.answer = answer
                            list_update.append(problem)
                    except models.Problem.DoesNotExist:
                        problem = models.Problem(
                            psat=psat, subject=subject, number=number, answer=answer)
                        list_create.append(problem)
                    except ValueError as error:
                        print(error)
        update_fields = ['answer']
        is_updated = bulk_create_or_update(models.Problem, list_create, list_update, update_fields)
    else:
        is_updated = None
        print(form)
    return is_updated, message_dict[is_updated]


def with_update_message(message_dict: dict):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_updated_list = func(*args, **kwargs)

            if None in is_updated_list:
                is_updated = None
            elif any(is_updated_list):
                is_updated = True
            else:
                is_updated = False

            return is_updated, message_dict[is_updated]
        return wrapper
    return decorator


@with_update_message(UPDATE_MESSAGES['score'])
def update_predict_scores(psat: models.Psat, qs_student, model_dict):
    sub_list = [sub for sub in common_utils.get_subject_vars(psat, True)]
    return [update_predict_score_model(qs_student, model_dict, sub_list)]


@with_update_message(UPDATE_MESSAGES['rank'])
def update_predict_ranks(psat: models.Psat, qs_student, model_dict):
    sub_list = [sub for sub in common_utils.get_subject_vars(psat, True)]
    return [
        update_predict_rank_model(qs_student, model_dict, sub_list, 'all', False),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'all', True),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'department', False),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'department', True),
    ]


@with_update_message(UPDATE_MESSAGES['statistics'])
def update_predict_statistics(psat: models.Psat):
    total_data, filtered_data = get_data_utils.get_predict_statistics_data(psat)
    return [
        update_predict_statistics_model(psat, total_data, False),
        update_predict_statistics_model(psat, filtered_data, True),
    ]


@with_update_message(UPDATE_MESSAGES['answer_count'])
def update_predict_answer_counts(model_dict: dict):
    return [
        update_predict_answer_count_model(model_dict, 'all', False),
        update_predict_answer_count_model(model_dict, 'top', False),
        update_predict_answer_count_model(model_dict, 'mid', False),
        update_predict_answer_count_model(model_dict, 'low', False),
        update_predict_answer_count_model(model_dict, 'all', True),
        update_predict_answer_count_model(model_dict, 'top', True),
        update_predict_answer_count_model(model_dict, 'mid', True),
        update_predict_answer_count_model(model_dict, 'low', True),
    ]


def with_bulk_create_or_update():
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            model, list_create, list_update, update_fields = func(*args, **kwargs)
            model_name = model._meta.model_name
            try:
                with transaction.atomic():
                    if list_create:
                        model.objects.bulk_create(list_create)
                        message = f'Successfully created {len(list_create)} {model_name} instances.'
                        is_updated = True
                    elif list_update:
                        model.objects.bulk_update(list_update, list(update_fields))
                        message = f'Successfully updated {len(list_update)} {model_name} instances.'
                        is_updated = True
                    else:
                        message = f'No changes were made to {model_name} instances.'
                        is_updated = False
            except django.db.utils.IntegrityError:
                traceback_message = traceback.format_exc()
                print(traceback_message)
                message = f'Error occurred.'
                is_updated = None
            print(message)
            return is_updated
        return wrapper
    return decorator


@with_bulk_create_or_update()
def update_predict_score_model(
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
        sub_list: list
):
    answer_model = model_dict['answer']
    score_model = model_dict['score']

    list_update = []
    list_create = []

    for student in qs_student:
        original_score_instance, _ = score_model.objects.get_or_create(student=student)

        score_list = []
        fields_not_match = []
        for idx, sub in enumerate(sub_list):
            problem_count = 25 if sub == '헌법' else 40
            correct_count = 0

            qs_answer = (
                answer_model.objects.filter(student=student, problem__subject=sub)
                .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
            )
            for entry in qs_answer:
                answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                correct_count += 1 if entry.answer_student in answer_correct_list else 0

            score = correct_count * 100 / problem_count
            score_list.append(score)
            fields_not_match.append(getattr(original_score_instance, f'subject_{idx}') != score)

        score_sum = sum(score_list[1:])
        average = round(score_sum / 3, 1)

        fields_not_match.append(original_score_instance.sum != score_sum)
        fields_not_match.append(original_score_instance.average != average)

        if any(fields_not_match):
            for idx, score in enumerate(score_list):
                setattr(original_score_instance, f'subject_{idx}', score)
            original_score_instance.sum = score_sum
            original_score_instance.average = average
            list_update.append(original_score_instance)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average']
    return score_model, list_create, list_update, update_fields


@with_bulk_create_or_update()
def update_predict_rank_model(
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
        sub_list: list,
        stat_type: str,
        is_filtered: bool,
):
    rank_model = model_dict[stat_type]
    prefix = ''
    if is_filtered:
        qs_student = qs_student.filter(is_filtered=is_filtered)
        prefix = 'filtered_'

    list_create = []
    list_update = []
    subject_count = len(sub_list)

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {f'{prefix}rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
    annotate_dict[f'{prefix}rank_average'] = rank_func('score__average')

    participants = qs_student.count()
    for student in qs_student:
        rank_list = qs_student.annotate(**annotate_dict)
        if stat_type == 'department':
            rank_list = rank_list.filter(category=student.category)
            participants = rank_list.count()
        target, _ = rank_model.objects.get_or_create(student=student)

        fields_not_match = [getattr(target, f'{prefix}participants') != participants]
        for row in rank_list:
            if row.id == student.id:
                for idx in range(subject_count):
                    fields_not_match.append(
                        getattr(target, f'{prefix}subject_{idx}') != getattr(row, f'{prefix}rank_{idx}')
                    )
                fields_not_match.append(
                    getattr(target, f'{prefix}average') != getattr(row, f'{prefix}rank_average')
                )

                if any(fields_not_match):
                    for idx in range(subject_count):
                        setattr(target, f'{prefix}subject_{idx}', getattr(row, f'{prefix}rank_{idx}'))
                    setattr(target, f'{prefix}average', getattr(row, f'{prefix}rank_average'))
                    setattr(target, f'{prefix}participants', participants)
                    list_update.append(target)

    update_fields = [
        f'{prefix}subject_0', f'{prefix}subject_1', f'{prefix}subject_2',
        f'{prefix}subject_3', f'{prefix}average', f'{prefix}participants'
    ]
    return rank_model, list_create, list_update, update_fields


def update_predict_statistics_model(
        psat: models.Psat,
        data_statistics,
        is_filtered: bool,
) -> tuple[bool | None, str]:
    prefix = 'filtered_' if is_filtered else ''
    message_dict = get_update_messages('통계')
    list_update = []
    list_create = []

    for data_stat in data_statistics:
        department = data_stat['department']
        stat_dict = {'department': department}
        for (_, fld, _, _) in common_utils.get_subject_vars(psat).values():
            stat_dict.update({
                f'{prefix}{fld}': {
                    'participants': data_stat[fld]['participants'],
                    'max': data_stat[fld]['max'],
                    't10': data_stat[fld]['t10'],
                    't20': data_stat[fld]['t20'],
                    'avg': data_stat[fld]['avg'],
                }
            })

        try:
            instance = models.PredictStatistics.objects.get(psat=psat, department=department)
            fields_not_match = any(
                getattr(instance, fld) != val for fld, val in stat_dict.items()
            )
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(instance, fld, val)
                list_update.append(instance)
        except models.PredictStatistics.DoesNotExist:
            list_create.append(models.PredictStatistics(psat=psat, **stat_dict))
    update_fields = [
        'department', f'{prefix}subject_0', f'{prefix}subject_1',
        f'{prefix}subject_2', f'{prefix}subject_3', f'{prefix}average',
    ]
    is_updated = bulk_create_or_update(models.PredictStatistics, list_create, list_update, update_fields)
    return is_updated, message_dict[is_updated]


@with_bulk_create_or_update()
def update_predict_answer_count_model(model_dict: dict, rank_type: str, is_filtered: bool):
    answer_model = model_dict['answer']
    answer_count_model = model_dict[rank_type]
    prefix = 'filtered_' if is_filtered else ''

    list_update = []
    list_create = []

    lookup_field = f'student__rank_total__{prefix}average'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants_function = F(f'student__rank_total__{prefix}participants')

    lookup_exp = {}
    if is_filtered:
        lookup_exp['student__is_filtered'] = is_filtered
    if rank_type == 'top':
        lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
    elif rank_type == 'mid':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
    elif rank_type == 'low':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

    qs_answer = (
        answer_model.objects.filter(**lookup_exp)
        .select_related('student', 'student__rank_total')
        .values('problem_id', 'answer')
        .annotate(count=Count('id')).order_by('problem_id', 'answer')
    )
    answer_distribution_dict = defaultdict(lambda: {i: 0 for i in range(6)})
    for qs_a in qs_answer:
        answer_distribution_dict[qs_a['problem_id']][qs_a['answer']] = qs_a['count']

    count_fields = [
        f'{prefix}count_0', f'{prefix}count_1', f'{prefix}count_2', f'{prefix}count_3',
        f'{prefix}count_4', f'{prefix}count_5', f'{prefix}count_multiple',
    ]
    for problem_id, answer_distribution in answer_distribution_dict.items():
        answers = {f'{prefix}count_multiple': 0}
        for ans, cnt in answer_distribution.items():
            if ans <= 5:
                answers[f'{prefix}count_{ans}'] = cnt
            else:
                answers[f'{prefix}count_multiple'] = cnt
        answers[f'{prefix}count_sum'] = sum(answers[fld] for fld in count_fields)

        try:
            instance = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(
                getattr(instance, fld) != val for fld, val in answers.items()
            )
            if fields_not_match:
                for fld, val in answers.items():
                    setattr(instance, fld, val)
                list_update.append(instance)
        except answer_count_model.DoesNotExist:
            list_create.append(answer_count_model(problem_id=problem_id, **answers))
    update_fields = [
        'problem_id', f'{prefix}count_0', f'{prefix}count_1', f'{prefix}count_2', f'{prefix}count_3',
        f'{prefix}count_4', f'{prefix}count_5', f'{prefix}count_multiple', f'{prefix}count_sum',
    ]
    return answer_count_model, list_create, list_update, update_fields


def append_list_create(model, list_create, **kwargs):
    try:
        model.objects.get(**kwargs)
    except model.DoesNotExist:
        list_create.append(model(**kwargs))


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated
