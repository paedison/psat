from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .normal_views import DetailView
from .viewmixins.admin_view_mixins import PrimeScoreAdminListViewMixin, PrimeScoreAdminDetailViewMixin


class AdminListView(LoginRequiredMixin, TemplateView):
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
        variable = PrimeScoreAdminListViewMixin(self.request, **self.kwargs)

        info = variable.get_info()
        page_obj, page_range = variable.get_paginator_info()

        return {
            # base info
            'info': info,
            'title': 'Score',

            # page objectives
            'page_obj': page_obj,
            'page_range': page_range,

            # Icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
        }


class AdminDetailView(LoginRequiredMixin, TemplateView):
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
        variable = PrimeScoreAdminDetailViewMixin(self.request, **self.kwargs)

        info = variable.get_info()
        page_obj, page_range = variable.get_paginator_info()
        statistics = variable.get_statistics_current()

        return {
            # base info
            'info': info,
            'year': variable.year,
            'round': variable.round,
            'title': 'Score',
            'sub_title': variable.sub_title,

            # score statistics
            'statistics': statistics,

            # page objectives
            'page_obj': page_obj,
            'page_range': page_range,

            # Icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,
        }


class AdminPrintView(AdminDetailView):
    template_name = 'score/prime/score_admin_print.html'
    view_type = 'print'

    def get_context_data(self, **kwargs) -> dict:
        variable = PrimeScoreAdminDetailViewMixin(self.request, **self.kwargs)
        context = super().get_context_data(**kwargs)
        context['all_stat'] = variable.get_all_stat()
        return context


class AdminStudentPrintView(DetailView):
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


admin_list_view = AdminListView.as_view()
admin_detail_view = AdminDetailView.as_view()
admin_print_view = AdminPrintView.as_view()
admin_student_print_view = AdminStudentPrintView.as_view()
