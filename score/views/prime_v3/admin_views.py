import vanilla

from . import normal_views
from .viewmixins import admin_view_mixins


class ListView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/prime_admin_list.html'

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

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # exam_list
            'exam_page_obj': self.exam_page_obj,
            'exam_page_range': self.exam_page_range,

            # student_list
            'student_page_obj': self.student_page_obj,
            'student_page_range': self.student_page_range,
        }


class DetailView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/prime_admin_detail.html'

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

            # answer analysis
            'answer_count_analysis': self.answer_count_analysis,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'student_ids': self.student_ids,

            # urls
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,
        }


class CatalogView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView
):
    template_name = 'score/prime_v3/snippets_admin/detail_catalog.html'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

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


class PrintView(
    DetailView,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/prime_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['all_stat'] = self.get_all_stat()
        return context


class IndividualStudentPrintView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    normal_views.DetailView
):
    template_name = 'score/prime_v3/prime_individual_print.html'
    view_type = 'print'


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


list_view = ListView.as_view()
detail_view = DetailView.as_view()
catalog_view = CatalogView.as_view()

print_view = PrintView.as_view()
individual_student_print_view = IndividualStudentPrintView.as_view()

export_statistics_to_excel_view = ExportStatisticsToExcelView.as_view()
export_analysis_to_excel_view = ExportAnalysisToExcelView.as_view()
export_scores_to_excel_view = ExportScoresToExcelView.as_view()
export_transcript_to_pdf_view = ExportTranscriptToPdfView.as_view()
