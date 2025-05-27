import io
from collections import defaultdict

import pandas as pd
from django.db.models import Count, Window, F, QuerySet
from django.db.models.functions import Rank
from django.http import HttpResponse

from a_psat import models
from common.utils import get_paginator_context
from . import common_utils


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
            common_utils.append_list_create(model, list_create, problem=problem)
        common_utils.bulk_create_or_update(model, list_create, [], [])


def create_predict_statistics_model_instances(original_psat: models.Psat) -> None:
    department_list = list(
        models.PredictCategory.objects.filter(exam=original_psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    list_create = []
    for department in department_list:
        common_utils.append_list_create(
            models.PredictStatistics, list_create, psat=original_psat, department=department)
    common_utils.bulk_create_or_update(models.PredictStatistics, list_create, [], [])


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
        is_updated = common_utils.bulk_create_or_update(models.Problem, list_create, list_update, update_fields)
    else:
        is_updated = None
        print(form)
    return is_updated, message_dict[is_updated]


def update_predict_scores(
        psat:models.Psat,
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
) -> tuple[bool | None, str]:
    sub_list = [sub for sub in common_utils.get_subject_vars(psat, True)]
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = [update_predict_score_model(qs_student, model_dict, sub_list)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_predict_score_model(
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
        sub_list: list
) -> bool | None:
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
    return common_utils.bulk_create_or_update(score_model, list_create, list_update, update_fields)


def update_predict_ranks(
        psat: models.Psat,
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict
) -> tuple[bool | None, str]:
    sub_list = [sub for sub in common_utils.get_subject_vars(psat, True)]
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '등수를 업데이트했습니다.',
        False: '기존 등수와 일치합니다.',
    }
    is_updated_list = [
        update_predict_rank_model(qs_student, model_dict, sub_list, 'all', False),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'all', True),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'department', False),
        update_predict_rank_model(qs_student, model_dict, sub_list, 'department', True),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_predict_rank_model(
        qs_student: QuerySet[models.PredictStudent],
        model_dict: dict,
        sub_list: list,
        stat_type: str,
        is_filtered: bool,
) -> bool | None:
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
    return common_utils.bulk_create_or_update(rank_model, list_create, list_update, update_fields)


def update_predict_statistics(psat: models.Psat) -> tuple[bool | None, str]:
    total_data, filtered_data = get_predict_statistics_data(psat)
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    is_updated_list = [
        update_predict_statistics_model(psat, total_data, False),
        update_predict_statistics_model(psat, filtered_data, True),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_predict_statistics_model(
        psat: models.Psat,
        data_statistics,
        is_filtered: bool,
) -> tuple[bool | None, str]:
    prefix = 'filtered_' if is_filtered else ''

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
    is_updated = common_utils.bulk_create_or_update(models.PredictStatistics, list_create, list_update, update_fields)
    return is_updated, message_dict[is_updated]


def update_predict_answer_counts(model_dict: dict) -> tuple[bool | None, str]:
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문항분석표를 업데이트했습니다.',
        False: '기존 문항분석표 데이터와 일치합니다.',
    }
    is_updated_list = [
        update_predict_answer_count_model(model_dict, 'all', False),
        update_predict_answer_count_model(model_dict, 'top', False),
        update_predict_answer_count_model(model_dict, 'mid', False),
        update_predict_answer_count_model(model_dict, 'low', False),
        update_predict_answer_count_model(model_dict, 'all', True),
        update_predict_answer_count_model(model_dict, 'top', True),
        update_predict_answer_count_model(model_dict, 'mid', True),
        update_predict_answer_count_model(model_dict, 'low', True),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_predict_answer_count_model(model_dict: dict, rank_type: str, is_filtered: bool) -> bool | None:
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
    return common_utils.bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def get_predict_only_answer_context(queryset: QuerySet, subject_vars: dict) -> dict:
    query_dict = defaultdict(list)
    for query in queryset.order_by('id'):
        query_dict[query.subject].append(query)
    return {
        sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
        for sub, (_, _, idx, _) in subject_vars.items()
    }


def get_predict_statistics_context(psat: models.Psat, page_number=1, per_page=10) -> dict:
    total_data, filtered_data = get_predict_statistics_data(psat)
    total_context = get_paginator_context(total_data, page_number, per_page)
    filtered_context = get_paginator_context(filtered_data, page_number, per_page)
    total_context.update({
        'id': '0', 'title': '전체', 'prefix': 'TotalStatistics', 'header': 'total_statistics_list',
    })
    filtered_context.update({
        'id': '1', 'title': '필터링', 'prefix': 'FilteredStatistics', 'header': 'filtered_statistics_list',
    })
    return {'total': total_context, 'filtered': filtered_context}


def get_predict_statistics_data(psat: models.Psat) -> tuple[list, list]:
    subject_vars = common_utils.get_subject_vars(psat)

    department_list = list(
        models.PredictCategory.objects.filter(exam=psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    total_data, filtered_data = defaultdict(dict), defaultdict(dict)
    total_scores, filtered_scores = defaultdict(dict), defaultdict(dict)
    for department in department_list:
        total_data[department] = {'department': department, 'participants': 0}
        filtered_data[department] = {'department': department, 'participants': 0}
        total_scores[department] = {sub: [] for sub in subject_vars}
        filtered_scores[department] = {sub: [] for sub in subject_vars}

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
    for qs_s in qs_students:
        for sub, (_,field, _, _) in subject_vars.items():
            score = getattr(qs_s, field)
            if score is not None:
                total_scores['전체'][sub].append(score)
                total_scores[qs_s.department][sub].append(score)
                if qs_s.is_filtered:
                    filtered_scores['전체'][sub].append(score)
                    filtered_scores[qs_s.department][sub].append(score)

    update_predict_statistics_data(total_data, subject_vars, total_scores)
    update_predict_statistics_data(filtered_data, subject_vars, filtered_scores)

    return list(total_data.values()), list(filtered_data.values())


def update_predict_statistics_data(
        data_statistics: dict,
        subject_vars: dict,
        score_list: dict,
) -> None:
    for department, score_dict in score_list.items():
        for sub, scores in score_dict.items():
            subject, field, _, _ = subject_vars[sub]
            participants = len(scores)

            sorted_scores = sorted(scores, reverse=True)
            max_score = top_score_10 = top_score_20 = avg_score = None
            if sorted_scores:
                max_score = sorted_scores[0]
                top_10_threshold = max(1, int(participants * 0.1))
                top_20_threshold = max(1, int(participants * 0.2))
                top_score_10 = sorted_scores[top_10_threshold - 1]
                top_score_20 = sorted_scores[top_20_threshold - 1]
                avg_score = round(sum(scores) / participants, 1)

            data_statistics[department][field] = {
                'field': field,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'participants': participants,
                'max': max_score,
                't10': top_score_10,
                't20': top_score_20,
                'avg': avg_score,
            }


def get_predict_catalog_context(psat: models.Psat, page_number=1, total_list=None) -> dict:
    if total_list is None:
        total_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    filtered_list = total_list.filter(is_filtered=True)
    total_context = get_paginator_context(total_list, page_number)
    filtered_context = get_paginator_context(filtered_list, page_number)
    update_predict_filtered_catalog(filtered_context['page_obj'])
    total_context.update({
        'id': '0', 'title': '전체', 'prefix': 'TotalCatalog', 'header': 'total_catalog_list',
    })
    filtered_context.update({
        'id': '1', 'title': '필터링', 'prefix': 'FilteredCatalog', 'header': 'filtered_catalog_list',
    })
    return {'total': total_context, 'filtered': filtered_context}


def update_predict_filtered_catalog(filtered_catalog_page_obj: list) -> None:
    field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
    for obj in filtered_catalog_page_obj:
        obj.rank_tot_num = obj.filtered_rank_tot_num
        obj.rank_dep_num = obj.filtered_rank_dep_num
        for key, fld in field_dict.items():
            setattr(obj, f'rank_tot_{key}', getattr(obj, f'filtered_rank_tot_{key}'))
            setattr(obj, f'rank_dep_{key}', getattr(obj, f'filtered_rank_dep_{key}'))


def get_predict_answer_context(psat: models.Psat, subject=None, page_number=1, per_page=10) -> dict:
    subject_vars = common_utils.get_subject_vars(psat, True)
    sub_list = [sub for sub in subject_vars]
    qs_answer_count_group = {sub: [] for sub in subject_vars}
    answer_context = {}

    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat_and_subject(psat, subject)
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        if sub not in qs_answer_count_group:
            qs_answer_count_group[sub] = []
        qs_answer_count_group[sub].append(qs_ac)

    for sub, qs_answer_count in qs_answer_count_group.items():
        if qs_answer_count:
            data_answers = get_predict_answer_data(qs_answer_count, subject_vars)
            context = get_paginator_context(data_answers, page_number, per_page)
            context.update({
                'id': str(sub_list.index(sub)),
                'title': sub,
                'prefix': 'Answer',
                'header': 'answer_list',
                'answer_count': 4 if sub == '헌법' else 5,
            })
            answer_context[sub] = context

    return answer_context


def get_predict_answer_data(qs_answer_count: QuerySet, subject_vars: dict) -> QuerySet:
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        field = subject_vars[sub][1]
        ans_official = qs_ac.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_ac.no = qs_ac.number
        qs_ac.ans_official = ans_official
        qs_ac.ans_official_circle = qs_ac.problem.get_answer_display()
        qs_ac.ans_predict_circle = models.choices.answer_choice()[qs_ac.ans_predict] if qs_ac.ans_predict else None
        qs_ac.ans_list = answer_official_list
        qs_ac.field = field

        qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
        qs_ac.rate_correct_top = qs_ac.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
        qs_ac.rate_correct_mid = qs_ac.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
        qs_ac.rate_correct_low = qs_ac.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
        except TypeError:
            qs_ac.rate_gap = None

    return qs_answer_count


def get_predict_statistics_response(psat: models.Psat) -> HttpResponse:
    qs_statistics = models.PredictStatistics.objects.filter(psat=psat).order_by('id')
    df = pd.DataFrame.from_records(qs_statistics.values())

    filename = f'{psat.full_reference}_성적통계.xlsx'
    drop_columns = ['id', 'psat_id']
    column_label = [('직렬', '')]

    subject_vars = common_utils.get_subject_vars(psat)
    subject_vars_total = subject_vars.copy()
    for sub, (subject, fld, idx, problem_count) in subject_vars.items():
        subject_vars_total[f'[필터링]{sub}'] = (f'[필터링]{subject}', f'filtered_{fld}', idx, problem_count)

    for (subject, fld, _, _) in subject_vars_total.values():
        drop_columns.append(fld)
        column_label.extend([
            (subject, '총 인원'), (subject, '최고'), (subject, '상위10%'), (subject, '상위20%'), (subject, '평균'),
        ])
        df_subject = pd.json_normalize(df[fld])
        df = pd.concat([df, df_subject], axis=1)

    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)

    return common_utils.get_response_for_excel_file(df, filename)


def get_predict_prime_id_response(psat: models.Psat) -> HttpResponse:
    qs_student = models.PredictStudent.objects.filter(psat=psat).values(
        'id', 'created_at', 'name', 'prime_id').order_by('id')
    df = pd.DataFrame.from_records(qs_student)
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    filename = f'{psat.full_reference}_참여자명단.xlsx'
    column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
    df.columns = pd.MultiIndex.from_tuples(column_label)
    return common_utils.get_response_for_excel_file(df, filename)


def get_predict_catalog_response(psat: models.Psat) -> HttpResponse:
    student_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    filtered_student_list = student_list.filter(is_filtered=True)
    filename = f'{psat.full_reference}_성적일람표.xlsx'

    df1 = get_predict_catalog_df_for_excel(student_list, psat)
    df2 = get_predict_catalog_df_for_excel(filtered_student_list, psat, True)

    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='전체')
        df2.to_excel(writer, sheet_name='필터링')

    return common_utils.get_response_for_excel_file(df1, filename, excel_data)


def get_predict_catalog_df_for_excel(
        student_list: QuerySet, psat: models.Psat, is_filtered=False) -> pd.DataFrame:
    column_list = [
        'id', 'psat_id', 'category_id', 'user_id',
        'name', 'serial', 'password', 'is_filtered', 'prime_id', 'unit', 'department',
        'created_at', 'latest_answer_time', 'answer_count',
        'score_sum', 'rank_tot_num', 'rank_dep_num', 'filtered_rank_tot_num', 'filtered_rank_dep_num',
    ]
    for sub_type in ['0', '1', '2', '3', 'avg']:
        column_list.append(f'score_{sub_type}')
        for stat_type in ['rank', 'filtered_rank']:
            for dep_type in ['tot', 'dep']:
                column_list.append(f'{stat_type}_{dep_type}_{sub_type}')
    df = pd.DataFrame.from_records(student_list.values(*column_list))
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    field_list = ['num', '0', '1', '2', '3', 'avg']
    if is_filtered:
        for key in field_list:
            df[f'rank_tot_{key}'] = df[f'filtered_rank_tot_{key}']
            df[f'rank_dep_{key}'] = df[f'filtered_rank_dep_{key}']

    drop_columns = []
    for key in field_list:
        drop_columns.extend([f'filtered_rank_tot_{key}', f'filtered_rank_dep_{key}'])

    column_label = [
        ('DB정보', 'ID'), ('DB정보', 'PSAT ID'), ('DB정보', '카테고리 ID'), ('DB정보', '사용자 ID'),
        ('수험정보', '이름'), ('수험정보', '수험번호'), ('수험정보', '비밀번호'),
        ('수험정보', '필터링 여부'), ('수험정보', '프라임 ID'), ('수험정보', '모집단위'), ('수험정보', '직렬'),
        ('답안정보', '등록일시'), ('답안정보', '최종답안 등록일시'), ('답안정보', '제출 답안수'),
        ('성적정보', 'PSAT 총점'), ('성적정보', '전체 총 인원'), ('성적정보', '직렬 총 인원'),
    ]
    for sub in common_utils.get_subject_vars(psat):
        column_label.extend([(sub, '점수'), (sub, '전체 등수'), (sub, '직렬 등수')])

    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)

    return df


def get_predict_answer_response(psat: models.Psat) -> HttpResponse:
    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat_and_subject(psat)
    filename = f'{psat.full_reference}_문항분석표.xlsx'

    df1 = get_predict_answer_df_for_excel(qs_answer_count)
    df2 = get_predict_answer_df_for_excel(qs_answer_count, True)

    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='전체')
        df2.to_excel(writer, sheet_name='필터링')

    return common_utils.get_response_for_excel_file(df1, filename, excel_data)


def get_predict_answer_df_for_excel(
        qs_answer_count: QuerySet[models.PredictAnswerCount], is_filtered=False
) -> pd.DataFrame:
    prefix = 'filtered_' if is_filtered else ''
    column_list = ['id',  'problem_id', 'subject', 'number', 'ans_official', 'ans_predict']
    for rank_type in ['all', 'top', 'mid', 'low']:
        for num in ['1', '2', '3', '4', '5', 'sum']:
            column_list.append(f'{prefix}count_{num}_{rank_type}')

    column_label = [
        ('DB정보', 'ID'), ('DB정보', '문제 ID'),
        ('문제정보', '과목'), ('문제정보', '번호'), ('문제정보', '정답'), ('문제정보', '예상 정답'),
    ]
    for rank_type in ['전체', '상위권', '중위권', '하위권']:
        column_label.extend([
            (rank_type, '①'), (rank_type, '②'), (rank_type, '③'),
            (rank_type, '④'), (rank_type, '⑤'), (rank_type, '합계'),
        ])

    df = pd.DataFrame.from_records(qs_answer_count.values(*column_list))
    df.columns = pd.MultiIndex.from_tuples(column_label)
    return df
