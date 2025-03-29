import io
import traceback
import zipfile
from collections import defaultdict
from urllib.parse import quote

import django.db.utils
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models.functions import Rank
from django.http import HttpResponse

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


def get_field_vars(psat, is_filtered=False) -> dict[str, tuple[str, str, int]]:
    if is_filtered:
        field_vars = {
            'filtered_subject_0': ('[필터링]헌법', '[필터링]헌법', 0),
            'filtered_subject_1': ('[필터링]언어', '[필터링]언어논리', 1),
            'filtered_subject_2': ('[필터링]자료', '[필터링]자료해석', 2),
            'filtered_subject_3': ('[필터링]상황', '[필터링]상황판단', 3),
            'filtered_average': ('[필터링]평균', '[필터링]PSAT 평균', 4),
        }
        if psat.exam in ['칠급', '칠예', '민경']:
            field_vars.pop('filtered_subject_0')
        return field_vars
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        field_vars.pop('subject_0')
    return field_vars


def get_total_field_vars(psat) -> dict[str, tuple[str, str, int]]:
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
        'filtered_subject_0': ('[필터링]헌법', '[필터링]헌법', 0),
        'filtered_subject_1': ('[필터링]언어', '[필터링]언어논리', 1),
        'filtered_subject_2': ('[필터링]자료', '[필터링]자료해석', 2),
        'filtered_subject_3': ('[필터링]상황', '[필터링]상황판단', 3),
        'filtered_average': ('[필터링]평균', '[필터링]PSAT 평균', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        field_vars.pop('subject_0')
        field_vars.pop('filtered_subject_0')
    return field_vars


def get_predict_psat(psat):
    try:
        return psat.predict_psat
    except ObjectDoesNotExist:
        return None


def get_answer_tab(sub_list):
    return [
        {'id': str(idx), 'title': sub, 'answer_count': 4 if sub == '헌법' else 5}
        for idx, sub in enumerate(sub_list)
    ]


def get_filter_tab(target: str):
    return [
        {'id': '0', 'title': '전체', 'prefix': f'Total{target.capitalize()}', 'header': f'total_{target}_list'},
        {'id': '1', 'title': '필터링', 'prefix': f'Filtered{target.capitalize()}', 'header': f'filtered_{target}_list'},
    ]


def get_answer_page_data(psat, qs_answer_count, page_number, per_page=10):
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
        entry.ans_official_circle = entry.problem.get_answer_display()
        entry.ans_predict_circle = models.choices.answer_choice()[entry.ans_predict] if entry.ans_predict else None
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


def update_rank_model(qs_student, model_dict: dict, sub_list: list, stat_type='total', is_filtered=False):
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
        update_rank_model(qs_student, model_dict, sub_list, 'total', True),
        update_rank_model(qs_student, model_dict, sub_list, 'department'),
        update_rank_model(qs_student, model_dict, sub_list, 'department', True),
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

    department_list = list(
        models.PredictCategory.objects.filter(exam=psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    data_statistics = []
    score_list = {}
    filtered_data_statistics = []
    filtered_score_list = {}
    for department in department_list:
        data_statistics.append({'department': department, 'participants': 0})
        score_list.update({department: {field: [] for field, subject_tuple in field_vars.items()}})
        filtered_data_statistics.append({'department': department, 'participants': 0})
        filtered_score_list.update({department: {field: [] for field, subject_tuple in field_vars.items()}})

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
        for field, subject_tuple in field_vars.items():
            score = getattr(qs_s, field)
            if score is not None:
                score_list['전체'][field].append(score)
                score_list[qs_s.department][field].append(score)
                if qs_s.is_filtered:
                    filtered_score_list['전체'][field].append(score)
                    filtered_score_list[qs_s.department][field].append(score)

    update_data_statistics(data_statistics, field_vars, score_list, department_list)
    update_data_statistics(filtered_data_statistics, field_vars, filtered_score_list, department_list)

    return data_statistics, filtered_data_statistics


def update_data_statistics(data_statistics, field_vars, score_list, department_list):
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
                avg_score = round(sum(scores) / participants, 1)

            data_statistics[department_idx][field] = {
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


def update_filtered_catalog(filtered_catalog_page_obj):
    field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
    for obj in filtered_catalog_page_obj:
        obj.rank_tot_num = obj.filtered_rank_tot_num
        obj.rank_dep_num = obj.filtered_rank_dep_num
        for key, fld in field_dict.items():
            setattr(obj, f'rank_tot_{key}', getattr(obj, f'filtered_rank_tot_{key}'))
            setattr(obj, f'rank_dep_{key}', getattr(obj, f'filtered_rank_dep_{key}'))


def update_statistics_model(psat, data_statistics, is_filtered=False):
    field_vars = get_field_vars(psat)
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
        for fld in field_vars.keys():
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


def update_statistics(psat, data_statistics, filtered_data_statistics):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    is_updated_list = [
        update_statistics_model(psat, data_statistics),
        update_statistics_model(psat, filtered_data_statistics, True),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_answer_count_model(model_dict, rank_type='all', is_filtered=False):
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
        update_answer_count_model(model_dict, 'all', True),
        update_answer_count_model(model_dict, 'top', True),
        update_answer_count_model(model_dict, 'mid', True),
        update_answer_count_model(model_dict, 'low', True),
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


def get_statistics_response(psat):
    qs_statistics = models.PredictStatistics.objects.filter(psat=psat).order_by('id')
    df = pd.DataFrame.from_records(qs_statistics.values())

    filename = f'{psat.full_reference}_성적통계.xlsx'
    drop_columns = ['id', 'psat_id']
    column_label = [('직렬', '')]

    field_vars = get_total_field_vars(psat)
    for fld, val in field_vars.items():
        drop_columns.append(fld)
        column_label.extend([
            (val[1], '총 인원'),
            (val[1], '최고'),
            (val[1], '상위10%'),
            (val[1], '상위20%'),
            (val[1], '평균'),
        ])
        df_subject = pd.json_normalize(df[fld])
        df = pd.concat([df, df_subject], axis=1)

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


def get_prime_id_response(psat):
    qs_student = models.PredictStudent.objects.filter(psat=psat).values(
        'id', 'created_at', 'name', 'prime_id').order_by('id')
    df = pd.DataFrame.from_records(qs_student)
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    filename = f'{psat.full_reference}_참여자명단.xlsx'
    column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
    return get_response_for_excel_file(df, [], column_label, filename)


def get_catalog_response(psat):
    student_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    filtered_student_list = student_list.filter(is_filtered=True)

    df1, filename1 = get_catalog_dataframe_and_file_name(student_list, psat)
    df2, filename2 = get_catalog_dataframe_and_file_name(filtered_student_list, psat, True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        excel_buffer1 = io.BytesIO()
        df1.to_excel(excel_buffer1, engine='xlsxwriter')
        zip_file.writestr(filename1, excel_buffer1.getvalue())

        excel_buffer2 = io.BytesIO()
        df2.to_excel(excel_buffer2, engine='xlsxwriter')
        zip_file.writestr(filename2, excel_buffer2.getvalue())

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="catalog_files.zip"'
    return response


def get_catalog_dataframe_and_file_name(student_list, psat, is_filtered=False):
    filtered_type = '필터링' if is_filtered else '전체'
    filename = f'{psat.full_reference}_성적일람표_{filtered_type}.xlsx'

    df = pd.DataFrame.from_records(student_list.values())
    if is_filtered:
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
        df['rank_tot_num'] = df['filtered_rank_tot_num']
        df['rank_dep_num'] = df['filtered_rank_dep_num']
        for key, fld in field_dict.items():
            df[f'rank_tot_{key}'] = df[f'filtered_rank_tot_{key}']
            df[f'rank_dep_{key}'] = df[f'filtered_rank_dep_{key}']

    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    drop_columns = ['filtered_rank_tot_num', 'filtered_rank_dep_num']
    field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
    for key in field_dict:
        drop_columns.extend([f'filtered_rank_tot_{key}', f'filtered_rank_dep_{key}'])
    column_label = [
        ('ID', ''), ('등록일시', ''), ('이름', ''), ('수험번호', ''), ('비밀번호', ''),
        ('PSAT ID', ''), ('카테고리 ID', ''), ('사용자 ID', ''),
        ('필터링 여부', ''), ('프라임 ID', ''), ('직렬', ''), ('최종답안 등록일시', ''),
        ('제출 답안수', ''), ('PSAT 총점', ''), ('전체 총 인원', ''), ('직렬 총 인원', ''),
    ]

    field_vars = get_field_vars(psat)
    for _, val in field_vars.items():
        column_label.extend([
            (val[1], '점수'),
            (val[1], '전체 등수'),
            (val[1], '직렬 등수'),
        ])

    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)
    df.reset_index(inplace=True)

    return df, filename


def get_answer_response(psat):
    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat_and_subject(psat)
    df = pd.DataFrame.from_records(qs_answer_count.values())

    def move_column(col_name: str, loc: int):
        col = df.pop(col_name)
        df.insert(loc, col_name, col)

    move_column('problem_id', 1)
    move_column('subject', 2)
    move_column('number', 3)
    move_column('ans_official', 4)
    move_column('ans_predict', 5)

    filename = f'{psat.full_reference}_문항분석표.xlsx'
    drop_columns = [
        'answer_predict',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0', 'count_multiple', 'count_sum',
        'filtered_count_1', 'filtered_count_2', 'filtered_count_3', 'filtered_count_4',
        'filtered_count_5', 'filtered_count_0', 'filtered_count_multiple', 'filtered_count_sum',
    ]
    column_label = [
        ('ID', '', ''), ('문제 ID', '', ''), ('과목', '', ''),
        ('번호', '', ''), ('정답', '', ''), ('예상 정답', '', ''),
    ]
    for top in ['전체 데이터', '필터링 데이터']:
        for mid in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (top, mid, '①'), (top, mid, '②'), (top, mid, '③'),
                (top, mid, '④'), (top, mid, '⑤'), (top, mid, '합계'),
            ])

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


def get_response_for_excel_file(df, drop_columns, column_label, filename):
    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)
    df.reset_index(inplace=True)

    excel_data = io.BytesIO()
    df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
