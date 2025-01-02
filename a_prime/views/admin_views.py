import dataclasses
import io
import traceback
import zipfile
from collections import defaultdict
from urllib.parse import quote

import django.db.utils
import pandas as pd
import pdfkit
import unicodedata
from django.db import transaction
from django.db.models import Case, When, Value, BooleanField, Count, F, Window
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import only_staff_allowed
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms

INFO = {'menu': 'score', 'view_type': 'primeScore'}


class ViewConfiguration:
    menu = menu_eng = 'prime'
    menu_kor = '프라임'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_psat_changelist')
    url_list = reverse_lazy('prime:admin-list')
    url_exam_create = reverse_lazy('prime:admin-exam-create')


@only_staff_allowed()
def list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Psat.objects.filter(year__gte=2024)
    config = ViewConfiguration()
    exam_page_obj, exam_page_range = utils.get_paginator_data(exam_list, page_number)

    student_list = models.ResultRegistry.objects.select_related('user', 'student').order_by('id')
    student_page_obj, student_page_range = utils.get_paginator_data(student_list, page_number)

    context = update_context_data(
        config=config,
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
    )
    if view_type == 'student_list':
        return render(request, 'a_prime/admin_list.html#student_list', context)
    return render(request, 'a_prime/admin_list.html', context)


@only_staff_allowed()
def detail_view(request: HtmxHttpRequest, model_type: str, pk: int):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    config = ViewConfiguration()
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    answer_tab = exam_vars.get_answer_tab()

    config.model_type = model_type
    config.url_admin_update = reverse_lazy('prime:admin-update', args=[exam.id])

    config.url_statistics_print = reverse_lazy(
        'prime:admin-statistics-print', args=[model_type, exam.id])
    config.url_catalog_print = reverse_lazy(
        'prime:admin-catalog-print', args=[model_type, exam.id])
    config.url_answers_print = reverse_lazy(
        'prime:admin-answers-print', args=[model_type, exam.id])

    config.url_export_statistics_excel = reverse_lazy(
        'prime:admin-export-statistics-excel', args=[model_type, exam.id])
    config.url_export_catalog_excel = reverse_lazy(
        'prime:admin-export-catalog-excel', args=[model_type, exam.id])
    config.url_export_answers_excel = reverse_lazy(
        'prime:admin-export-answers-excel', args=[model_type, exam.id])

    config.url_export_statistics_pdf = reverse_lazy(
        'prime:admin-export-statistics-pdf', args=[model_type, exam.id])

    context = update_context_data(
        config=config, exam=exam, answer_tab=answer_tab,
        icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH,
    )
    data_statistics = exam_vars.get_qs_statistics(model_type)
    student_list = exam_vars.get_student_list(model_type)
    qs_answer_count = exam_vars.get_qs_answer_count(subject, model_type)

    if view_type == 'statistics_list':
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_prime/snippets/admin_detail_statistics.html', context)
    if view_type == 'catalog_list':
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime/snippets/admin_detail_catalog.html', context)
    if view_type == 'student_search':
        searched_student = student_list.filter(name=student_name)
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime/snippets/admin_detail_catalog.html', context)
    if view_type == 'answer_list':
        subject_idx = exam_vars.subject_vars[subject][2]
        answers_page_obj_group, answers_page_range_group = (
            exam_vars.get_answer_page_data(qs_answer_count, page_number, 10, model_type))
        context = update_context_data(
            context,
            tab=answer_tab[subject_idx],
            answers=answers_page_obj_group[subject],
            answers_page_range=answers_page_range_group[subject],
        )
        return render(request, 'a_prime/snippets/admin_detail_answer.html', context)

    statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_answer_count, page_number, 10, model_type))

    context = update_context_data(
        context,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
    )
    return render(request, f'a_prime/admin_{model_type}_detail.html', context)


@only_staff_allowed()
def result_student_detail_view(request: HtmxHttpRequest, pk: int):
    from .result_views import get_detail_context
    student = get_object_or_404(models.ResultStudent, pk=pk)
    context = get_detail_context(request.user, student.psat, student)
    if context is None:
        return redirect('prime:admin-detail', args=['result', pk])
    return render(request, 'a_prime/result_print.html', context)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    context = {}
    predict_headers = [
        'score_predict', 'rank_predict', 'statistics_predict', 'answer_count_predict'
    ]
    if view_type in predict_headers:
        next_url = exam.get_admin_predict_detail_url()
    else:
        next_url = exam.get_admin_result_detail_url()

    qs_result_student = exam_vars.get_qs_student('result')
    qs_predict_student = exam_vars.get_qs_student('predict')

    if view_type == 'answer_official':
        is_updated, message = exam_vars.update_problem_model_for_answer_official(request)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_student':
        is_updated, message = exam_vars.update_result_answer_model_for_answer_student(request)
        context = update_context_data(
            header='제출 답안 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = exam_vars.update_scores(qs_result_student)
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'score_predict':
        is_updated, message = exam_vars.update_scores(qs_predict_student, 'predict')
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = exam_vars.update_ranks(qs_result_student)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank_predict':
        is_updated, message = exam_vars.update_ranks(qs_predict_student, 'predict')
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics_model(data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics_predict':
        predict_data_statistics = exam_vars.get_data_statistics('predict')
        is_updated, message = exam_vars.update_statistics_model(predict_data_statistics, 'predict')
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = exam_vars.update_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count_predict':
        is_updated, message = exam_vars.update_answer_counts('predict')
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_prime/snippets/admin_modal_update.html', context)


@only_staff_allowed()
def exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            psat = form.save()
            exam_vars = ExamVars(psat)

            exam_vars.create_default_problems()
            exam_vars.create_default_statistics('result')
            exam_vars.create_default_statistics('predict')

            problems = models.Problem.objects.filter(psat=psat).order_by('id')
            exam_vars.create_default_answer_counts(problems, 'result')
            exam_vars.create_default_answer_counts(problems, 'predict')

            response = redirect('prime:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_prime/admin_create_exam.html', context)

    form = forms.PsatForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_exam_create.html', context)


@only_staff_allowed()
def statistics_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    statistics_model = models.ResultStatistics
    if model_type == 'predict':
        statistics_model = models.PredictStatistics
    data_statistics = statistics_model.objects.filter(psat=exam).order_by('id')
    statistics_page_obj, _ = utils.get_paginator_data(data_statistics, 1, 50)
    context = update_context_data(exam=exam, statistics_page_obj=statistics_page_obj)
    return render(request, 'a_prime/admin_print_statistics.html', context)


@only_staff_allowed()
def catalog_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    student_list = exam_vars.get_student_list(model_type)
    catalog_page_obj, _ = utils.get_paginator_data(student_list, 1, 10000)
    context = update_context_data(exam=exam, catalog_page_obj=catalog_page_obj)
    return render(request, 'a_prime/admin_print_catalog.html', context)


@only_staff_allowed()
def answers_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    qs_answer_count = exam_vars.get_qs_answer_count(model_type=model_type).order_by('id')
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_answer_count, 1, 1000))
    context = update_context_data(exam=exam, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_prime/admin_print_answers.html', context)


@only_staff_allowed()
def export_statistics_pdf_view(request: HtmxHttpRequest, model_type: str, pk: int):
    page_number = request.GET.get('page', 1)
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    student_list = exam_vars.get_student_list(model_type)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for student in catalog_page_obj:
            # from django.test import Client
            # client = Client()
            # resp = client.get(f'prime/admin/student/{student.id}')
            resp = result_student_detail_view(request, student.id)
            html_content = resp.content.decode('utf-8')

            # current_site = Site.objects.get_current()
            # domain = f"http://{current_site.domain}"
            # html_content = html_content.replace('href="/', f'href="{domain}/')
            # html_content = html_content.replace('src="/', f'src="{domain}/')

            # Convert HTML to PDF using pdfkit
            options = {
                # '--page-width': '297mm',
                # '--page-height': '210mm',
                'page-size': 'A4',
                'encoding': 'UTF-8',
                # '--enable-local-file-access': True,

            }
            print(html_content)
            pdf_file_path = f"제{exam.round}회_전국모의고사_{student.id}_{student.serial}_{student.name}.pdf"
            pdf_file_path = unicodedata.normalize('NFC', pdf_file_path)  # Normalize Unicode

            pdf_content = pdfkit.from_string(html_content, False, options=options)

            # Add the PDF to the zip file
            zip_file.writestr(pdf_file_path, pdf_content)

    filename = f'제{exam.round}회_전국모의고사_성적표_모음_{page_number}.zip'
    filename = quote(filename)

    # Create a response with the zipped content
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@only_staff_allowed()
def export_statistics_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    statistics_model = models.ResultStatistics
    if model_type == 'predict':
        statistics_model = models.PredictStatistics

    data_statistics = statistics_model.objects.filter(psat=exam).order_by('id')
    df = pd.DataFrame.from_records(data_statistics.values())

    filename = f'제{exam.round}회_전국모의고사_성적통계.xlsx'
    drop_columns = ['id', 'psat_id']
    column_label = [('직렬', '')]

    field_vars = exam_vars.field_vars
    if model_type == 'predict':
        field_vars.update({
            'filtered_subject_0': ('[필터링]헌법', '[필터링]헌법', 0),
            'filtered_subject_1': ('[필터링]언어', '[필터링]언어논리', 1),
            'filtered_subject_2': ('[필터링]자료', '[필터링]자료해석', 2),
            'filtered_subject_3': ('[필터링]상황', '[필터링]상황판단', 3),
            'filtered_average': ('[필터링]평균', '[필터링]PSAT 평균', 4),
        })

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


@only_staff_allowed()
def export_catalog_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    student_list = exam_vars.get_student_list(model_type)
    df = pd.DataFrame.from_records(student_list.values())

    filename = f'제{exam.round}회_전국모의고사_성적일람표.xlsx'

    drop_columns = ['id', 'created_at', 'password', 'psat_id', 'category_id']
    if model_type == 'predict':
        drop_columns.append('user_id')

    column_label = [
        ('이름', ''), ('수험번호', ''), ('직렬', ''), ('PSAT 총점', ''),
        ('전체 총 인원', ''), ('직렬 총 인원', '')
    ]
    if model_type == 'predict':
        column_label.insert(2, ('필터링', ''))

    for _, val in exam_vars.field_vars.items():
        column_label.extend([
            (val[1], '점수'),
            (val[1], '전체 등수'),
            (val[1], '직렬 등수'),
        ])

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


@only_staff_allowed()
def export_answers_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    qs_answer_count = exam_vars.get_qs_answer_count(model_type=model_type).order_by('id')
    df = pd.DataFrame.from_records(qs_answer_count.values())

    def move_column(col_name: str, loc: int):
        col = df.pop(col_name)
        df.insert(loc, col_name, col)

    move_column('subject', 0)
    move_column('number', 1)
    move_column('ans_official', 2)
    move_column('ans_predict', 3)

    filename = f'제{exam.round}회_전국모의고사_문항분석표.xlsx'
    drop_columns = ['id', 'problem_id', 'answer_predict']
    if model_type == 'predict':
        drop_columns.extend([
            'filtered_count_1', 'filtered_count_2', 'filtered_count_3', 'filtered_count_4', 'filtered_count_5',
            'filtered_count_0', 'filtered_count_multiple', 'filtered_count_sum',
        ])
    column_label = [('과목', ''), ('번호', ''), ('정답', ''), ('예상 정답', '')]
    top_label = ['전체', '상위권', '중위권', '하위권']
    for lbl in top_label:
        column_label.extend([
            (lbl, '①'), (lbl, '②'), (lbl, '③'), (lbl, '④'), (lbl, '⑤'),
            (lbl, '무응답'), (lbl, '복수응답'), (lbl, '합계'),
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


def export_transcript_to_pdf_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/admin_list.html', context)


def export_statistics_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/admin_list.html', context)


def export_analysis_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/admin_list.html', context)


def export_scores_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/admin_list.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.Psat

    exam_model = models.Psat
    problem_model = models.Problem
    category_model = models.Category

    # Result Models
    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    score_model = models.ResultScore
    rank_total_model = models.ResultRankTotal
    rank_category_model = models.ResultRankCategory
    statistics_model = models.ResultStatistics
    answer_count_model = models.ResultAnswerCount
    answer_count_top_model = models.ResultAnswerCountTopRank
    answer_count_mid_model = models.ResultAnswerCountMidRank
    answer_count_low_model = models.ResultAnswerCountLowRank

    # Predict Models
    predict_student_model = models.PredictStudent
    predict_answer_model = models.PredictAnswer
    predict_score_model = models.PredictScore
    predict_rank_total_model = models.PredictRankTotal
    predict_rank_category_model = models.PredictRankCategory
    predict_statistics_model = models.PredictStatistics
    predict_answer_count_model = models.PredictAnswerCount
    predict_answer_count_top_model = models.PredictAnswerCountTopRank
    predict_answer_count_mid_model = models.PredictAnswerCountMidRank
    predict_answer_count_low_model = models.PredictAnswerCountLowRank

    upload_file_form = forms.UploadFileForm

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'헌법': 25, '언어': 40, '자료': 40, '상황': 40}
    subject_vars = {
        '헌법': ('헌법', 'subject_0', 0),
        '언어': ('언어논리', 'subject_1', 1),
        '자료': ('자료해석', 'subject_2', 2),
        '상황': ('상황판단', 'subject_3', 3),
        '평균': ('PSAT 평균', 'average', 4),
    }
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }

    # Template constants
    score_template_table_1 = 'a_prime/snippets/detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_prime/snippets/detail_sheet_score_table_2.html'

    def get_student(self, user):
        return (
            self.student_model.objects.filter(registries__user=user, psat=self.exam)
            .select_related('psat', 'score', 'category').order_by('id').last()
        )

    def get_qs_student(self, model_type='result'):
        model = self.student_model
        if model_type == 'predict':
            model = self.predict_student_model
        return model.objects.filter(psat=self.exam).order_by('id')

    def get_qs_student_result_answer(self, student):
        return self.answer_model.objects.filter(
            problem__psat=self.exam, student=student).annotate(
            is_correct=Case(
                When(answer=F('problem__answer'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related(
            'problem',
            'problem__result_answer_count',
            'problem__result_answer_count_top_rank',
            'problem__result_answer_count_mid_rank',
            'problem__result_answer_count_low_rank',
        )

    def get_qs_answers(self, student: models.ResultStudent, stat_type: str):
        qs_answers = (
            self.answer_model.objects.filter(problem__psat=self.exam).values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        if stat_type == 'department':
            qs_answers = qs_answers.filter(student__category__department=student.category.department)
        return qs_answers

    def get_student_list(self, model_type='result'):
        model = self.student_model
        if model_type == 'predict':
            model = self.predict_student_model
        annotate_dict = {
            'score_sum': F('score__sum'),
            'rank_tot_num': F(f'rank_total__participants'),
            'rank_dep_num': F(f'rank_category__participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
            annotate_dict[f'rank_tot_{key}'] = F(f'rank_total__{fld}')
            annotate_dict[f'rank_dep_{key}'] = F(f'rank_category__{fld}')

        return (
            model.objects.filter(psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .order_by('psat__year', 'psat__round', 'rank_total__average')
            .annotate(department=F('category__department'), **annotate_dict)
        )

    def get_qs_answer_count(self, subject=None, model_type='result'):
        model = self.answer_count_model
        if model_type == 'predict':
            model = self.predict_answer_count_model
        annotate_dict = {
            'subject': F('problem__subject'),
            'number': F('problem__number'),
            'ans_predict': F(f'problem__{model_type}_answer_count__answer_predict'),
            'ans_official': F('problem__answer'),
        }
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}_all'] = F(f'{fld}')
            annotate_dict[f'{fld}_top'] = F(f'problem__{model_type}_answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = F(f'problem__{model_type}_answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = F(f'problem__{model_type}_answer_count_low_rank__{fld}')
        qs_answer_count = (
            model.objects.filter(problem__psat=self.exam)
            .order_by('problem__subject', 'problem__number').annotate(**annotate_dict)
            .select_related(
                f'problem',
                f'problem__{model_type}_answer_count',
                f'problem__{model_type}_answer_count_top_rank',
                f'problem__{model_type}_answer_count_mid_rank',
                f'problem__{model_type}_answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def get_qs_statistics(self, model_type='result'):
        model = self.statistics_model
        if model_type == 'predict':
            model = self.predict_statistics_model
        return model.objects.filter(psat=self.exam).order_by('id')

    def get_qs_score(self, student: models.ResultStudent, stat_type: str):
        qs_score = self.score_model.objects.filter(student__psat=self.exam)
        if stat_type == 'department':
            qs_score = qs_score.filter(student__category__department=student.category.department)
        return qs_score.values()

    def get_score_frequency_list(self) -> list:
        return self.student_model.objects.filter(psat=self.exam).values_list('score__sum', flat=True)

    def get_score_tab(self):
        return [
            {'id': '0', 'title': '내 성적', 'template': self.score_template_table_1},
            {'id': '1', 'title': '전체 기준', 'template': self.score_template_table_2},
            {'id': '2', 'title': '직렬 기준', 'template': self.score_template_table_2},
        ]

    def get_answer_tab(self):
        answer_tab = [
            {'id': str(idx), 'title': sub, 'icon': icon_set_new.ICON_SUBJECT[sub], 'answer_count': 5}
            for idx, sub in enumerate(self.sub_list)
        ]
        answer_tab[0]['answer_count'] = 4
        return answer_tab

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    def get_answer_page_data(self, qs_answer_count, page_number, per_page=10, model_type='result'):
        qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

        for entry in qs_answer_count:
            if entry.subject not in qs_answer_count_group:
                qs_answer_count_group[entry.subject] = []
            qs_answer_count_group[entry.subject].append(entry)

        for subject, qs_answer_count in qs_answer_count_group.items():
            if subject not in answers_page_obj_group:
                answers_page_obj_group[subject] = []
                answers_page_range_group[subject] = []
            data_answers = self.get_data_answers(qs_answer_count, model_type)
            answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
                data_answers, page_number, per_page)

        return answers_page_obj_group, answers_page_range_group

    def get_data_answers(self, qs_answer_count, model_type='result'):
        for entry in qs_answer_count:
            sub = entry.subject
            field = self.subject_vars[sub][1]
            ans_official = entry.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            entry.no = entry.number
            entry.ans_official = ans_official
            entry.ans_official_circle = entry.problem.get_answer_display
            entry.ans_list = answer_official_list
            entry.field = field

            if model_type == 'result':
                entry.rate_correct = entry.get_answer_rate(ans_official)
                entry.rate_correct_top = entry.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
                entry.rate_correct_mid = entry.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
                entry.rate_correct_low = entry.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
            else:
                entry.rate_correct = entry.get_answer_rate(ans_official)
                entry.rate_correct_top = entry.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
                entry.rate_correct_mid = entry.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
                entry.rate_correct_low = entry.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            try:
                entry.rate_gap = entry.rate_correct_top - entry.rate_correct_low
            except TypeError:
                entry.rate_gap = None

        return qs_answer_count

    def update_problem_model_for_answer_official(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문제 정답을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }
        list_update = []
        list_create = []

        form = self.upload_file_form(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file, sheet_name='정답', header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = self.problem_model.objects.get(
                                psat=self.exam, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except self.problem_model.DoesNotExist:
                            problem = self.problem_model(
                                psat=self.exam, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(self.problem_model, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    def update_result_answer_model_for_answer_student(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '제출 답안을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }

        form = self.upload_file_form(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(
                uploaded_file, sheet_name='마킹데이터', header=[0, 1], index_col=0,
                dtype={('비밀번호', 'Unnamed: 3_level_1'): str}
            )
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            department_dict = {
                '5급공채_일반행정': ('5급공채', '5급 일반행정'),
                '5급공채_재경': ('5급공채', '5급 재경'),
                '5급공채_기술직': ('5급공채', '5급 과학기술'),
                '5급공채_기타': ('5급공채', '5급 기타'),
                '외교관후보자': ('외교관후보자', '일반외교'),
                '지역인재_7급': ('지역인재 7급', '지역인재 7급 행정'),
                '7급_공채': ('7급공채', '7급 행정'),
                '기타': ('기타', '기타 직렬'),
            }
            for serial, row in df.iterrows():
                name = row[('성명', 'Unnamed: 1_level_1')] or '미기입자'
                department = row[('직렬', 'Unnamed: 2_level_1')]
                department_tuple = department_dict.get(department, '')
                category = self.category_model.objects.get(
                    unit=department_tuple[0], department=department_tuple[1])
                password = row[('비밀번호', 'Unnamed: 3_level_1')] or '0000'
                try:
                    student = self.student_model.objects.get(
                        psat=self.exam, name=name, serial=serial, category=category)
                    student.password = password
                    student.save()
                except self.student_model.DoesNotExist:
                    student = self.student_model.objects.create(
                        psat=self.exam, name=name, serial=serial, category=category, password=password)

                if student.answers.count() == sum(self.problem_count.values()):
                    print('No Change')
                else:
                    subject_vars = self.subject_vars.copy()
                    subject_vars.pop('평균')

                    list_update = []
                    list_create = []
                    for sub, sub_tuple in subject_vars.items():
                        subject = sub_tuple[0]
                        problem_count = self.problem_count[sub]
                        for number in range(1, problem_count + 1):
                            answer = row[(f'{subject} 마킹데이타', number)]
                            try:
                                q_student_answer = self.answer_model.objects.get(
                                    student=student,
                                    problem__subject=sub,
                                    problem__number=number,
                                )
                                if q_student_answer.answer != answer:
                                    q_student_answer.answer = answer
                                    list_update.append(q_student_answer)
                            except self.answer_model.DoesNotExist:
                                problem = self.problem_model.objects.get(
                                    psat=self.exam, subject=sub, number=number)
                                q_student_answer = self.answer_model(
                                    student=student, problem=problem, answer=answer)
                                list_create.append(q_student_answer)
                            except ValueError as error:
                                print(error)
                    update_fields = ['answer']
                    print(student.name)
                    bulk_create_or_update(self.answer_model, list_create, list_update, update_fields)
            is_updated = True
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    def update_score_model(self, qs_student, model_dict):
        answer_model = model_dict['answer']
        score_model = model_dict['score']

        list_update = []
        list_create = []

        for student in qs_student:
            original_score_instance, _ = score_model.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self.sub_list):
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

    def update_scores(self, qs_student, model_type='result'):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '점수를 업데이트했습니다.',
            False: '기존 점수와 일치합니다.',
        }

        if model_type == 'result':
            model_dict = {
                'answer': self.answer_model,
                'score': self.score_model,
            }
        else:
            model_dict = {
                'answer': self.predict_answer_model,
                'score': self.predict_score_model,
            }

        is_updated_list = [
            self.update_score_model(qs_student, model_dict),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def update_rank_model(self, qs_student, model_dict, stat_type='total'):
        rank_model = model_dict[stat_type]

        list_create = []
        list_update = []
        subject_count = len(self.sub_list)

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

    def update_ranks(self, qs_student, model_type='result'):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '등수를 업데이트했습니다.',
            False: '기존 등수와 일치합니다.',
        }
        if model_type == 'result':
            model_dict = {
                'total': self.rank_total_model,
                'department': self.rank_category_model,
            }
        else:
            model_dict = {
                'total': self.predict_rank_total_model,
                'department': self.predict_rank_category_model,
            }

        is_updated_list = [
            self.update_rank_model(qs_student, model_dict, 'total'),
            self.update_rank_model(qs_student, model_dict, 'department'),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def get_data_statistics(self, model_type='result'):
        model = self.student_model
        if model_type == 'predict':
            model = self.predict_student_model
        qs_students = (
            model.objects.filter(psat=self.exam)
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

        departments = models.choices.get_departments()
        departments.insert(0, '전체')

        data_statistics = []
        score_list = {}
        for department in departments:
            data_statistics.append({'department': department, 'participants': 0})
            score_list.update({
                department: {field: [] for field, subject_tuple in self.field_vars.items()}
            })

        for qs in qs_students:
            for field, subject_tuple in self.field_vars.items():
                score = getattr(qs, field)
                score_list['전체'][field].append(score)
                score_list[qs.department][field].append(score)

        for department, score_dict in score_list.items():
            department_idx = departments.index(department)
            for field, scores in score_dict.items():
                sub = self.field_vars[field][0]
                subject = self.field_vars[field][1]
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

    def update_statistics_model(self, data_statistics, model_type='result'):
        model = self.statistics_model
        if model_type == 'predict':
            model = self.predict_statistics_model

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
            for field in self.field_vars.keys():
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
                new_query = model.objects.get(psat=self.exam, department=department)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except model.DoesNotExist:
                list_create.append(model(psat=self.exam, **stat_dict))
        update_fields = [
            'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
        ]
        is_updated = bulk_create_or_update(model, list_create, list_update, update_fields)
        return is_updated, message_dict[is_updated]

    @staticmethod
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
            'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
            'count_sum'
        ]
        return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)

    def update_answer_counts(self, model_type='result'):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문항분석표를 업데이트했습니다.',
            False: '기존 문항분석표 데이터와 일치합니다.',
        }

        if model_type == 'result':
            model_dict = {
                'answer': self.answer_model,
                'all': self.answer_count_model,
                'top': self.answer_count_top_model,
                'mid': self.answer_count_mid_model,
                'low': self.answer_count_low_model,
            }
        else:
            model_dict = {
                'answer': self.predict_answer_model,
                'all': self.predict_answer_count_model,
                'top': self.predict_answer_count_top_model,
                'mid': self.predict_answer_count_mid_model,
                'low': self.predict_answer_count_low_model,
            }

        is_updated_list = [
            self.update_answer_count_model(model_dict, 'all'),
            self.update_answer_count_model(model_dict, 'top'),
            self.update_answer_count_model(model_dict, 'mid'),
            self.update_answer_count_model(model_dict, 'low'),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def create_default_problems(self):
        list_create = []
        for subject in self.sub_list:
            problem_count = self.problem_count[subject]
            for number in range(1, problem_count + 1):
                problem_info = {'psat': self.exam, 'subject': subject, 'number': number}
                try:
                    self.problem_model.objects.get(**problem_info)
                except self.problem_model.DoesNotExist:
                    list_create.append(models.Problem(**problem_info))
        bulk_create_or_update(self.problem_model, list_create, [], [])

    def create_default_statistics(self, statistics_type: str):
        model_dict = {
            'result': self.statistics_model,
            'predict': self.predict_statistics_model,
        }
        model = model_dict.get(statistics_type)

        department_list = list(
            self.category_model.objects.order_by('order').values_list('department', flat=True))
        department_list.insert(0, '전체')

        list_create = []
        if model:
            for department in department_list:
                try:
                    model.objects.get(psat=self.exam, department=department)
                except model.DoesNotExist:
                    list_create.append(model(psat=self.exam, department=department))
        bulk_create_or_update(model, list_create, [], [])

    def create_default_answer_counts(self, problems, statistics_type: str):
        model_dict = {
            'result': {
                'all': self.answer_count_model,
                'top': self.answer_count_top_model,
                'mid': self.answer_count_mid_model,
                'low': self.answer_count_low_model,
            },
            'predict': {
                'all': self.predict_answer_count_model,
                'top': self.predict_answer_count_top_model,
                'mid': self.predict_answer_count_mid_model,
                'low': self.predict_answer_count_low_model,
            }
        }
        model_set = model_dict.get(statistics_type)
        for rank_type, model in model_set.items():
            list_create = []
            if model:
                for problem in problems:
                    try:
                        model.objects.get(problem=problem)
                    except model.DoesNotExist:
                        list_create.append(model(problem=problem))
            bulk_create_or_update(model, list_create, [], [])


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