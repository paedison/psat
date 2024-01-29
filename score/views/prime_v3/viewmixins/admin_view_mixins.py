import io
import zipfile
from urllib.parse import quote

import pandas as pd
import pdfkit
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from score.utils import get_dict_by_sub
from .base_mixins import AdminBaseMixin


class OnlyStaffAllowedMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: any

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('prime:list'))


class ListViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    page_obj: any
    page_range: any

    def get_properties(self):
        super().get_properties()
        
        self.sub_title = f'{self.exam_name} 관리자 페이지'
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
            obj['detail_url'] = reverse_lazy('prime_admin:detail', args=[obj['year'], obj['round']])
        return page_obj, page_range


class DetailViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    current_category: str
    category_list: list
    search_student_name: str
    statistics: list
    answer_count_analysis: list
    page_obj: any
    page_range: any
    student_ids: list
    base_url: str
    pagination_url: str

    def get_properties(self):
        super().get_properties()

        self.sub_title = f'제{self.round}회 {self.exam_name} 관리자 페이지'

        self.current_category = self.get_variable('category') or '전체'
        self.category_list = self.get_category_list()
        self.search_student_name = self.get_variable('student_name')

        self.statistics = self.get_statistics(self.year, self.round)
        self.answer_count_analysis = self.get_answer_count_analysis()

        self.page_obj, self.page_range, self.student_ids = self.get_paginator_info()
        self.base_url = reverse_lazy(
            'prime_admin:catalog_year_round', args=[self.year, self.round])
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

    def get_answer_count_analysis(self):
        answer_count = (
            self.answer_count_model.objects
            .filter(problem__prime__year=self.year, problem__prime__round=self.round)
            .order_by('problem_id')
            .annotate(
                sub=F('problem__prime__subject__abbr'),
                number=F('problem__number'),
                answer_correct=F('problem__answer'))
            .values(
                'sub', 'number', 'answer_correct',
                'count_total', 'count_1', 'count_2','count_3', 'count_4', 'count_5', 'count_0',
                'rate_1', 'rate_2','rate_3', 'rate_4', 'rate_5', 'rate_0')
        )
        for problem in answer_count:
            answer_correct = problem['answer_correct']
            if answer_correct in range(1, 6):
                rate_correct = problem[f'rate_{answer_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(answer_correct)]
                rate_correct = sum(problem[f'rate_{ans}'] for ans in answer_correct_list)
            problem['rate_correct'] = rate_correct
        return get_dict_by_sub(answer_count)

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


class ExportStatisticsToExcelMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        df = pd.DataFrame.from_records(self.statistics)
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


class ExportAnalysisToExcelMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        def get_df(df_target):
            df = pd.DataFrame.from_records(df_target)
            df = df.drop('sub', axis=1)
            df_target_number = df.pop('number')
            df_target_answer_correct = df.pop('answer_correct')
            df_target_rate_correct = df.pop('rate_correct')

            df.insert(0, 'number', df_target_number)
            df.insert(1, 'answer_correct', df_target_answer_correct)
            df.insert(2, 'rate_correct', df_target_rate_correct)

            return df

        df_heonbeob = get_df(self.answer_count_analysis['헌법'])
        df_eoneo = get_df(self.answer_count_analysis['언어'])
        df_jaryo = get_df(self.answer_count_analysis['자료'])
        df_sanghwang = get_df(self.answer_count_analysis['상황'])

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            df_heonbeob.to_excel(writer, sheet_name='헌법', index=False)
            df_eoneo.to_excel(writer, sheet_name='언어', index=False)
            df_jaryo.to_excel(writer, sheet_name='자료', index=False)
            df_sanghwang.to_excel(writer, sheet_name='상황', index=False)

        filename = f'제{self.round}회_전국모의고사_문항분석표.xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportScoresToExcelMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        queryset = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .annotate(
                이름=F('student__name'), 수험번호=F('student__serial'), 직렬=F('student__department__name'),

                헌법_점수=F('score_heonbeob'), 언어_점수=F('score_eoneo'),
                자료_점수=F('score_jaryo'), 상황_점수=F('score_sanghwang'),
                PSAT_총점=F('score_psat'), PSAT_평균=F('score_psat_avg'),

                헌법_전체_석차=F('rank_total_heonbeob'), 언어_전체_석차=F('rank_total_eoneo'),
                자료_전체_석차=F('rank_total_jaryo'), 상황_전체_석차=F('rank_total_sanghwang'),
                PSAT_전체_석차=F('rank_total_psat'),

                헌법_전체_석차_백분율=F('rank_ratio_total_heonbeob'), 언어_전체_석차_백분율=F('rank_ratio_total_eoneo'),
                자료_전체_석차_백분율=F('rank_ratio_total_jaryo'), 상황_전체_석차_백분율=F('rank_ratio_total_sanghwang'),
                PSAT_전체_석차_백분율=F('rank_ratio_total_psat'),

                헌법_직렬_석차=F('rank_department_heonbeob'), 언어_직렬_석차=F('rank_department_eoneo'),
                자료_직렬_석차=F('rank_department_jaryo'), 상황_직렬_석차=F('rank_department_sanghwang'),
                PSAT_직렬_석차=F('rank_department_psat'),

                헌법_직렬_석차_백분율=F('rank_ratio_total_heonbeob'), 언어_직렬_석차_백분율=F('rank_ratio_total_eoneo'),
                자료_직렬_석차_백분율=F('rank_ratio_total_jaryo'), 상황_직렬_석차_백분율=F('rank_ratio_total_sanghwang'),
                PSAT_직렬_석차_백분율=F('rank_ratio_total_psat'),
            )
            .values(
                '이름', '수험번호', '직렬',
                '헌법_점수', '헌법_전체_석차', '헌법_전체_석차_백분율', '헌법_직렬_석차', '헌법_직렬_석차_백분율',
                '언어_점수', '언어_전체_석차', '언어_전체_석차_백분율', '언어_직렬_석차', '언어_직렬_석차_백분율',
                '자료_점수', '자료_전체_석차', '자료_전체_석차_백분율', '자료_직렬_석차', '자료_직렬_석차_백분율',
                '상황_점수', '상황_전체_석차', '상황_전체_석차_백분율', '상황_직렬_석차', '상황_직렬_석차_백분율',
                'PSAT_총점', 'PSAT_평균', 'PSAT_전체_석차', 'PSAT_전체_석차_백분율', 'PSAT_직렬_석차', 'PSAT_직렬_석차_백분율',
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
