import pandas as pd
from django.db.models import QuerySet

from a_psat import models
from a_psat.utils.variables import *
from common.utils.export_excel_methods import *


@for_normal_views
def get_normal_next_url_for_answer_input(
        student: models.PredictStudent, psat: models.Psat) -> str:
    subject_vars = get_subject_vars(psat, True)
    for sub, (_, fld, _, _) in subject_vars.items():
        if student.answer_count[sub] == 0:
            return psat.get_predict_answer_input_url(fld)
    return psat.get_predict_detail_url()


@for_admin_views
def get_admin_statistics_response(psat: models.Psat) -> HttpResponse:
    qs_statistics = models.PredictStatistics.objects.filter(psat=psat).order_by('id')
    df = pd.DataFrame.from_records(qs_statistics.values())

    filename = f'{psat.full_reference}_성적통계.xlsx'
    drop_columns = ['id', 'psat_id']
    column_label = [('직렬', '')]

    subject_vars = get_subject_vars(psat)
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


@for_admin_views
def get_admin_prime_id_response(psat: models.Psat) -> HttpResponse:
    qs_student = models.PredictStudent.objects.filter(psat=psat).values(
        'id', 'created_at', 'name', 'prime_id').order_by('id')
    df = pd.DataFrame.from_records(qs_student)
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    filename = f'{psat.full_reference}_참여자명단.xlsx'
    column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
    df.columns = pd.MultiIndex.from_tuples(column_label)
    return get_response_for_excel_file(df, filename)


@for_admin_views
def get_admin_catalog_response(psat: models.Psat) -> HttpResponse:
    student_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    filtered_student_list = student_list.filter(is_filtered=True)
    filename = f'{psat.full_reference}_성적일람표.xlsx'

    df1 = get_admin_catalog_df_for_excel(student_list, psat)
    df2 = get_admin_catalog_df_for_excel(filtered_student_list, psat, True)

    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='전체')
        df2.to_excel(writer, sheet_name='필터링')

    return get_response_for_excel_file(df1, filename, excel_data)


@for_admin_views
def get_admin_catalog_df_for_excel(
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
    for sub in get_subject_vars(psat):
        column_label.extend([(sub, '점수'), (sub, '전체 등수'), (sub, '직렬 등수')])

    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)

    return df


@for_admin_views
def get_admin_answer_response(psat: models.Psat) -> HttpResponse:
    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat_and_subject(psat)
    filename = f'{psat.full_reference}_문항분석표.xlsx'

    df1 = get_admin_answer_df_for_excel(qs_answer_count)
    df2 = get_admin_answer_df_for_excel(qs_answer_count, True)

    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='전체')
        df2.to_excel(writer, sheet_name='필터링')

    return get_response_for_excel_file(df1, filename, excel_data)


@for_admin_views
def get_admin_answer_df_for_excel(
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
