from django.utils import timezone
from django.views import generic

from .normal_views_old import IndexView
from a_predict.utils import get_all_score_stat_sub_dict
from .viewmixins import admin_view_mixins, base_mixins


class ListView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/predict_admin_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        exam_list = self.exam_model.objects.all()
        exam_page_obj, exam_page_range = self.get_paginator_info(exam_list)
        student_page_obj, student_page_range = self.get_paginator_info(self.student_list)

        return {
            # base info
            'info': self.info,
            'title': 'Score',
            'sub_title': '성적 예측 [관리자 페이지]',
            'exam_list': self.exam_list,

            # icons
            'icon_menu': self.ICON_MENU['score'],

            # exam_list
            'exam_page_obj': exam_page_obj,
            'exam_page_range': exam_page_range,

            # student_list
            'student_page_obj': student_page_obj,
            'student_page_range': student_page_range,
            'student_pagination_url': self.get_url('list_student'),
        }


class ListStudentView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/snippets/list_student_list.html'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        student_page_obj, student_page_range = self.get_paginator_info(self.student_list)
        return {
            'student_page_obj': student_page_obj,
            'student_page_range': student_page_range,
            'student_pagination_url': self.get_url('list_student'),
        }


class DetailView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/predict_admin_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#admin_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        statistics_page_obj, statistics_page_range = self.get_detail_statistics()
        heonbeob_page_obj, heonbeob_page_range = self.get_sub_answer_count('헌법')
        all_stat = self.get_all_stat()
        catalog_page_obj, catalog_page_range = self.get_paginator_info(all_stat)

        return {
            # base info
            'info': self.info,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.get_sub_title(),

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,

            # statistics
            'statistics_page_obj': statistics_page_obj,
            'statistics_page_range': statistics_page_range,
            'statistics_pagination_url': self.get_url('statistics'),

            # answer count analysis
            'heonbeob_page_obj': heonbeob_page_obj,
            'heonbeob_page_range': heonbeob_page_range,
            'heonbeob_pagination_url': self.get_url('answer_count_heonbeob'),

            # catalog
            'catalog_page_obj': catalog_page_obj,
            'catalog_page_range': catalog_page_range,
            'catalog_pagination_url': self.get_url('catalog'),
        }


class DetailPartialView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    generic.TemplateView,
):

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class StatisticsView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_statistics.html#real'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        statistics_page_obj, statistics_page_range = self.get_detail_statistics()
        return {
            'statistics_page_obj': statistics_page_obj,
            'statistics_page_range': statistics_page_range,
            'statistics_pagination_url': self.get_url('statistics'),
        }


class StatisticsVirtualView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_statistics.html#virtual'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        statistics_virtual_page_obj, statistics_virtual_page_range = self.get_detail_statistics('virtual')
        return {
            'statistics_virtual_page_obj': statistics_virtual_page_obj,
            'statistics_virtual_page_range': statistics_virtual_page_range,
            'statistics_virtual_pagination_url': self.get_url('statistics_virtual'),
        }


class AnswerCountHeonbeobView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_answer_analysis.html#heonbeob'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        heonbeob_page_obj, heonbeob_page_range = self.get_sub_answer_count('헌법')
        return {
            'heonbeob_page_obj': heonbeob_page_obj,
            'heonbeob_page_range': heonbeob_page_range,
            'heonbeob_pagination_url': self.get_url('answer_count_heonbeob'),
        }


class AnswerCountEoneoView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_answer_analysis.html#eoneo'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        eoneo_page_obj, eoneo_page_range = self.get_sub_answer_count('언어')
        return {
            'eoneo_page_obj': eoneo_page_obj,
            'eoneo_page_range': eoneo_page_range,
            'eoneo_pagination_url': self.get_url('answer_count_eoneo'),
        }


class AnswerCountJaryoView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_answer_analysis.html#jaryo'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        jaryo_page_obj, jaryo_page_range = self.get_sub_answer_count('자료')
        return {
            'jaryo_page_obj': jaryo_page_obj,
            'jaryo_page_range': jaryo_page_range,
            'jaryo_pagination_url': self.get_url('answer_count_jaryo'),
        }


class AnswerCountSanghwangView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_answer_analysis.html#sanghwang'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        sanghwang_page_obj, sanghwang_page_range = self.get_sub_answer_count('상황')
        return {
            'sanghwang_page_obj': sanghwang_page_obj,
            'sanghwang_page_range': sanghwang_page_range,
            'sanghwang_pagination_url': self.get_url('answer_count_sanghwang'),
        }


class CatalogView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_catalog.html#real'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        all_stat = self.get_all_stat()
        catalog_page_obj, catalog_page_range = self.get_paginator_info(all_stat)
        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'catalog_page_obj': catalog_page_obj,
            'catalog_page_range': catalog_page_range,
            'catalog_pagination_url': self.get_url('catalog'),
        }


class CatalogVirtualView(DetailPartialView):
    template_name = 'a_predict/admin/snippets/detail_catalog.html#virtual'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        all_virtual_stat = self.get_all_stat('virtual')
        catalog_virtual_page_obj, catalog_virtual_page_range = self.get_paginator_info(all_virtual_stat)
        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'catalog_virtual_page_obj': catalog_virtual_page_obj,
            'catalog_virtual_page_range': catalog_virtual_page_range,
            'catalog_virtual_pagination_url': self.get_url('catalog_virtual'),
        }


class IndividualIndexView(
    base_mixins.OnlyStaffAllowedMixin,
    IndexView,
):
    template_name = 'a_predict/admin/predict_individual_index.html'

    def get_properties(self):
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.exam = self.get_exam()
        self.sub_title = self.get_sub_title()
        self.departments = self.department_model.objects.filter(unit__exam__abbr=self.ex).values()

        user_id = self.kwargs.get('user_id')
        self.student = self.get_student(user_id)  # Check
        self.location = self.get_location()

        self.problem_count_dict = self.get_problem_count_dict()
        self.answer_correct_dict = self.get_answer_correct_dict()

        self.all_answer_count = self.get_all_answer_count()
        self.dataset_answer_student = self.get_dataset_answer_student(self.student)  # Check
        self.answer_student_status = self.get_answer_student_status()
        self.participant_count = self.get_participant_count()

        self.data_answer = self.get_data_answer()
        self.info_answer_student = self.get_info_answer_student()

        self.all_score_stat = {'전체': '', '직렬': ''}
        self.score_student = {}
        self.filtered_all_score_stat = {'전체': '', '직렬': ''}
        self.filtered_score_student = {}

        if timezone.now() > self.exam.answer_open_datetime and self.student:
            statistics_student = self.calculate_score()
            self.all_score_stat = get_all_score_stat_sub_dict(self.get_statistics_qs, self.student)
            self.score_student = self.get_score_student(statistics_student)
            self.update_info_answer_student()
            if statistics_student.student.statistics_virtual.updated_at < self.exam.answer_open_datetime:
                self.filtered_all_score_stat = get_all_score_stat_sub_dict(self.get_filtered_statistics_qs, self.student)
                self.filtered_score_student = self.get_filtered_score_student(statistics_student)


class PrintView(
    DetailView,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/score_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        context = super().get_context_data(**kwargs)
        context['all_stat'] = self.get_all_stat()
        return context


class UpdateAnswer(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateAnswerMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()

        return {'message': self.update_answer()}


class UpdateScore(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateScoreMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()
        return {'message': self.update_score()}


class UpdateStatistics(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateStatisticsMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()

        return {
            'message': self.update_statistics(),
            'next_url': self.get_next_url()
        }


class ExportStatisticsToExcelView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportStatisticsToExcelMixin,
    generic.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportAnalysisToExcelView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportAnalysisToExcelMixin,
    generic.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportScoresToExcelView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportScoresToExcelMixin,
    generic.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportPredictDataToGoogleSheetView(
    base_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportPredictDataToGoogleSheetMixin,
    generic.TemplateView,
):
    template_name = 'a_predict/admin/snippets/predict_admin_modal.html#update'

    def get(self, request, *args, **kwargs):
        self.export_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'message': '구글시트가 업데이트되었습니다.'
        }


list_view = ListView.as_view()
list_student_view = ListStudentView.as_view()

detail_view = DetailView.as_view()

individual_index_view = IndividualIndexView.as_view()

update_answer = UpdateAnswer.as_view()
update_score = UpdateScore.as_view()
update_statistics = UpdateStatistics.as_view()

statistics_view = StatisticsView.as_view()
statistics_virtual_view = StatisticsVirtualView.as_view()

answer_count_heonbeob_view = AnswerCountHeonbeobView.as_view()
answer_count_eoneo_view = AnswerCountEoneoView.as_view()
answer_count_jaryo_view = AnswerCountJaryoView.as_view()
answer_count_sanghwang_view = AnswerCountSanghwangView.as_view()

catalog_view = CatalogView.as_view()
catalog_virtual_view = CatalogVirtualView.as_view()

print_view = PrintView.as_view()
export_statistics_to_excel_view = ExportStatisticsToExcelView.as_view()
export_analysis_to_excel_view = ExportAnalysisToExcelView.as_view()
export_scores_to_excel_view = ExportScoresToExcelView.as_view()
export_predict_data_to_google_sheet_view = ExportPredictDataToGoogleSheetView.as_view()
