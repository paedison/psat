import dataclasses
import io
import zipfile
from urllib.parse import quote

import pandas as pd
import pdfkit
import unicodedata
from django.contrib.sites.models import Site
from django.db.models import Case, When, Value, BooleanField, Count, F
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import only_staff_allowed
from common.utils import HtmxHttpRequest, update_context_data
from scripts.update_prime_result_models import bulk_create_or_update
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
    url_list = reverse_lazy('prime:score-admin-list')
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
def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)
    subject = request.GET.get('subject', '')

    config = ViewConfiguration()
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    answer_tab = exam_vars.get_answer_tab()

    config.url_statistics_print = reverse_lazy('prime:admin-statistics-print', args=[exam.id])
    config.url_catalog_print = reverse_lazy('prime:admin-catalog-print', args=[exam.id])
    config.url_answers_print = reverse_lazy('prime:admin-answers-print', args=[exam.id])
    config.url_export_statistics_pdf = reverse_lazy('prime:admin-export-statistics-pdf', args=[exam.id])
    config.url_export_statistics_excel = reverse_lazy('prime:admin-export-statistics-excel', args=[exam.id])
    config.url_export_catalog_excel = reverse_lazy('prime:admin-export-catalog-excel', args=[exam.id])
    config.url_export_answers_excel = reverse_lazy('prime:admin-export-answers-excel', args=[exam.id])

    context = update_context_data(
        config=config, exam=exam, answer_tab=answer_tab,
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,
    )
    if view_type == 'statistics_list':
        data_statistics = models.ResultStatistics.objects.filter(psat=exam).order_by('id')
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_prime/snippets/admin_detail_statistics.html', context)
    if view_type == 'catalog_list':
        student_list = exam_vars.get_student_list()
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime/snippets/admin_detail_catalog.html', context)
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
        return render(request, 'a_prime/snippets/admin_detail_answer.html', context)

    data_statistics = models.ResultStatistics.objects.filter(psat=exam).order_by('id')
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
    return render(request, 'a_prime/admin_detail.html', context)


@only_staff_allowed()
def student_detail_view(request: HtmxHttpRequest, pk: int):
    from .score_views import get_detail_context
    student = get_object_or_404(models.ResultStudent, pk=pk)
    registry = models.ResultRegistry.objects.filter(student=student).last()
    context = get_detail_context(registry.user, student.psat.pk)
    return render(request, 'a_prime/score_print.html', context)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    is_answer_official = view_type == 'answer_official'
    is_statistics = view_type == 'statistics'

    context = {}
    next_url = exam.get_admin_detail_url()
    if is_answer_official:
        is_updated, message = update_answer_official(request, exam_vars, exam)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)
    if is_statistics:
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics(data_statistics)
        print(is_updated)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

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

            response = redirect('prime:score-admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_prime/admin_create_exam.html', context)

    form = forms.PsatForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_exam_create.html', context)


@only_staff_allowed()
def statistics_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    data_statistics = models.ResultStatistics.objects.filter(psat=exam).order_by('id')
    statistics_page_obj, _ = utils.get_paginator_data(data_statistics, 1, 50)
    context = update_context_data(exam=exam, statistics_page_obj=statistics_page_obj)
    return render(request, 'a_prime/admin_print_statistics.html', context)


@only_staff_allowed()
def catalog_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    student_list = exam_vars.get_student_list()
    catalog_page_obj, _ = utils.get_paginator_data(student_list, 1, 10000)
    context = update_context_data(exam=exam, catalog_page_obj=catalog_page_obj)
    return render(request, 'a_prime/admin_print_catalog.html', context)


@only_staff_allowed()
def answers_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    qs_problems = exam_vars.get_qs_problems_for_answer_count().order_by('id')
    answers_page_obj_group, answers_page_range_group = (
        exam_vars.get_answer_page_data(qs_problems, 1, 1000))
    context = update_context_data(exam=exam, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_prime/admin_print_answers.html', context)


@only_staff_allowed()
def export_statistics_pdf_view(request: HtmxHttpRequest, pk: int):
    page_number = request.GET.get('page', 1)
    exam = get_object_or_404(models.Psat, pk=pk)
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
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    data_statistics = models.ResultStatistics.objects.filter(psat=exam).order_by('id')
    df = pd.DataFrame.from_records(data_statistics.values())

    filename = f'제{exam.round}회_전국모의고사_성적통계.xlsx'
    drop_columns = ['id', 'psat_id']
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
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    student_list = exam_vars.get_student_list()
    df = pd.DataFrame.from_records(student_list.values())

    filename = f'제{exam.round}회_전국모의고사_성적일람표.xlsx'
    drop_columns = ['id', 'created_at', 'password', 'psat_id', 'category_id']
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
    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    qs_problems = exam_vars.get_qs_problems_for_answer_count().order_by('id')
    df = pd.DataFrame.from_records(qs_problems.values())

    filename = f'제{exam.round}회_전국모의고사_문항분석표.xlsx'
    drop_columns = ['id', 'psat_id']
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

    statistics_model = models.ResultStatistics
    answer_count_model = models.ResultAnswerCount
    answer_count_top_model = models.ResultAnswerCountTopRank
    answer_count_mid_model = models.ResultAnswerCountMidRank
    answer_count_low_model = models.ResultAnswerCountLowRank

    predict_statistics_model = models.PredictStatistics
    predict_answer_count_model = models.PredictAnswerCount
    predict_answer_count_top_model = models.PredictAnswerCountTopRank
    predict_answer_count_mid_model = models.PredictAnswerCountMidRank
    predict_answer_count_low_model = models.PredictAnswerCountLowRank

    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    score_model = models.ResultScore
    rank_total_model = models.ResultRankTotal
    rank_category_model = models.ResultRankCategory

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

    def get_qs_student_answer(self, student):
        return models.ResultAnswer.objects.filter(
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

    def get_student_list(self):
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
            self.student_model.objects.filter(psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .order_by('psat__year', 'psat__round', 'rank_total__average')
            .annotate(department=F('category__department'), **annotate_dict)
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
            self.problem_model.objects.filter(psat=self.exam)
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

    def get_data_statistics(self):
        qs_students = (
            self.student_model.objects.filter(psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_total')
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

    def update_statistics(self, data_statistics):
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
                new_query = self.statistics_model.objects.get(psat=self.exam, department=department)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except self.statistics_model.DoesNotExist:
                list_create.append(self.statistics_model(psat=self.exam, **stat_dict))
        update_fields = [
            'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
        ]
        bulk_create_or_update(self.statistics_model, list_create, list_update, update_fields)

        is_updated = True
        message = '통계가 업데이트됐습니다.'

        return is_updated, message

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
