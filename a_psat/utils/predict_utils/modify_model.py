from collections import defaultdict

import pandas as pd
from django.db.models import Count, Window, F, QuerySet
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404

from a_psat import models
from a_psat.utils.predict_utils.get_data import get_admin_statistics_data
from a_psat.utils.variables import *
from common.utils.decorators import *
from common.utils.modify_models_methods import *

UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@for_normal_views
@with_bulk_create_or_update()
def create_normal_confirmed_answers(
        student: models.PredictStudent, sub: str, answer_data: list):
    list_create, list_update = [], []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(psat=student.psat, subject=sub, number=no)
        list_create.append(models.PredictAnswer(student=student, problem=problem, answer=ans))
    return models.PredictAnswer, list_create, list_update, []


@for_normal_views
def update_normal_answer_counts_after_confirm(
        qs_answer_count: QuerySet[models.PredictAnswerCount],
        psat: models.Psat,
        answer_data: list,
) -> None:
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
        if not psat.predict_psat.is_answer_official_opened:
            setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
        qs_ac.save()


@for_normal_views
def update_normal_statistics_after_confirm(
        student: models.PredictStudent,
        subject_field: str,
        answer_all_confirmed: bool
) -> None:
    predict_psat = student.psat.predict_psat

    def get_statistics_and_edit_participants(department: str):
        stat = get_object_or_404(models.PredictStatistics, psat=student.psat, department=department)

        # Update participants for each subject [All, Filtered]
        getattr(stat, subject_field)['participants'] += 1
        if not predict_psat.is_answer_official_opened:
            getattr(stat, f'filtered_{subject_field}')['participants'] += 1

        # Update participants for average [All, Filtered]
        if answer_all_confirmed:
            stat.average['participants'] += 1
            if not predict_psat.is_answer_official_opened:
                stat.filtered_average['participants'] += 1
                student.is_filtered = True
                student.save()
        stat.save()

    get_statistics_and_edit_participants('전체')
    get_statistics_and_edit_participants(student.department)


@for_normal_views
def update_normal_score_for_each_student(
        qs_answer: QuerySet[models.PredictAnswer],
        subject_field: str,
        sub: str
) -> None:
    student = qs_answer.first().student
    score = student.score
    correct_count = 0
    for qs_a in qs_answer:
        correct_count += 1 if qs_a.answer_student == qs_a.answer_correct else 0

    problem_count = get_subject_vars(student.psat)[sub][3]
    score_point = correct_count * 100 / problem_count
    setattr(score, subject_field, score_point)

    score_list = [sco for sco in [score.subject_1, score.subject_2, score.subject_3] if sco is not None]
    score_sum = sum(score_list) if score_list else None
    score_average = round(score_sum / 3, 1) if score_sum else None

    score.sum = score_sum
    score.average = score_average
    score.save()


@for_normal_views
def update_normal_rank_for_each_student(
        qs_student: QuerySet[models.PredictStudent],
        student: models.PredictStudent,
        subject_field: str,
        field_idx: int,
        stat_type: str
) -> None:
    field_average = 'average'

    rank_model = models.PredictRankTotal
    if stat_type == 'department':
        rank_model = models.PredictRankCategory

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {
        f'rank_{field_idx}': rank_func(f'score__{subject_field}'),
        'rank_average': rank_func(f'score__{field_average}')
    }

    rank_list = qs_student.annotate(**annotate_dict)
    if stat_type == 'department':
        rank_list = rank_list.filter(category=student.category)
    participants = rank_list.count()

    target, _ = rank_model.objects.get_or_create(student=student)
    fields_not_match = [target.participants != participants]

    for entry in rank_list:
        if entry.id == student.id:
            score_for_field = getattr(entry, f'rank_{field_idx}')
            score_for_average = getattr(entry, f'rank_average')
            fields_not_match.append(getattr(target, subject_field) != score_for_field)
            fields_not_match.append(target.average != entry.rank_average)

            if any(fields_not_match):
                target.participants = participants
                setattr(target, subject_field, score_for_field)
                setattr(target, field_average, score_for_average)
                target.save()


@for_admin_views
def create_admin_answer_count_model_instances(original_psat: models.Psat) -> None:
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


@for_admin_views
@with_bulk_create_or_update()
def create_admin_statistics_model_instances(original_psat: models.Psat):
    department_list = list(
        models.PredictCategory.objects.filter(exam=original_psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    list_create = []
    for department in department_list:
        append_list_create(models.PredictStatistics, list_create, psat=original_psat, department=department)
    return models.PredictStatistics, list_create, [], []


@for_admin_views
def update_admin_problem_model_for_answer_official(psat: models.Psat, form, file) -> tuple[bool | None, str]:
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '정답을 업데이트했습니다.',
        False: '기존 정답과 일치합니다.',
    }
    list_create, list_update = [], []

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


@for_admin_views
@with_update_message(UPDATE_MESSAGES['score'])
def update_admin_scores(psat: models.Psat, qs_student, model_dict):
    sub_list = [sub for sub in get_subject_vars(psat, True)]
    return [update_admin_score_model(qs_student, model_dict, sub_list)]


@for_admin_views
@with_update_message(UPDATE_MESSAGES['rank'])
def update_admin_ranks(psat: models.Psat, qs_student, model_dict):
    sub_list = [sub for sub in get_subject_vars(psat, True)]
    return [
        update_admin_rank_model(qs_student, model_dict, sub_list, 'all', False),
        update_admin_rank_model(qs_student, model_dict, sub_list, 'all', True),
        update_admin_rank_model(qs_student, model_dict, sub_list, 'department', False),
        update_admin_rank_model(qs_student, model_dict, sub_list, 'department', True),
    ]


@for_admin_views
@with_update_message(UPDATE_MESSAGES['statistics'])
def update_admin_statistics(psat: models.Psat):
    total_data, filtered_data = get_admin_statistics_data(psat)
    return [
        update_admin_statistics_model(psat, total_data, False),
        update_admin_statistics_model(psat, filtered_data, True),
    ]


@for_admin_views
@with_update_message(UPDATE_MESSAGES['answer_count'])
def update_admin_answer_counts(model_dict: dict):
    return [
        update_admin_answer_count_model(model_dict, 'all', False),
        update_admin_answer_count_model(model_dict, 'top', False),
        update_admin_answer_count_model(model_dict, 'mid', False),
        update_admin_answer_count_model(model_dict, 'low', False),
        update_admin_answer_count_model(model_dict, 'all', True),
        update_admin_answer_count_model(model_dict, 'top', True),
        update_admin_answer_count_model(model_dict, 'mid', True),
        update_admin_answer_count_model(model_dict, 'low', True),
    ]


@for_admin_views
@with_bulk_create_or_update()
def update_admin_score_model(
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
        sub_list: list
):
    answer_model = model_dict['answer']
    score_model = model_dict['score']
    list_create, list_update = [], []

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


@for_admin_views
@with_bulk_create_or_update()
def update_admin_rank_model(
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


@for_admin_views
def update_admin_statistics_model(
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
        for (_, fld, _, _) in get_subject_vars(psat).values():
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


@for_admin_views
@with_bulk_create_or_update()
def update_admin_answer_count_model(model_dict: dict, rank_type: str, is_filtered: bool):
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
