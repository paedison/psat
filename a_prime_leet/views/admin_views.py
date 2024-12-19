import dataclasses
import io
import zipfile
from collections import defaultdict
from urllib.parse import quote

import pandas as pd
import pdfkit
import unicodedata
from django.db.models import Case, When, Value, BooleanField, Count, F, Avg, StdDev, Window
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import only_staff_allowed
from common.utils import HtmxHttpRequest, update_context_data
from scripts.update_prime_result_models import bulk_create_or_update
from .. import models, utils, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임Leet'
    submenu = submenu_eng = 'score'
    submenu_kor = '관리자 메뉴'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:score-admin-list')
    url_exam_create = reverse_lazy('prime_leet:admin-exam-create')


@only_staff_allowed()
def list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Leet.objects.filter(year__gte=2024)
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
        return render(request, 'a_prime_leet/score_admin_list.html#student_list', context)
    return render(request, 'a_prime_leet/score_admin_list.html', context)


@only_staff_allowed()
def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)
    subject = request.GET.get('subject', '')

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
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,
    )
    if view_type == 'statistics_list':
        data_statistics = models.ResultStatistics.objects.filter(leet=exam).order_by('id')
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_statistics.html', context)
    if view_type == 'catalog_list':
        student_list = exam_vars.get_student_list()
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_catalog.html', context)
    if view_type == 'answer_list':
        subject_idx = exam_vars.subject_vars[subject][2]
        qs_problems = exam_vars.get_qs_problems_for_answer_count(subject)
        answers_page_obj_group, answers_page_range_group = (
            exam_vars.get_answer_page_data(qs_problems, page_number, 10))
        context = update_context_data(
            context,
            tab=answer_tab[subject_idx],
            answers=answers_page_obj_group[subject],
            answers_page_range=answers_page_range_group[subject],
        )
        return render(request, 'a_prime_leet/snippets/admin_detail_answer.html', context)

    data_statistics = models.ResultStatistics.objects.filter(leet=exam).order_by('id')
    statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)

    student_list = exam_vars.get_student_list()
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)

    qs_problems = exam_vars.get_qs_problems_for_answer_count(subject)
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_problems, page_number, 10))

    context = update_context_data(
        context,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
    )
    return render(request, 'a_prime_leet/score_admin_detail.html', context)


@only_staff_allowed()
def student_detail_view(request: HtmxHttpRequest, pk: int):
    from .score_views import get_detail_context
    student = get_object_or_404(models.ResultStudent, pk=pk)
    registry = models.ResultRegistry.objects.filter(student=student).last()
    context = get_detail_context(registry.user, student.leet.pk)
    return render(request, 'a_prime_leet/score_print.html', context)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)

    context = {}
    next_url = exam.get_admin_detail_url()

    if view_type == 'answer_official':
        is_updated, message = exam_vars.update_answer_official(request)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_student':
        is_updated, message = exam_vars.update_answer_student(request)
        context = update_context_data(
            header='제출 답안 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'raw_scores':
        is_updated, message = exam_vars.update_raw_scores()
        context = update_context_data(
            header='원점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'scores':
        is_updated, message = exam_vars.update_scores()
        context = update_context_data(
            header='표준점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'ranks':
        is_updated, message = exam_vars.update_ranks()
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics(data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answers':
        is_updated, message = exam_vars.update_answer_analysis(models.ResultAnswerCount)
        is_updated, message = exam_vars.update_answer_analysis(models.ResultAnswerCountTopRank, 'top')
        is_updated, message = exam_vars.update_answer_analysis(models.ResultAnswerCountMidRank, 'mid')
        is_updated, message = exam_vars.update_answer_analysis(models.ResultAnswerCountLowRank, 'low')
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_prime_leet/snippets/admin_modal_update.html', context)


@only_staff_allowed()
def exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.LeetForm(request.POST, request.FILES)
        if form.is_valid():
            leet = form.save()
            exam_vars = ExamVars(leet)

            exam_vars.create_problems()

            problems = models.Problem.objects.filter(leet=leet).order_by('id')
            exam_vars.create_answer_counts(problems, 'all')
            exam_vars.create_answer_counts(problems, 'top')
            exam_vars.create_answer_counts(problems, 'mid')
            exam_vars.create_answer_counts(problems, 'low')

            response = redirect('prime_leet:score-admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_prime_leet/admin_exam_create.html', context)

    form = forms.LeetForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_prime_leet/admin_exam_create.html', context)


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
    qs_problems = exam_vars.get_qs_problems_for_answer_count().order_by('id')
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
            resp = student_detail_view(request, student.id)
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

    filename = f'제{exam.round}회_전국모의고사_성적통계.xlsx'
    drop_columns = ['id', 'leet_id']
    column_label = [('직렬', '')]
    for fld, val in exam_vars.field_vars.items():
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

    qs_problems = exam_vars.get_qs_problems_for_answer_count().order_by('id')
    df = pd.DataFrame.from_records(qs_problems.values())

    filename = f'제{exam.round}회_전국모의고사_문항분석표.xlsx'
    drop_columns = ['id', 'leet_id']
    column_label = [('과목', ''), ('번호', ''), ('정답', '')]
    count_dict = {1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤', 6: '합계'}
    for num in range(1, 7):
        column_label.extend([
            (count_dict[num], '전체'),
            (count_dict[num], '상위권'),
            (count_dict[num], '중위권'),
            (count_dict[num], '하위권'),
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
    return render(request, 'a_prime_leet/score_admin_list.html', context)


def export_statistics_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/score_admin_list.html', context)


def export_analysis_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/score_admin_list.html', context)


def export_scores_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime_leet/score_admin_list.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.Leet

    exam_model = models.Leet
    problem_model = models.Problem
    statistics_model = models.ResultStatistics
    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    answer_count_model = models.ResultAnswerCount
    answer_count_top_model = models.ResultAnswerCountTopRank
    answer_count_mid_model = models.ResultAnswerCountMidRank
    answer_count_low_model = models.ResultAnswerCountLowRank
    score_model = models.ResultScore
    rank_model = models.ResultRank
    student_form = forms.PrimeLeetStudentForm

    sub_list = ['언어', '추리']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'언어': 30, '추리': 40}
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

    def get_student(self, user):
        return (
            self.student_model.objects.filter(registries__user=user, leet=self.exam)
            .select_related('leet', 'score', 'rank').order_by('id').last()
        )

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
        annotate_dict = {'rank_num': F(f'rank__participants')}
        field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'raw_score_{key}'] = F(f'score__raw_{fld}')
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = F(f'rank__{fld}')

        return (
            self.student_model.objects.filter(leet=self.exam)
            .select_related('leet', 'score', 'rank')
            .order_by('leet__year', 'leet__round', 'rank__sum').annotate(**annotate_dict)
        )

    def get_qs_problems_for_answer_count(self, subject=None):
        annotate_dict = {}
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}'] = F(f'result_answer_count__{fld}')
            annotate_dict[f'{fld}_top'] = F(f'result_answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = F(f'result_answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = F(f'result_answer_count_low_rank__{fld}')
        qs_problems = (
            self.problem_model.objects.filter(leet=self.exam)
            .order_by('subject', 'number')
            .select_related(
                'result_answer_count',
                'result_answer_count_top_rank',
                'result_answer_count_mid_rank',
                'result_answer_count_low_rank',
            ).annotate(**annotate_dict)
        )
        if subject:
            qs_problems = qs_problems.filter(subject=subject)
        return qs_problems

    def get_answer_page_data(self, qs_problems, page_number, per_page=10):
        qs_problems_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

        for problem in qs_problems:
            if problem.subject not in qs_problems_group:
                qs_problems_group[problem.subject] = []
            qs_problems_group[problem.subject].append(problem)

        for subject, qs_problems in qs_problems_group.items():
            if subject not in answers_page_obj_group:
                answers_page_obj_group[subject] = []
                answers_page_range_group[subject] = []
            data_answers = self.get_data_answers(qs_problems)
            answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
                data_answers, page_number, per_page)

        return answers_page_obj_group, answers_page_range_group

    def get_qs_score(self, student: models.ResultStudent, stat_type: str):
        qs_score = self.score_model.objects.filter(student__leet=self.exam)
        return qs_score.values()

    def get_score_frequency_list(self) -> list:
        return self.student_model.objects.filter(leet=self.exam).values_list('score__sum', flat=True)

    def get_score_tab(self):
        return [
            {'id': '0', 'title': '내 성적', 'template': self.score_template_table_1},
            {'id': '1', 'title': '전체 기준', 'template': self.score_template_table_2},
        ]

    def get_answer_tab(self):
        answer_tab = [
            {'id': str(idx), 'title': sub, 'icon': icon_set_new.ICON_SUBJECT[sub], 'answer_count': 5}
            for idx, sub in enumerate(self.sub_list)
        ]
        return answer_tab

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    def get_data_answers(self, qs_problems):
        for line in qs_problems:
            sub = line.subject
            field = self.subject_vars[sub][1]
            ans_official = line.answer

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            line.no = line.number
            line.ans_official = ans_official
            line.ans_official_circle = line.get_answer_display
            line.ans_list = answer_official_list
            line.field = field

            line.rate_correct = line.result_answer_count.get_answer_rate(ans_official)
            line.rate_correct_top = line.result_answer_count_top_rank.get_answer_rate(ans_official)
            line.rate_correct_mid = line.result_answer_count_mid_rank.get_answer_rate(ans_official)
            line.rate_correct_low = line.result_answer_count_low_rank.get_answer_rate(ans_official)
            try:
                line.rate_gap = line.rate_correct_top - line.rate_correct_low
            except TypeError:
                line.rate_gap = None

        return qs_problems

    def update_answer_official(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문제 정답을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }
        list_update = []
        list_create = []
        is_updated = None
        error = None

        form = forms.UploadAnswerOfficialFileForm(request.POST, request.FILES)
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

    def update_answer_student(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '제출 답안을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }
        list_update = []
        list_create = []
        error = None

        form = forms.UploadAnswerOfficialFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file, sheet_name='마킹데이터', header=[0, 1], index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for serial, row in df.iterrows():
                name = row[('성명', 'Unnamed: 1_level_1')]
                password = row[('비밀번호', 'Unnamed: 3_level_1')]
                student, _ = self.student_model.objects.get_or_create(
                    leet=self.exam, name=name, serial=serial, password=password)

                subject_vars = self.subject_vars.copy()
                subject_vars.pop('총점')
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
            original, _ = self.score_model.objects.get_or_create(student=student)
            target = (
                self.get_qs_student_answer(student).filter(is_correct=True)
                .values(sub=F('problem__subject'))
                .annotate(score_raw=Count('id'))
                .order_by('sub')
            )

            fields_not_match = []
            score_raw_sum = 0
            for tg in target:
                sub = tg['sub']
                score_raw = tg['score_raw']
                score_raw_sum += score_raw
                field = f'raw_{self.subject_vars[sub][1]}'
                if getattr(original, field) != score_raw:
                    fields_not_match.append(True)
                    setattr(original, field, score_raw)
            if any(fields_not_match):
                original.raw_sum = score_raw_sum
                list_update.append(original)

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
            1: ('raw_subject_1', 'subject_1', 60, 12),
        }
        stats = self.score_model.objects.aggregate(
            avg_0=Avg('raw_subject_0'),
            stddev_0=StdDev('raw_subject_0'),
            avg_1=Avg('raw_subject_1'),
            stddev_1=StdDev('raw_subject_1'),
        )
        original = self.score_model.objects.filter(student__leet=self.exam)
        for origin in original:
            fields_not_match = []
            scores = []

            for subject_idx, data_tuple in subject_fields.items():
                raw_fld = data_tuple[0]
                fld = data_tuple[1]
                leet_avg = data_tuple[2]
                leet_stddev = data_tuple[3]

                avg = stats[f'avg_{subject_idx}']
                stddev = stats[f'stddev_{subject_idx}']

                if avg is not None and stddev and stddev > 0:
                    raw_score = getattr(origin, raw_fld)
                    standard_score = (raw_score - avg) / stddev
                    score = standard_score * leet_stddev + leet_avg
                    scores.append(score)

                    if getattr(origin, fld) != score:
                        fields_not_match.append(True)
                        setattr(origin, fld, score)

            score_sum = sum(scores)
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

    def update_ranks(self):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '등수를 업데이트했습니다.',
            False: '기존 등수와 일치합니다.',
        }
        list_create = []
        list_update = []
        error = None
        subject_count = len(self.sub_list)

        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        annotate_dict = {f'rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
        annotate_dict['rank_sum'] = rank_func('score__sum')

        qs_student = self.student_model.objects.filter(leet=self.exam).order_by('id')
        participants = qs_student.count()
        for student in qs_student:
            rank_list = qs_student.annotate(**annotate_dict)
            target, _ = self.rank_model.objects.get_or_create(student=student)

            fields_not_match = [target.participants != participants]
            for row in rank_list:
                if row.id == student.id:
                    for idx in range(subject_count):
                        fields_not_match.append(
                            getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}')
                        )
                    fields_not_match.append(target.sum != row.rank_sum)

                    if any(fields_not_match):
                        for idx in range(subject_count):
                            setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                        target.sum = row.rank_sum
                        target.participants = participants
                        list_update.append(target)

        update_fields = ['subject_0', 'subject_1', 'sum', 'participants']
        bulk_create_or_update(self.rank_model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
        else:
            is_updated = False

        return is_updated, message_dict[is_updated]

    def get_data_statistics(self):
        qs_students = (
            self.student_model.objects.filter(leet=self.exam)
            .select_related('leet', 'score', 'rank')
            .annotate(
                raw_subject_0=F('score__raw_subject_0'),
                raw_subject_1=F('score__raw_subject_1'),
                raw_sum=F('score__raw_sum'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                sum=F('score__sum'),
            )
        )

        data_statistics = {}
        field_vars = {
            'raw_subject_0': ('언어', '언어이해', 0),
            'raw_subject_1': ('추리', '추리논증', 1),
            'raw_sum': ('총점', '총점', 2),
            'subject_0': ('언어', '언어이해', 0),
            'subject_1': ('추리', '추리논증', 1),
            'sum': ('총점', '총점', 2),
        }
        score_dict = {
            'raw_subject_0': [],
            'raw_subject_1': [],
            'raw_sum': [],
            'subject_0': [],
            'subject_1': [],
            'sum': [],
        }

        for qs in qs_students:
            for fld in score_dict.keys():
                score = getattr(qs, fld)
                score_dict[fld].append(score)

        for fld, scores in score_dict.items():
            sub = field_vars[fld][0]
            subject = field_vars[fld][1]
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

            data_statistics[fld] = {
                'field': fld,
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

    def update_statistics(self, data_statistics):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '통계를 업데이트했습니다.',
            False: '기존 통계와 일치합니다.',
        }
        list_update = []
        list_create = []
        error = None

        stat_dict = {}
        for fld, data in data_statistics.items():
            stat_dict.update({
                fld: {
                    'participants': data['participants'],
                    'max': data['max'],
                    't10': data['t10'],
                    't20': data['t20'],
                    'avg': data['avg'],
                }
            })

        try:
            new_query = self.statistics_model.objects.get(leet=self.exam)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in stat_dict.items()
            )
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except self.statistics_model.DoesNotExist:
            list_create.append(self.statistics_model(leet=self.exam, **stat_dict))

        update_fields = [
            'raw_subject_0', 'raw_subject_1', 'raw_sum', 'subject_0', 'subject_1', 'sum',
        ]
        bulk_create_or_update(self.statistics_model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
        else:
            is_updated = False

        return is_updated, message_dict[is_updated]

    def update_answer_analysis(self, answer_count_model, rank_type=''):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문항 분석표를 업데이트했습니다.',
            False: '기존 문항 분석표와 일치합니다.',
        }
        list_create = []
        list_update = []
        error = None

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
            self.answer_model.objects.filter(**lookup_exp)
            .values('problem_id', 'answer')
            .annotate(count=Count('id'))
            .order_by('problem_id', 'answer')
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
            'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
            'count_multiple', 'count_sum',
        ]
        bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)

        if any(list_create) or any(list_update):
            is_updated = True
        elif error:
            is_updated = None
        else:
            is_updated = False

        return is_updated, message_dict[is_updated]

    def create_problems(self):
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

    def create_answer_counts(self, problems, count_type: str):
        model_dict = {
            'all': self.answer_count_model,
            'top': self.answer_count_top_model,
            'mid': self.answer_count_mid_model,
            'low': self.answer_count_low_model,
        }
        model = model_dict.get(count_type)
        list_create = []
        if model:
            for problem in problems:
                try:
                    model.objects.get(problem=problem)
                except model.DoesNotExist:
                    list_create.append(model(problem=problem))
        bulk_create_or_update(model, list_create, [], [])
