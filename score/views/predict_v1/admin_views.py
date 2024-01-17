import vanilla

from .viewmixins import admin_view_mixins


class TestView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.TestViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/predict_v1/predict_admin_test.html'

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
            'answer_uploaded': self.answer_uploaded,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'exam': self.exam_name,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            'answer_data': self.answer_data,
        }


class IndexView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.IndexViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/predict_v1/predict_admin_index.html'

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


class CatalogView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.IndexViewMixin,
    vanilla.TemplateView
):
    template_name = 'score/predict_v1/score_admin_detail.html#catalog'

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
    IndexView,
    vanilla.TemplateView,
):
    template_name = 'score/predict_v1/score_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['all_stat'] = self.get_all_stat()
        return context


# class IndividualStudentPrintView(
#     admin_view_mixins.OnlyStaffAllowedMixin,
#     normal_views.DetailView
# ):
#     template_name = 'score/predict_v1/score_individual_print.html'
#     view_type = 'print'


class UpdateScore(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.UpdateScoreMixin,
    vanilla.TemplateView,
):
    template_name = 'score/predict_v1/snippets/predict_modal.html#update_score'

    def get_context_data(self, **kwargs):
        self.get_properties()

        return {'message': self.update_score()}


class ExportStatisticsToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportStatisticsToExcelMixin,
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


index_view = IndexView.as_view()
test_view = TestView.as_view()
update_score = UpdateScore.as_view()

catalog_view = CatalogView.as_view()

print_view = PrintView.as_view()
# individual_student_print_view = IndividualStudentPrintView.as_view()

export_statistics_to_excel_view = ExportStatisticsToExcelView.as_view()
export_scores_to_excel_view = ExportScoresToExcelView.as_view()
export_transcript_to_pdf_view = ExportTranscriptToPdfView.as_view()
