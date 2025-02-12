import dataclasses
import io
import traceback
import zipfile
from collections import defaultdict
from urllib.parse import quote

import django.db.utils
import numpy as np
import pandas as pd
import pdfkit
import unicodedata
from django.db import transaction
from django.db.models import Case, When, Value, BooleanField, Count, F, Avg, StdDev, Window, Q
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import only_staff_allowed
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임Leet'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:admin-list')
    url_exam_create = reverse_lazy('prime_leet:admin-exam-create')


@only_staff_allowed()
def list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Leet.objects.all()
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
        return render(request, 'a_prime_leet/admin_list.html#student_list', context)
    return render(request, 'a_prime_leet/admin_list.html', context)


@only_staff_allowed()
def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    config = ViewConfiguration()
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)
    answer_tab = exam_vars.get_answer_tab()

    config.url_statistics_print = reverse_lazy('prime_leet:admin-statistics-print', args=[exam.id])
    config.url_catalog_print = reverse_lazy('prime_leet:admin-catalog-print', args=[exam.id])
    config.url_answers_print = reverse_lazy('prime_leet:admin-answers-print', args=[exam.id])
    config.url_export_statistics_pdf = reverse_lazy('prime_leet:admin-export-statistics-pdf', args=[exam.id])
    config.url_export_statistics_excel = reverse_lazy('prime_leet:admin-export-statistics-excel', args=[exam.id])
    config.url_export_catalog_excel = reverse_lazy('prime_leet:admin-export-catalog-excel', args=[exam.id])
    config.url_export_answers_excel = reverse_lazy('prime_leet:admin-export-answers-excel', args=[exam.id])

    context = update_context_data(
        config=config, exam=exam, answer_tab=answer_tab,
        icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH,
    )
    data_statistics = models.ResultStatistics.objects.filter(leet=exam).order_by('id')
    student_list = exam_vars.get_student_list()
    registry_list = exam_vars.get_qs_result_registry()
    qs_answer_count = exam_vars.get_qs_answer_count(subject)

    if view_type == 'statistics_list':
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_statistics.html', context)
    if view_type == 'catalog_list':
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_catalog.html', context)
    if view_type == 'student_search':
        searched_student = student_list.filter(name=student_name)
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_catalog.html', context)
    if view_type == 'registry_list':
        registry_page_obj, registry_page_range = utils.get_paginator_data(registry_list, page_number)
        context = update_context_data(
            context, registry_page_obj=registry_page_obj, registry_page_range=registry_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_registry.html', context)
    if view_type == 'answer_list':
        subject_idx = exam_vars.subject_vars[subject][2]
        answers_page_obj_group, answers_page_range_group = (
            exam_vars.get_answer_page_data(qs_answer_count, page_number, 10))
        context = update_context_data(
            context,
            tab=answer_tab[subject_idx],
            answers=answers_page_obj_group[subject],
            answers_page_range=answers_page_range_group[subject],
        )
        return render(request, 'a_prime_leet/snippets/admin_detail_answer.html', context)

    statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
    registry_page_obj, registry_page_range = utils.get_paginator_data(registry_list, page_number)
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_answer_count, page_number, 10))

    context = update_context_data(
        context,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
        registry_page_obj=registry_page_obj, registry_page_range=registry_page_range,
    )
    return render(request, 'a_prime_leet/admin_result_detail.html', context)


@only_staff_allowed()
def result_student_detail_view(request: HtmxHttpRequest, pk: int):
    from .result_views import get_detail_context
    student = get_object_or_404(models.ResultStudent, pk=pk)
    registry = models.ResultRegistry.objects.filter(student=student).last()
    context = get_detail_context(registry.user, student.leet, student)
    if context is None:
        return redirect('prime:admin-detail', args=['result', pk])
    return render(request, 'a_prime_leet/result_print.html', context)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    context = {}
    next_url = exam.get_admin_result_detail_url()

    qs_result_student = exam_vars.get_qs_student()

    if view_type == 'answer_official':
        is_updated, message = exam_vars.update_problem_model_for_answer_official(request)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_student':
        is_updated, message = exam_vars.update_result_answer_model_for_answer_student(request)
        context = update_context_data(
            header='제출 답안 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'raw_score':
        is_updated, message = exam_vars.update_raw_scores()
        context = update_context_data(
            header='원점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = exam_vars.update_scores()
        context = update_context_data(
            header='표준점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = exam_vars.update_ranks(qs_result_student)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics(data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = exam_vars.update_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_prime_leet/snippets/admin_modal_update.html', context)


@only_staff_allowed()
def exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.LeetForm(request.POST, request.FILES)
        if form.is_valid():
            leet, _ = models.Leet.objects.get_or_create(
                year=form.cleaned_data['year'], exam=form.cleaned_data['exam'],
                round=form.cleaned_data['round'], name=form.cleaned_data['name'],
            )
            leet.is_active = True
            leet.abbr = form.cleaned_data['abbr']
            leet.page_opened_at = form.cleaned_data['page_opened_at']
            leet.exam_started_at = form.cleaned_data['exam_started_at']
            leet.exam_finished_at = form.cleaned_data['exam_finished_at']
            leet.answer_predict_opened_at = form.cleaned_data['answer_predict_opened_at']
            leet.answer_official_opened_at = form.cleaned_data['answer_official_opened_at']
            leet.save()

            exam_vars = ExamVars(leet)
            exam_vars.create_default_problems()
            exam_vars.create_default_statistics('result')

            problems = models.Problem.objects.filter(leet=leet).order_by('id')
            exam_vars.create_default_answer_counts(problems, 'result')

            response = redirect('prime_leet:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_prime_leet/admin_form.html', context)

    form = forms.LeetForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_prime_leet/admin_form.html', context)


@only_staff_allowed()
def statistics_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    data_statistics = models.ResultStatistics.objects.filter(leet=exam).order_by('id')
    statistics_page_obj, _ = utils.get_paginator_data(data_statistics, 1, 50)
    context = update_context_data(exam=exam, statistics_page_obj=statistics_page_obj)
    return render(request, 'a_prime_leet/admin_statistics_print.html', context)


@only_staff_allowed()
def catalog_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)
    student_list = exam_vars.get_student_list()
    catalog_page_obj, _ = utils.get_paginator_data(student_list, 1, 10000)
    context = update_context_data(exam=exam, catalog_page_obj=catalog_page_obj)
    return render(request, 'a_prime_leet/admin_catalog_print.html', context)


@only_staff_allowed()
def answers_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)
    qs_problems = exam_vars.get_qs_answer_count().order_by('id')
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_problems, 1, 1000))
    context = update_context_data(exam=exam, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_prime_leet/admin_answers_print.html', context)


@only_staff_allowed()
def export_statistics_pdf_view(request: HtmxHttpRequest, pk: int):
    page_number = request.GET.get('page', 1)
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    student_list = exam_vars.get_student_list()
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
def export_statistics_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    data_statistics = models.ResultStatistics.objects.filter(leet=exam).order_by('id')
    df = pd.DataFrame.from_records(data_statistics.values())

    filename = f'{exam.name}_성적통계.xlsx'
    drop_columns = ['id', 'leet_id']
    column_label = [('지망 대학', '')]
    for fld, (_, subject, _) in exam_vars.total_field_vars.items():
        drop_columns.append(fld)

        if fld[:3] == 'raw':
            subject += ' (원점수)'
        else:
            subject += ' (표준점수)'

        column_label.extend([
            (subject, '총 인원'), (subject, '최고'),
            (subject, '상위10%'), (subject, '상위25%'),
            (subject, '상위50%'), (subject, '평균'),
        ])
        df_subject = pd.json_normalize(df[fld])
        df = pd.concat([df, df_subject], axis=1)

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


@only_staff_allowed()
def export_catalog_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    student_list = exam_vars.get_student_list()
    df = pd.DataFrame.from_records(student_list.values())

    filename = f'제{exam.round}회_전국모의고사_성적일람표.xlsx'
    drop_columns = ['id', 'created_at', 'password', 'leet_id', 'category_id']
    column_label = [
        ('이름', ''), ('수험번호', ''), ('직렬', ''), ('PSAT 총점', ''),
        ('전체 총 인원', ''), ('직렬 총 인원', '')
    ]
    for _, val in exam_vars.field_vars.items():
        column_label.extend([
            (val[1], '점수'),
            (val[1], '전체 등수'),
            (val[1], '직렬 등수'),
        ])

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


@only_staff_allowed()
def export_answers_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    qs_answer_count = exam_vars.get_qs_answer_count().order_by('id')
    df = pd.DataFrame.from_records(qs_answer_count.values())

    def move_column(col_name: str, loc: int):
        col = df.pop(col_name)
        df.insert(loc, col_name, col)

    move_column('subject', 0)
    move_column('number', 1)
    move_column('ans_official', 2)
    # move_column('ans_predict', 3)

    filename = f'제{exam.round}회_전국모의고사_문항분석표.xlsx'
    drop_columns = ['id', 'leet_id']
    column_label = [('과목', ''), ('번호', ''), ('정답', '')]
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
    return render(request, 'a_prime_leet/admin_list.html', context)


def export_statistics_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/admin_list.html', context)


def export_analysis_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/admin_list.html', context)


def export_scores_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/admin_list.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.Leet

    exam_model = models.Leet
    problem_model = models.Problem

    # Result Models
    statistics_model = models.ResultStatistics
    student_model = models.ResultStudent
    registry_model = models.ResultRegistry
    answer_model = models.ResultAnswer
    score_model = models.ResultScore
    rank_model = models.ResultRank
    rank_aspiration_1_model = models.ResultRankAspiration1
    rank_aspiration_2_model = models.ResultRankAspiration2
    answer_count_model = models.ResultAnswerCount
    answer_count_top_model = models.ResultAnswerCountTopRank
    answer_count_mid_model = models.ResultAnswerCountMidRank
    answer_count_low_model = models.ResultAnswerCountLowRank

    upload_file_form = forms.UploadFileForm

    sub_list = ['언어', '추리']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    subject_vars = {
        '언어': ('언어이해', 'subject_0', 0),
        '추리': ('추리논증', 'subject_1', 1),
        '총점': ('총점', 'sum', 2),
    }
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }
    total_field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
        'raw_subject_0': ('언어', '언어이해', 0),
        'raw_subject_1': ('추리', '추리논증', 1),
        'raw_sum': ('총점', '총점', 2),
    }

    @property
    def problem_count(self):
        if self.exam.exam == '하프':
            return {'언어': 15, '추리': 20}
        return {'언어': 30, '추리': 40}

    def get_qs_student(self):
        model = self.student_model
        return model.objects.filter(leet=self.exam).order_by('id')

    def get_qs_student_answer(self, student):
        return models.ResultAnswer.objects.filter(
            problem__leet=self.exam, student=student).annotate(
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

    def get_student_list(self):
        annotate_dict = {
            'rank_num': F(f'rank__participants'),
            'rank_num_aspiration_1': F(f'rank_aspiration_1__participants'),
            'rank_num_aspiration_2': F(f'rank_aspiration_2__participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = F(f'score__raw_{fld}')
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = F(f'rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = F(f'rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = F(f'rank_aspiration_2__{fld}')

        return (
            self.student_model.objects.filter(leet=self.exam)
            .select_related('leet', 'score', 'rank')
            .order_by('leet__year', 'leet__round', 'rank__sum').annotate(**annotate_dict)
        )

    def get_qs_result_registry(self):
        annotate_dict = {
            'aspiration_1': F('student__aspiration_1'),
            'aspiration_2': F('student__aspiration_2'),
            'score_sum': F('student__score__sum'),
            'rank_num': F(f'student__rank__participants'),
            'rank_num_aspiration_1': F(f'student__rank_aspiration_1__participants'),
            'rank_num_aspiration_2': F(f'student__rank_aspiration_2__participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = F(f'student__score__raw_{fld}')
            annotate_dict[f'score_{key}'] = F(f'student__score__{fld}')
            annotate_dict[f'rank_{key}'] = F(f'student__rank__{fld}')
            annotate_dict[f'rank_{key}_aspiration_1'] = F(f'student__rank_aspiration_1__{fld}')
            annotate_dict[f'rank_{key}_aspiration_2'] = F(f'student__rank_aspiration_2__{fld}')

        return (
            self.registry_model.objects.filter(student__leet=self.exam)
            .select_related(
                'user', 'student', 'student__leet', 'student__score',
                'student__rank', 'student__rank_aspiration_1', 'student__rank_aspiration_2')
            .order_by('id').annotate(**annotate_dict)
        )

    def get_qs_answer_count(self, subject=None, model_type='result'):
        model = self.answer_count_model
        annotate_dict = {
            'subject': F('problem__subject'),
            'number': F('problem__number'),
            # 'ans_predict': F(f'problem__{model_type}_answer_count__answer_predict'),
            'ans_official': F('problem__answer'),
        }
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}_all'] = F(f'{fld}')
            annotate_dict[f'{fld}_top'] = F(f'problem__{model_type}_answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = F(f'problem__{model_type}_answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = F(f'problem__{model_type}_answer_count_low_rank__{fld}')
        qs_answer_count = (
            model.objects.filter(problem__leet=self.exam)
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

    def get_answer_tab(self):
        answer_tab = [
            {'id': str(idx), 'title': sub, 'icon': icon_set_new.ICON_SUBJECT[sub], 'answer_count': 5}
            for idx, sub in enumerate(self.sub_list)
        ]
        return answer_tab

    def get_answer_page_data(self, qs_answer_count, page_number, per_page=10):
        qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

        for entry in qs_answer_count:
            if entry.subject not in qs_answer_count_group:
                qs_answer_count_group[entry.subject] = []
            qs_answer_count_group[entry.subject].append(entry)

        for subject, qs_answer_count in qs_answer_count_group.items():
            if subject not in answers_page_obj_group:
                answers_page_obj_group[subject] = []
                answers_page_range_group[subject] = []
            data_answers = self.get_data_answers(qs_answer_count)
            answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
                data_answers, page_number, per_page)

        return answers_page_obj_group, answers_page_range_group

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

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
        is_updated = None
        error = None

        form = self.upload_file_form(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file, header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = self.problem_model.objects.get(
                                leet=self.exam, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except self.problem_model.DoesNotExist:
                            problem = self.problem_model(
                                leet=self.exam, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            bulk_create_or_update(self.problem_model, list_create, list_update, update_fields)

            if any(list_create) or any(list_update):
                is_updated = True
            elif error:
                is_updated = None
            else:
                is_updated = False
        else:
            print(form)
        return is_updated, message_dict[is_updated]

    def update_result_answer_model_for_answer_student(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '제출 답안을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }
        list_update = []
        list_create = []
        error = None

        form = self.upload_file_form(request.POST, request.FILES)
        if form.is_valid():
            label_name = ('성명', 'Unnamed: 1_level_1')
            label_password = ('비밀번호', 'Unnamed: 2_level_1')
            label_school = ('출신대학', 'Unnamed: 3_level_1')
            label_major = ('전공', 'Unnamed: 4_level_1')
            label_aspiration_1 = ('1지망', 'Unnamed: 5_level_1')
            label_aspiration_2 = ('2지망', 'Unnamed: 6_level_1')
            label_gpa_type = ('학점 (GPA)', '만점')
            label_gpa = ('학점 (GPA)', '학점')
            label_english_type = ('공인영어성적', '종류')
            label_english = ('공인영어성적', '성적')

            uploaded_file = request.FILES['file']
            df = pd.read_excel(
                uploaded_file, sheet_name='마킹데이터', header=[0, 1], index_col=0,
                dtype={label_password: str}
            )
            df = df.infer_objects(copy=False)
            df.fillna(
                {
                    label_name: '', label_password: '0000',
                    label_school: '', label_major: '',
                    label_aspiration_1: '', label_aspiration_2: '',
                    label_gpa_type: np.nan, label_gpa: np.nan,
                    label_english_type: '', label_english: np.nan,
                },
                inplace=True
            )

            for serial, row in df.iterrows():
                student_detail = {
                    'name': row[label_name], 'password': row[label_password],
                    'school': row[label_school], 'major': row[label_major],
                    'aspiration_1': row[label_aspiration_1], 'aspiration_2': row[label_aspiration_2],
                    'gpa_type': row[label_gpa_type],
                    'gpa': row[label_gpa] if row[label_gpa] != ' .' else None,
                    'english_type': row[label_english_type],
                    'english': row[label_english] if not np.isnan(row[label_english]) else None,
                }

                student, _ = self.student_model.objects.get_or_create(leet=self.exam, serial=serial)
                fields_not_match = any(str(getattr(student, fld)) != val for fld, val in student_detail.items())
                if fields_not_match:
                    for fld, val in student_detail.items():
                        setattr(student, fld, val)
                    student.save()

                subject_vars = self.subject_vars.copy()
                subject_vars.pop('총점')
                for sub, (subject, _, _) in subject_vars.items():
                    problem_count = self.problem_count[sub]
                    for number in range(1, problem_count + 1):
                        answer = row[(subject, number)] if not np.isnan(row[(subject, number)]) else 0
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
                                leet=self.exam, subject=sub, number=number)
                            q_student_answer = self.answer_model(
                                student=student, problem=problem, answer=answer)
                            list_create.append(q_student_answer)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            bulk_create_or_update(self.answer_model, list_create, list_update, update_fields)

            if any(list_create) or any(list_update):
                is_updated = True
            elif error:
                is_updated = None
            else:
                is_updated = False
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    def update_raw_scores(self):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '원점수를 업데이트했습니다.',
            False: '기존 원점수와 일치합니다.',
        }
        list_update = []
        list_create = []
        error = None

        qs_students = self.student_model.objects.filter(leet=self.exam)
        for student in qs_students:
            original_score_instance, _ = self.score_model.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self.sub_list):
                correct_count = 0
                qs_answer = (
                    self.answer_model.objects.filter(student=student, problem__subject=sub)
                    .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
                )
                for entry in qs_answer:
                    answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                    correct_count += 1 if entry.answer_student in answer_correct_list else 0

                score_list.append(correct_count)
                fields_not_match.append(getattr(original_score_instance, f'raw_subject_{idx}') != correct_count)

            score_raw_sum = sum(score_list)
            fields_not_match.append(original_score_instance.raw_sum != score_raw_sum)

            if any(fields_not_match):
                for idx, score in enumerate(score_list):
                    setattr(original_score_instance, f'raw_subject_{idx}', score)
                original_score_instance.raw_sum = score_raw_sum
                list_update.append(original_score_instance)

        update_fields = ['raw_subject_0', 'raw_subject_1', 'raw_sum']
        bulk_create_or_update(self.score_model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
        else:
            is_updated = False

        return is_updated, message_dict[is_updated]

    def update_scores(self):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '표준점수를 업데이트했습니다.',
            False: '기존 표준점수와 일치합니다.',
        }
        list_create = []
        list_update = []
        error = None

        subject_fields = {
            0: ('raw_subject_0', 'subject_0', 45, 9),
            1: ('raw_subject_1', 'subject_1', 60, 9),
        }
        original = self.score_model.objects.filter(student__leet=self.exam)
        stats = original.aggregate(
            avg_0=Avg('raw_subject_0', filter=~Q(raw_subject_0=0)),
            stddev_0=StdDev('raw_subject_0', filter=~Q(raw_subject_0=0)),
            avg_1=Avg('raw_subject_1', filter=~Q(raw_subject_1=0)),
            stddev_1=StdDev('raw_subject_1', filter=~Q(raw_subject_1=0)),
        )
        for origin in original:
            fields_not_match = []
            score_list = []

            for idx, (raw_fld, fld, leet_avg, leet_stddev) in subject_fields.items():
                avg = stats[f'avg_{idx}']
                stddev = stats[f'stddev_{idx}']

                if avg is not None and stddev:
                    raw_score = getattr(origin, raw_fld)
                    score = round((raw_score - avg) / stddev * leet_stddev + leet_avg, 1)
                    score_list.append(score)

                    if getattr(origin, fld) != score:
                        fields_not_match.append(True)
                        setattr(origin, fld, score)

            score_sum = sum(score_list)
            if any(fields_not_match):
                origin.sum = score_sum
                list_update.append(origin)

        update_fields = ['subject_0', 'subject_1', 'sum']
        bulk_create_or_update(self.score_model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
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
        annotate_dict['rank_sum'] = rank_func('score__sum')

        for student in qs_student:
            rank_list = qs_student.annotate(**annotate_dict)
            aspiration = ''
            if stat_type in ['aspiration_1', 'aspiration_2']:
                aspiration = getattr(student, stat_type)
                rank_list = rank_list.filter(Q(aspiration_1=aspiration) | Q(aspiration_2=aspiration))
            target, _ = rank_model.objects.get_or_create(student=student)

            participants = None
            if stat_type == 'total' or aspiration:
                participants = rank_list.count()
            fields_not_match = [target.participants != participants]

            for row in rank_list:
                if row.id == student.id:
                    if stat_type == 'total' or aspiration:
                        for idx in range(subject_count):
                            fields_not_match.append(
                                getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}')
                            )
                        fields_not_match.append(target.sum != row.rank_sum)
                    else:
                        for idx in range(subject_count):
                            fields_not_match.append(getattr(target, f'subject_{idx}') is not None)
                        fields_not_match.append(target.sum is not None)

                    if any(fields_not_match):
                        if stat_type == 'total' or aspiration:
                            for idx in range(subject_count):
                                setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                            target.sum = row.rank_sum
                            target.participants = participants
                        else:
                            for idx in range(subject_count):
                                setattr(target, f'subject_{idx}', None)
                            target.sum = None
                            target.participants = None
                        list_update.append(target)

        update_fields = ['subject_0', 'subject_1', 'sum', 'participants']
        return bulk_create_or_update(rank_model, list_create, list_update, update_fields)

    def update_ranks(self, qs_student):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '등수를 업데이트했습니다.',
            False: '기존 등수와 일치합니다.',
        }
        model_dict = {
            'total': self.rank_model,
            'aspiration_1': self.rank_aspiration_1_model,
            'aspiration_2': self.rank_aspiration_2_model,
        }

        is_updated_list = [
            self.update_rank_model(qs_student, model_dict, 'total'),
            self.update_rank_model(qs_student, model_dict, 'aspiration_1'),
            self.update_rank_model(qs_student, model_dict, 'aspiration_2'),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def get_data_statistics(self):
        qs_students = (
            self.student_model.objects.filter(leet=self.exam)
            .select_related('leet', 'score', 'rank', 'rank_aspiration_1', 'rank_aspiration_2')
            .annotate(
                raw_subject_0=F('score__raw_subject_0'),
                raw_subject_1=F('score__raw_subject_1'),
                raw_sum=F('score__raw_sum'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                sum=F('score__sum'),
            )
        )

        aspirations = models.choices.get_aspirations()

        data_statistics = []
        score_list = {}

        for aspiration in aspirations:
            data_statistics.append({'aspiration': aspiration, 'participants': 0})
            score_list.update({
                aspiration: {fld: [] for fld in self.total_field_vars.keys()}
            })

        for qs in qs_students:
            for fld in self.total_field_vars.keys():
                score = getattr(qs, fld)
                score_list['전체'][fld].append(score)
                if qs.aspiration_1:
                    score_list[qs.aspiration_1][fld].append(score)
                if qs.aspiration_2:
                    score_list[qs.aspiration_2][fld].append(score)

        for aspiration, score_dict in score_list.items():
            aspiration_idx = aspirations.index(aspiration)
            for fld, scores in score_dict.items():
                sub = self.total_field_vars[fld][0]
                subject = self.total_field_vars[fld][1]
                participants = len(scores)

                sorted_scores = sorted(scores, reverse=True)
                max_score = top_score_10 = top_score_25 = top_score_50 = avg_score = None
                if sorted_scores:
                    max_score = sorted_scores[0]
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_25_threshold = max(1, int(participants * 0.25))
                    top_50_threshold = max(1, int(participants * 0.5))
                    top_score_10 = sorted_scores[top_10_threshold - 1]
                    top_score_25 = sorted_scores[top_25_threshold - 1]
                    top_score_50 = sorted_scores[top_50_threshold - 1]
                    avg_score = sum(scores) / participants

                data_statistics[aspiration_idx][fld] = {
                    'field': fld,
                    'is_confirmed': True,
                    'sub': sub,
                    'subject': subject,
                    'icon': icon_set_new.ICON_SUBJECT[sub],
                    'participants': participants,
                    'max': max_score,
                    't10': top_score_10,
                    't25': top_score_25,
                    't50': top_score_50,
                    'avg': avg_score,
                }
        return data_statistics

    def update_statistics(self, data_statistics):
        model = self.statistics_model
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '통계를 업데이트했습니다.',
            False: '기존 통계와 일치합니다.',
        }
        list_update = []
        list_create = []
        error = None

        for data_stat in data_statistics:
            aspiration = data_stat['aspiration']
            stat_dict = {'aspiration': aspiration}
            for fld in self.total_field_vars.keys():
                stat_dict.update({
                    fld: {
                        'participants': data_stat[fld]['participants'],
                        'max': data_stat[fld]['max'],
                        't10': data_stat[fld]['t10'],
                        't25': data_stat[fld]['t25'],
                        't50': data_stat[fld]['t50'],
                        'avg': data_stat[fld]['avg'],
                    }
                })

            try:
                new_query = model.objects.get(leet=self.exam, aspiration=aspiration)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except model.DoesNotExist:
                list_create.append(model(leet=self.exam, **stat_dict))

        update_fields = [
            'raw_subject_0', 'raw_subject_1', 'raw_sum', 'subject_0', 'subject_1', 'sum',
        ]
        bulk_create_or_update(model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
        else:
            is_updated = False

        return is_updated, message_dict[is_updated]

    @staticmethod
    def update_answer_count_model(model_dict, rank_type='all'):
        answer_model = model_dict['answer']
        answer_count_model = model_dict[rank_type]

        list_update = []
        list_create = []

        lookup_field = f'student__rank__sum'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F('student__rank__participants')

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
            .select_related('student', 'student__rank')
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
            'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
            'count_multiple', 'count_sum',
        ]
        return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)

    def update_answer_counts(self, model_type='result'):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문항 분석표를 업데이트했습니다.',
            False: '기존 문항 분석표와 일치합니다.',
        }

        model_dict = {
            'answer': self.answer_model,
            'all': self.answer_count_model,
            'top': self.answer_count_top_model,
            'mid': self.answer_count_mid_model,
            'low': self.answer_count_low_model,
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
                problem_info = {'leet': self.exam, 'subject': subject, 'number': number}
                try:
                    self.problem_model.objects.get(**problem_info)
                except self.problem_model.DoesNotExist:
                    list_create.append(models.Problem(**problem_info))
        bulk_create_or_update(self.problem_model, list_create, [], [])

    def create_default_statistics(self, statistics_type='result'):
        model_dict = {
            'result': self.statistics_model,
        }
        model = model_dict.get(statistics_type)

        aspirations = models.choices.get_aspirations()

        list_create = []
        if model:
            for aspiration in aspirations:
                try:
                    model.objects.get(leet=self.exam, aspiration=aspiration)
                except model.DoesNotExist:
                    list_create.append(model(leet=self.exam, aspiration=aspiration))
        bulk_create_or_update(model, list_create, [], [])

    def create_default_answer_counts(self, problems, statistics_type='result'):
        model_dict = {
            'result': {
                'all': self.answer_count_model,
                'top': self.answer_count_top_model,
                'mid': self.answer_count_mid_model,
                'low': self.answer_count_low_model,
            },
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