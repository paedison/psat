import traceback
from collections import defaultdict

import django.db.utils
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models.functions import Rank

from common.constants import icon_set_new
from ... import models, utils


def get_sub_list(psat) -> list:
    if psat.exam in ['칠급', '칠예', '민경']:
        return ['언어', '자료', '상황']
    return ['헌법', '언어', '자료', '상황']


def get_subject_vars(psat) -> dict[str, tuple[str, str, int]]:
    subject_vars = {
        '헌법': ('헌법', 'subject_0', 0),
        '언어': ('언어논리', 'subject_1', 1),
        '자료': ('자료해석', 'subject_2', 2),
        '상황': ('상황판단', 'subject_3', 3),
        '평균': ('PSAT 평균', 'average', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        subject_vars.pop('헌법')
    return subject_vars


def get_field_vars(psat) -> dict[str, tuple[str, str, int]]:
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        field_vars.pop('헌법')
    return field_vars


def get_predict_psat(psat):
    try:
        return psat.predict_psat
    except ObjectDoesNotExist:
        return None


def get_answer_tab(sub_list):
    answer_tab = [
        {'id': str(idx), 'title': sub, 'answer_count': 4 if sub == '헌법' else 5}
        for idx, sub in enumerate(sub_list)
    ]
    return answer_tab


def get_answer_page_data(qs_answer_count, page_number, per_page=10):
    psat = qs_answer_count.first().problem.psat
    subject_vars = get_subject_vars(psat)
    qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

    for entry in qs_answer_count:
        if entry.subject not in qs_answer_count_group:
            qs_answer_count_group[entry.subject] = []
        qs_answer_count_group[entry.subject].append(entry)

    for subject, qs_answer_count in qs_answer_count_group.items():
        if subject not in answers_page_obj_group:
            answers_page_obj_group[subject] = []
            answers_page_range_group[subject] = []
        data_answers = get_data_answers(qs_answer_count, subject_vars)
        answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
            data_answers, page_number, per_page)

    return answers_page_obj_group, answers_page_range_group


def get_data_answers(qs_answer_count, subject_vars):
    for entry in qs_answer_count:
        sub = entry.subject
        field = subject_vars[sub][1]
        ans_official = entry.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        entry.no = entry.number
        entry.ans_official = ans_official
        entry.ans_official_circle = entry.problem.get_answer_display
        entry.ans_list = answer_official_list
        entry.field = field

        entry.rate_correct = entry.get_answer_rate(ans_official)
        entry.rate_correct_top = entry.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
        entry.rate_correct_mid = entry.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
        entry.rate_correct_low = entry.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            entry.rate_gap = entry.rate_correct_top - entry.rate_correct_low
        except TypeError:
            entry.rate_gap = None

    return qs_answer_count


def update_problem_model_for_answer_official(psat, form, file) -> tuple:
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


def update_score_model(qs_student, model_dict: dict, sub_list: list):
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
    return bulk_create_or_update(score_model, list_create, list_update, update_fields)


def update_scores(psat, qs_student, model_dict: dict):
    sub_list = get_sub_list(psat)
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = [update_score_model(qs_student, model_dict, sub_list)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_rank_model(qs_student, model_dict: dict, sub_list: list, stat_type='total'):
    rank_model = model_dict[stat_type]

    list_create = []
    list_update = []
    subject_count = len(sub_list)

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {f'rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
    annotate_dict['rank_average'] = rank_func('score__average')

    participants = qs_student.count()
    for student in qs_student:
        rank_list = qs_student.annotate(**annotate_dict)
        if stat_type == 'department':
            rank_list = rank_list.filter(category=student.category)
        target, _ = rank_model.objects.get_or_create(student=student)

        fields_not_match = [target.participants != participants]
        for row in rank_list:
            if row.id == student.id:
                for idx in range(subject_count):
                    fields_not_match.append(
                        getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}')
                    )
                fields_not_match.append(target.average != row.rank_average)

                if any(fields_not_match):
                    for idx in range(subject_count):
                        setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                    target.average = row.rank_average
                    target.participants = participants
                    list_update.append(target)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'average', 'participants']
    return bulk_create_or_update(rank_model, list_create, list_update, update_fields)


def update_ranks(psat, qs_student, model_dict: dict):
    sub_list = get_sub_list(psat)
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '등수를 업데이트했습니다.',
        False: '기존 등수와 일치합니다.',
    }
    is_updated_list = [
        update_rank_model(qs_student, model_dict, sub_list, 'total'),
        update_rank_model(qs_student, model_dict, sub_list, 'department'),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def get_data_statistics(psat):
    field_vars = get_field_vars(psat)
    qs_students = (
        models.PredictStudent.objects.filter(psat=psat)
        .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
        .annotate(
            department=F('category__department'),
            subject_0=F('score__subject_0'),
            subject_1=F('score__subject_1'),
            subject_2=F('score__subject_2'),
            subject_3=F('score__subject_3'),
            average=F('score__average'),
        )
    )

    department_list = list(
        models.PredictCategory.objects.filter(exam=psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    data_statistics = []
    score_list = {}
    for department in department_list:
        data_statistics.append({'department': department, 'participants': 0})
        score_list.update({
            department: {field: [] for field, subject_tuple in field_vars.items()}
        })

    for qs in qs_students:
        for field, subject_tuple in field_vars.items():
            score = getattr(qs, field)
            score_list['전체'][field].append(score)
            score_list[qs.department][field].append(score)

    for department, score_dict in score_list.items():
        department_idx = department_list.index(department)
        for field, scores in score_dict.items():
            sub = field_vars[field][0]
            subject = field_vars[field][1]
            participants = len(scores)

            sorted_scores = sorted(scores, reverse=True)
            max_score = top_score_10 = top_score_20 = avg_score = None
            if sorted_scores:
                max_score = sorted_scores[0]
                top_10_threshold = max(1, int(participants * 0.1))
                top_20_threshold = max(1, int(participants * 0.2))
                top_score_10 = sorted_scores[top_10_threshold - 1]
                top_score_20 = sorted_scores[top_20_threshold - 1]
                avg_score = sum(scores) / participants

            data_statistics[department_idx][field] = {
                'field': field,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'participants': participants,
                'max': max_score,
                't10': top_score_10,
                't20': top_score_20,
                'avg': avg_score,
            }
    return data_statistics


def update_statistics_model(psat, data_statistics):
    field_vars = get_field_vars(psat)
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    list_update = []
    list_create = []

    for data_stat in data_statistics:
        department = data_stat['department']
        stat_dict = {'department': department}
        for field in field_vars.keys():
            stat_dict.update({
                field: {
                    'participants': data_stat[field]['participants'],
                    'max': data_stat[field]['max'],
                    't10': data_stat[field]['t10'],
                    't20': data_stat[field]['t20'],
                    'avg': data_stat[field]['avg'],
                }
            })

        try:
            new_query = models.PredictStatistics.objects.get(psat=psat, department=department)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in stat_dict.items()
            )
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except models.PredictStatistics.DoesNotExist:
            list_create.append(models.PredictStatistics(psat=psat, **stat_dict))
    update_fields = [
        'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
    ]
    is_updated = bulk_create_or_update(models.PredictStatistics, list_create, list_update, update_fields)
    return is_updated, message_dict[is_updated]


def update_answer_count_model(model_dict, rank_type='all'):
    answer_model = model_dict['answer']
    answer_count_model = model_dict[rank_type]

    list_update = []
    list_create = []

    lookup_field = f'student__rank_total__average'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants_function = F('student__rank_total__participants')

    lookup_exp = {}
    if rank_type == 'top':
        lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
    elif rank_type == 'mid':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
    elif rank_type == 'low':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

    answer_distribution = (
        answer_model.objects.filter(**lookup_exp)
        .select_related('student', 'student__rank_total')
        .values('problem_id', 'answer')
        .annotate(count=Count('id')).order_by('problem_id', 'answer')
    )
    organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

    for entry in answer_distribution:
        problem_id = entry['problem_id']
        answer = entry['answer']
        count = entry['count']
        organized_distribution[problem_id][answer] = count

    count_fields = [
        'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
    ]
    for problem_id, answers_original in organized_distribution.items():
        answers = {'count_multiple': 0}
        for answer, count in answers_original.items():
            if answer <= 5:
                answers[f'count_{answer}'] = count
            else:
                answers['count_multiple'] = count
        answers['count_sum'] = sum(answers[fld] for fld in count_fields)

        try:
            new_query = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in answers.items()
            )
            if fields_not_match:
                for fld, val in answers.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except answer_count_model.DoesNotExist:
            list_create.append(answer_count_model(problem_id=problem_id, **answers))
    update_fields = [
        'problem_id', 'count_0', 'count_1', 'count_2', 'count_3',
        'count_4', 'count_5', 'count_multiple', 'count_sum',
    ]
    return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def update_answer_counts(model_dict):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문항분석표를 업데이트했습니다.',
        False: '기존 문항분석표 데이터와 일치합니다.',
    }
    is_updated_list = [
        update_answer_count_model(model_dict, 'all'),
        update_answer_count_model(model_dict, 'top'),
        update_answer_count_model(model_dict, 'mid'),
        update_answer_count_model(model_dict, 'low'),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


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
