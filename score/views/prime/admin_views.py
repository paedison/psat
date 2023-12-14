import io
import zipfile
from urllib.parse import quote

import pandas as pd
import pdfkit
import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import HttpResponse

from . import normal_views
from score.utils import get_score_stat_korean
from .viewmixins import admin_view_mixins


class ListView(LoginRequiredMixin, vanilla.TemplateView):
    """ Represent information related PrimeTemporaryAnswer and PrimeConfirmedAnswer models. """
    template_name = 'score/prime/score_admin_list.html'
    login_url = settings.LOGIN_URL
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = admin_view_mixins.ListViewMixin(self.request, **self.kwargs)
        return variable.get_context_data()


class DetailView(LoginRequiredMixin, vanilla.TemplateView):
    template_name = 'score/prime/score_admin_detail.html'
    login_url = settings.LOGIN_URL
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#admin_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = admin_view_mixins.DetailViewMixin(self.request, **self.kwargs)
        return variable.get_context_data()


class CatalogView(LoginRequiredMixin, vanilla.TemplateView):
    template_name = 'score/prime/score_admin_detail.html#catalog'
    login_url = settings.LOGIN_URL
    request: any

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = admin_view_mixins.CatalogViewMixin(self.request, **self.kwargs)
        return variable.get_context_data()


class PrintView(DetailView):
    template_name = 'score/prime/score_admin_print.html'
    view_type = 'print'

    def get_context_data(self, **kwargs) -> dict:
        variable = admin_view_mixins.DetailViewMixin(self.request, **self.kwargs)
        context = super().get_context_data(**kwargs)
        context['all_stat'] = variable.get_all_stat()
        return context


class StudentPrintView(normal_views.DetailView):
    template_name = 'score/prime/score_print_test.html'
    view_type = 'print'


def export_statistics_view(request, **kwargs):
    variable = admin_view_mixins.DetailViewMixin(request, **kwargs)
    year = variable.year
    exam_round = variable.round

    statistics = []
    statistics_qs_list = variable.get_statistics_qs_list(year, exam_round)
    if statistics_qs_list:
        for qs_list in statistics_qs_list:
            statistics_dict = {'직렬': qs_list['department']}
            statistics_dict.update(get_score_stat_korean(qs_list['queryset']))
            statistics.append(statistics_dict)

    df = pd.DataFrame.from_records(statistics)
    excel_data = io.BytesIO()
    df.to_excel(excel_data, index=False, engine='xlsxwriter')

    filename = f'제{exam_round}회_전국모의고사_성적통계.xlsx'
    filename = quote(filename)

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


def export_students_score_view(request, **kwargs):
    variable = admin_view_mixins.DetailViewMixin(request, **kwargs)
    year = variable.year
    exam_round = variable.round

    queryset = (
        variable.statistics_model.objects.filter(student__year=year, student__round=exam_round)
        .annotate(
            이름=F('student__name'), 수험번호=F('student__serial'), 직렬=F('student__department__name'),

            PSAT_총점=F('score_psat'), PSAT_평균=F('score_psat_avg'), 언어_점수=F('score_eoneo'),
            자료_점수=F('score_jaryo'), 상황_점수=F('score_sanghwang'), 헌법_점수=F('score_heonbeob'),

            PSAT_전체_석차=F('rank_total_psat'), 언어_전체_석차=F('rank_total_eoneo'),
            자료_전체_석차=F('rank_total_jaryo'), 상황_전체_석차=F('rank_total_sanghwang'),
            헌법_전체_석차=F('rank_total_heonbeob'),

            PSAT_전체_석차_백분율=F('rank_ratio_total_psat'), 언어_전체_석차_백분율=F('rank_ratio_total_eoneo'),
            자료_전체_석차_백분율=F('rank_ratio_total_jaryo'), 상황_전체_석차_백분율=F('rank_ratio_total_sanghwang'),
            헌법_전체_석차_백분율=F('rank_ratio_total_heonbeob'),

            PSAT_직렬_석차=F('rank_department_psat'), 언어_직렬_석차=F('rank_department_eoneo'),
            자료_직렬_석차=F('rank_department_jaryo'), 상황_직렬_석차=F('rank_department_sanghwang'),
            헌법_직렬_석차=F('rank_department_heonbeob'),

            PSAT_직렬_석차_백분율=F('rank_ratio_total_psat'), 언어_직렬_석차_백분율=F('rank_ratio_total_eoneo'),
            자료_직렬_석차_백분율=F('rank_ratio_total_jaryo'), 상황_직렬_석차_백분율=F('rank_ratio_total_sanghwang'),
            헌법_직렬_석차_백분율=F('rank_ratio_total_heonbeob'),
        )
        .values(
            '이름', '수험번호', '직렬',
            'PSAT_총점', 'PSAT_평균', 'PSAT_전체_석차', 'PSAT_전체_석차_백분율', 'PSAT_직렬_석차', 'PSAT_직렬_석차_백분율',
            '언어_점수', '언어_전체_석차', '언어_전체_석차_백분율', '언어_직렬_석차', '언어_직렬_석차_백분율',
            '자료_점수', '자료_전체_석차', '자료_전체_석차_백분율', '자료_직렬_석차', '자료_직렬_석차_백분율',
            '상황_점수', '상황_전체_석차', '상황_전체_석차_백분율', '상황_직렬_석차', '상황_직렬_석차_백분율',
            '헌법_점수', '헌법_전체_석차', '헌법_전체_석차_백분율', '헌법_직렬_석차', '헌법_직렬_석차_백분율',
        )
    )
    df = pd.DataFrame.from_records(queryset)

    excel_data = io.BytesIO()
    df.to_excel(excel_data, index=False, engine='xlsxwriter')

    filename = f'제{exam_round}회_전국모의고사_성적일람표.xlsx'
    filename = quote(filename)

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def export_transcripts_view(request, *args, **kwargs):
    page_number = request.GET.get('page', 1)

    from .viewmixins import normal_view_mixins
    variable = normal_view_mixins.PrimeScoreDetailViewMixin(request, **kwargs)
    exam_round = variable.round

    # Extract parameters from URL
    student_ids = [int(student_id) for student_id in request.POST.get('student_ids').split(',')]

    # Create a zip file to store the individual PDFs
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for student_id in student_ids:
            student = variable.student_model.objects.get(id=student_id)
            student_name = student.name
            student_serial = student.serial

            html_content = StudentPrintView.as_view()(
                request, student_id=student_id, *args, **kwargs).rendered_content

            # Convert HTML to PDF using pdfkit
            options = {
                '--page-width': '297mm',
                '--page-height': '210mm',
            }
            pdf_file_path = f"제{exam_round}회_전국모의고사_{student_id}_{student_serial}_{student_name}.pdf"
            pdf_content = pdfkit.from_string(html_content, False, options=options)

            # Add the PDF to the zip file
            zip_file.writestr(pdf_file_path, pdf_content)

    filename = f'제{exam_round}회_전국모의고사_성적표_모음_{page_number}.zip'
    filename = quote(filename)

    # Create a response with the zipped content
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


list_view = ListView.as_view()
detail_view = DetailView.as_view()
catalog_view = CatalogView.as_view()

print_view = PrintView.as_view()
student_print_view = StudentPrintView.as_view()
