from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

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

        page_obj, page_range = variable.get_paginator_info()
        info = variable.get_info()

        return {
            'info': info,
            'title': 'Score',
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
        all_answers = variable.get_all_answers()
        all_ranks = variable.get_all_ranks()
        all_stat = variable.get_all_stat()
        all_answer_rates = variable.get_all_answer_rates()

        return {
            # base info
            'info': info,
            'year': variable.year,
            'round': variable.round,
            'title': 'Score',
            'sub_title': variable.sub_title,

            # Icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,

            # score_student.html
            'student': variable.student,

            # score_sheet.html
            'rank_total': all_ranks['전체'],
            'rank_department': all_ranks['직렬'],
            'stat_total': all_stat['전체'],
            'stat_department': all_stat['직렬'],

            # score_answers.html
            'eoneo_answer': all_answers['언어'],
            'jaryo_answer': all_answers['자료'],
            'sanghwang_answer': all_answers['상황'],
            'heonbeob_answer': all_answers['헌법'],

            'eoneo_rates': all_answer_rates['언어'],
            'jaryo_rates': all_answer_rates['자료'],
            'sanghwang_rates': all_answer_rates['상황'],
            'heonbeob_rates': all_answer_rates['헌법'],
        }


class PrintView(AdminDetailView):
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


admin_list_view = AdminListView.as_view()
admin_detail_view = AdminDetailView.as_view()
admin_print_view = PrintView.as_view()
