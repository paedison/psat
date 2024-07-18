import io
import zipfile
from urllib.parse import quote

import pandas as pd
import pdfkit
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponse
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_score_stat
from . import base_mixins


class BaseViewMixin(ConstantIconSet, base_mixins.BaseMixin):
    def get_statistics_qs_list(self, year, exam_round) -> list:
        filter_expr = {
            'student__year': year,
            'student__round': exam_round,
        }
        statistics_qs = (
            self.statistics_model.objects.defer('timestamp')
            .select_related('student', 'student__department').filter(**filter_expr)
        )
        if statistics_qs:
            statistics_qs_list = [{'department': '전체', 'queryset': statistics_qs}]

            department_list = self.department_model.objects.values_list('name', flat=True)
            for department in department_list:
                filter_expr['student__department__name'] = department
                statistics_qs_list.append({'department': department, 'queryset': statistics_qs.filter(**filter_expr)})
            return statistics_qs_list

    def get_statistics(self, year, exam_round) -> list:
        score_statistics_list = []
        statistics_qs_list = self.get_statistics_qs_list(year, exam_round)
        if statistics_qs_list:
            for qs_list in statistics_qs_list:
                statistics_dict = {'department': qs_list['department']}
                statistics_dict.update(get_score_stat(qs_list['queryset']))
                score_statistics_list.append(statistics_dict)
            return score_statistics_list


class ListViewMixin(BaseViewMixin):
    page_obj: any
    page_range: any

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'title': 'Score',

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }

    def get_properties(self):
        super().get_properties()
        self.page_obj, self.page_range = self.get_paginator_info()

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.exam_list, 10)
        page_obj: list[dict] = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        for obj in page_obj:
            statistics = self.get_statistics(obj['year'], obj['round'])
            obj['statistics'] = statistics
            obj['detail_url'] = reverse_lazy('score_old:prime-admin-detail-year-round', args=[obj['year'], obj['round']])
        return page_obj, page_range


class DetailViewMixin(BaseViewMixin):
    sub_title: str
    current_category: str
    category_list: list
    search_student_name: str
    statistics: list
    page_obj: any
    page_range: any
    student_ids: list
    base_url: str
    pagination_url: str

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'year': self.year,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,

            # filtering and searching
            'current_category': self.current_category,
            'category_list': self.category_list,
            'search_student_name': self.search_student_name,

            # score statistics
            'statistics': self.statistics,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'student_ids': self.student_ids,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,
        }

    def get_properties(self):
        super().get_properties()

        self.sub_title = f'제{self.round}회 프라임 모의고사'

        self.current_category = self.get_variable('category') or '전체'
        self.category_list = self.get_category_list()
        self.search_student_name = self.get_variable('student_name')

        self.statistics = self.get_statistics(self.year, self.round)

        self.page_obj, self.page_range, self.student_ids = self.get_paginator_info()
        self.base_url = reverse_lazy(
            'score_old:prime-admin-catalog-year-round', args=[self.year, self.round])
        self.pagination_url = f'{self.base_url}?category={self.current_category}'

    def get_variable(self, variable: str) -> str:
        variable_get = self.request.GET.get(variable, '')
        variable_post = self.request.POST.get(variable, '')
        if variable_get:
            return variable_get
        return variable_post

    def get_category_list(self):
        category_list = ['전체']
        all_category = list(
            self.student_model.objects.filter(year=self.year, round=self.round)
            .order_by('category').values_list('category', flat=True).distinct()
        )
        category_list.extend(all_category)
        return category_list

    def get_all_stat(self):
        qs = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .select_related('student', 'student__department').order_by('rank_total_psat')
        )
        if self.search_student_name:
            return qs.filter(student__name=self.search_student_name)
        if self.current_category and self.current_category != '전체':
            return qs.filter(student__category=self.current_category)
        return qs

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = self.get_all_stat()
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        student_ids = []
        for obj in page_obj:
            student_ids.append(obj.student.id)

        return page_obj, page_range, student_ids


class CatalogViewMixin(DetailViewMixin):
    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'year': self.year,
            'round': self.round,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'student_ids': self.student_ids,

            # filtering and searching
            'current_category': self.current_category,
            'category_list': self.category_list,
            'search_student_name': self.search_student_name,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class PrintViewMixin(DetailViewMixin):
    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['all_stat'] = self.get_all_stat()
        return context


class ExportStatisticsToExcelViewMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()
        statistics = self.get_statistics(self.year, self.round)

        df = pd.DataFrame.from_records(statistics)
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False, engine='xlsxwriter')

        filename = f'제{self.round}회_전국모의고사_성적통계.xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportStudentScoreToExcelViewMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        queryset = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
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

        filename = f'제{self.round}회_전국모의고사_성적일람표.xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class ExportTranscriptToPdfViewMixin(DetailViewMixin):
    page_number: int | str

    def post(self, request, *args, **kwargs):
        from score.views.prime_v2.admin_views import IndividualStudentPrintView
        self.get_properties()

        page_number = request.GET.get('page', 1)
        exam_round = self.round

        # Extract parameters from URL
        student_ids = [int(student_id) for student_id in request.POST.get('student_ids').split(',')]

        # Create a zip file to store the individual PDFs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for student_id in student_ids:
                student = self.student_model.objects.get(id=student_id)
                student_name = student.name
                student_serial = student.serial

                html_content = IndividualStudentPrintView.as_view()(
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
