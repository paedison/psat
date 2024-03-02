import vanilla
from django.utils import timezone

from .normal_views import IndexView
from .utils import get_all_score_stat_sub_dict
from .viewmixins import admin_view_mixins


class ListView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/predict_admin_list.html'

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

        return {
            # base info
            'info': self.info,
            'title': 'Score',
            'sub_title': self.sub_title,
            'exam_list': self.exam_list,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # exam_list
            'exam_page_obj': self.exam_page_obj,
            'exam_page_range': self.exam_page_range,

            # student_list
            'student_page_obj': self.student_page_obj,
            'student_page_range': self.student_page_range,
            'student_base_url': self.student_base_url,
            'student_pagination_url': self.student_pagination_url,

            #
            # # participant_list
            # 'participant_page_obj': self.participant_page_obj,
            # 'participant_page_range': self.participant_page_range,
        }


class ListStudentView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/snippets/list_student_list.html'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'title': 'Score',
            'sub_title': self.sub_title,
            'exam_list': self.exam_list,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # student_list
            'student_page_obj': self.student_page_obj,
            'student_page_range': self.student_page_range,
            'student_base_url': self.student_base_url,
            'student_pagination_url': self.student_pagination_url,
        }


class DetailView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/predict_admin_detail.html'

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

        return {
            # base info
            'info': self.info,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,

            # statistics
            'statistics_page_obj': self.statistics_page_obj,
            'statistics_page_range': self.statistics_page_range,
            'statistics_pagination_url': self.statistics_pagination_url,

            'statistics_virtual_page_obj': self.statistics_virtual_page_obj,
            'statistics_virtual_page_range': self.statistics_virtual_page_range,
            'statistics_virtual_pagination_url': self.statistics_virtual_pagination_url,

            # answer count analysis
            'answer_count_analysis': self.answer_count_analysis,

            # catalog
            'catalog_page_obj': self.catalog_page_obj,
            'catalog_page_range': self.catalog_page_range,
            'catalog_pagination_url': self.catalog_pagination_url,

            'catalog_virtual_page_obj': self.catalog_virtual_page_obj,
            'catalog_virtual_page_range': self.catalog_virtual_page_range,
            'catalog_virtual_pagination_url': self.catalog_virtual_pagination_url,
        }


class StatisticsView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView
):
    template_name = 'predict/v1/admin/snippets/detail_statistics.html#real'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'statistics_page_obj': self.statistics_page_obj,
            'statistics_page_range': self.statistics_page_range,
            'statistics_pagination_url': self.statistics_pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class StatisticsVirtualView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView
):
    template_name = 'predict/v1/admin/snippets/detail_statistics.html#virtual'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'statistics_virtual_page_obj': self.statistics_virtual_page_obj,
            'statistics_virtual_page_range': self.statistics_virtual_page_range,
            'statistics_virtual_pagination_url': self.statistics_virtual_pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class CatalogView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView
):
    template_name = 'predict/v1/admin/snippets/detail_catalog.html#real'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'catalog_page_obj': self.catalog_page_obj,
            'catalog_page_range': self.catalog_page_range,
            'catalog_pagination_url': self.catalog_pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class CatalogVirtualView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView
):
    template_name = 'predict/v1/admin/snippets/detail_catalog.html#virtual'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'round': self.round,

            # page objectives
            'catalog_virtual_page_obj': self.catalog_virtual_page_obj,
            'catalog_virtual_page_range': self.catalog_virtual_page_range,
            'catalog_virtual_pagination_url': self.catalog_virtual_pagination_url,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,
            'icon_search': self.ICON_SEARCH,
        }


class IndividualIndexView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    IndexView,
):
    template_name = 'predict/v1/admin/predict_individual_index.html'

    def get_properties(self):
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.exam = self.get_exam()
        self.sub_title = self.get_sub_title()
        self.units = self.unit_model.objects.filter(exam__abbr=self.ex)
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
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/score_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.answer_uploaded = True
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        context = super().get_context_data(**kwargs)
        context['all_stat'] = self.get_all_stat()
        return context


class UpdateAnswer(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateAnswerMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.answer_uploaded = True
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()

        return {'message': self.update_answer()}


class UpdateScore(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateScoreMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.answer_uploaded = True
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()

        if self.answer_uploaded:
            return {'message': self.update_score()}
        return {'message': '답안이 공개되지 않았습니다.'}


class UpdateStatistics(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateStatisticsMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/snippets/predict_admin_modal.html#update'

    def get_context_data(self, **kwargs):
        self.answer_uploaded = True
        self.category = self.kwargs.get('category')
        self.year = self.kwargs.get('year')
        self.ex = self.kwargs.get('ex')
        self.round = self.kwargs.get('round')

        self.get_properties()

        if self.answer_uploaded:
            return {
                'message': self.update_statistics(),
                'next_url': self.get_next_url()
            }
        return {'message': '답안이 공개되지 않았습니다.'}


class ExportStatisticsToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportStatisticsToExcelMixin,
    vanilla.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportAnalysisToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportAnalysisToExcelMixin,
    vanilla.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportScoresToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportScoresToExcelMixin,
    vanilla.View,
):
    view_type = 'export'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExportTranscriptToPdfView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportTranscriptToPdfViewMixin,
    vanilla.View,
):
    view_type = 'export'


class ExportPredictDataToGoogleSheetView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportPredictDataToGoogleSheetMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/admin/snippets/predict_admin_modal.html#update'

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
catalog_view = CatalogView.as_view()
catalog_virtual_view = CatalogVirtualView.as_view()

print_view = PrintView.as_view()
# individual_student_print_view = IndividualStudentPrintView.as_view()

export_statistics_to_excel_view = ExportStatisticsToExcelView.as_view()
export_analysis_to_excel_view = ExportAnalysisToExcelView.as_view()
export_scores_to_excel_view = ExportScoresToExcelView.as_view()
export_transcript_to_pdf_view = ExportTranscriptToPdfView.as_view()
export_predict_data_to_google_sheet_view = ExportPredictDataToGoogleSheetView.as_view()
