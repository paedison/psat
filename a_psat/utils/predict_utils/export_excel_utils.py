import io
from urllib.parse import quote

import pandas as pd
from django.db.models import Window, F, QuerySet
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from a_psat import models
from . import common_utils


def create_predict_confirmed_answers(
        student: models.PredictStudent, sub: str, answer_data: list) -> None:
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(psat=student.psat, subject=sub, number=no)
        list_create.append(models.PredictAnswer(student=student, problem=problem, answer=ans))
    common_utils.bulk_create_or_update(models.PredictAnswer, list_create, [], [])


def update_predict_answer_counts_after_confirm(
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


def get_predict_answer_all_confirmed(student: models.PredictStudent) -> bool:
    answer_student_counts = models.PredictAnswer.objects.filter(student=student).count()
    problem_count_sum = sum([
        value[3] for value in common_utils.get_subject_vars(student.psat, True).values()
    ])
    return answer_student_counts == problem_count_sum


def update_predict_statistics_after_confirm(
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


def update_predict_score_for_each_student(
        qs_answer: QuerySet[models.PredictAnswer],
        subject_field: str,
        sub: str
) -> None:
    student = qs_answer.first().student
    score = student.score
    correct_count = 0
    for qs_a in qs_answer:
        correct_count += 1 if qs_a.answer_student == qs_a.answer_correct else 0

    problem_count = common_utils.get_subject_vars(student.psat)[sub][3]
    score_point = correct_count * 100 / problem_count
    setattr(score, subject_field, score_point)

    score_list = [sco for sco in [score.subject_1, score.subject_2, score.subject_3] if sco is not None]
    score_sum = sum(score_list) if score_list else None
    score_average = round(score_sum / 3, 1) if score_sum else None

    score.sum = score_sum
    score.average = score_average
    score.save()


def update_predict_rank_for_each_student(
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


def get_predict_next_url_for_answer_input(
        student: models.PredictStudent, psat: models.Psat) -> str:
    subject_vars = common_utils.get_subject_vars(psat, True)
    for sub, (_, fld, _, _) in subject_vars.items():
        if student.answer_count[sub] == 0:
            return psat.get_predict_answer_input_url(fld)
    return psat.get_predict_detail_url()


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

    return get_response_for_excel_file(df, filename)


def get_predict_prime_id_response(psat: models.Psat) -> HttpResponse:
    qs_student = models.PredictStudent.objects.filter(psat=psat).values(
        'id', 'created_at', 'name', 'prime_id').order_by('id')
    df = pd.DataFrame.from_records(qs_student)
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    filename = f'{psat.full_reference}_참여자명단.xlsx'
    column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
    df.columns = pd.MultiIndex.from_tuples(column_label)
    return get_response_for_excel_file(df, filename)


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

    return get_response_for_excel_file(df1, filename, excel_data)


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

    return get_response_for_excel_file(df1, filename, excel_data)


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


def get_response_for_excel_file(df, filename, excel_data=None) -> HttpResponse:
    if excel_data is None:
        excel_data = io.BytesIO()
        df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
