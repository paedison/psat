import vanilla
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from . import normal_views
from .viewmixins import admin_view_mixins


class ListView(
    LoginRequiredMixin,
    admin_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v2/score_admin_list.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class DetailView(
    LoginRequiredMixin,
    admin_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v2/score_admin_detail.html'
    login_url = settings.LOGIN_URL

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#admin_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class CatalogView(
    LoginRequiredMixin,
    admin_view_mixins.CatalogViewMixin,
    vanilla.TemplateView
):
    template_name = 'score/prime_v2/score_admin_detail.html#catalog'
    login_url = settings.LOGIN_URL

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class PrintView(
    LoginRequiredMixin,
    admin_view_mixins.PrintViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v2/score_admin_print.html'
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class IndividualStudentPrintView(normal_views.DetailView):
    template_name = 'score/prime_v2/score_individual_print.html'
    view_type = 'print'


class ExportStatisticsToExcelView(
    LoginRequiredMixin,
    admin_view_mixins.ExportStatisticsToExcelViewMixin,
    vanilla.View,
):
    view_type = 'export'


class ExportStudentScoreToExcelView(
    LoginRequiredMixin,
    admin_view_mixins.ExportStudentScoreToExcelViewMixin,
    vanilla.View,
):
    view_type = 'export'


class ExportTranscriptToPdfView(
    LoginRequiredMixin,
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
export_student_score_to_excel_view = ExportStudentScoreToExcelView.as_view()
export_transcript_to_pdf_view = ExportTranscriptToPdfView.as_view()