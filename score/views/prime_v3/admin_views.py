import vanilla

from . import normal_views
from .viewmixins import admin_view_mixins


class ListView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/score_admin_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class DetailView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/score_admin_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#admin_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class CatalogView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.CatalogViewMixin,
    vanilla.TemplateView
):
    template_name = 'score/prime_v3/score_admin_detail.html#catalog'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class PrintView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.PrintViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/score_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class IndividualStudentPrintView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    normal_views.DetailView
):
    template_name = 'score/prime_v3/score_individual_print.html'
    view_type = 'print'


class ExportStatisticsToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportStatisticsToExcelMixin,
    vanilla.View,
):
    view_type = 'export'


class ExportScoresToExcelView(
    admin_view_mixins.OnlyStaffAllowedMixin,
    admin_view_mixins.ExportScoresToExcelMixin,
    vanilla.View,
):
    view_type = 'export'


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
export_scores_to_excel_view = ExportScoresToExcelView.as_view()
export_transcript_to_pdf_view = ExportTranscriptToPdfView.as_view()