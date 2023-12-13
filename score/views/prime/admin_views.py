from io import BytesIO

import pandas as pd
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import HttpResponse
from vanilla import TemplateView, View

from score.utils import get_score_stat_korean
from .normal_views import DetailView
from .viewmixins.admin_view_mixins import PrimeScoreAdminListViewMixin, PrimeScoreAdminDetailViewMixin, \
    PrimeScoreAllStudentPrintViewMixin


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
        return variable.get_context_data()


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
        return variable.get_context_data()


class AdminPrintView(AdminDetailView):
    template_name = 'score/prime/score_admin_print.html'
    view_type = 'print'

    def get_context_data(self, **kwargs) -> dict:
        variable = PrimeScoreAdminDetailViewMixin(self.request, **self.kwargs)
        context = super().get_context_data(**kwargs)
        context['all_stat'] = variable.get_all_stat()
        return context


class AdminStudentPrintView(DetailView):
    template_name = 'score/prime/score_print_test.html'
    view_type = 'print'


class AdminAllStudentPrintView(View):
    view_type = 'print'

    def post(self, request, *args, **kwargs):
        variable = PrimeScoreAllStudentPrintViewMixin(request, **kwargs)
        return variable.post(request, *args, **kwargs)


def export_statistics_view(request, **kwargs):
    variable = PrimeScoreAdminDetailViewMixin(request, **kwargs)
    year = variable.year
    exam_round = variable.round

    statistics = []
    statistics_qs_list = variable.get_statistics_qs_list(year, exam_round)
    if statistics_qs_list:
        for qs_list in statistics_qs_list:
            statistics_dict = {'직렬': qs_list['department']}
            statistics_dict.update(get_score_stat_korean(qs_list['queryset']))
            statistics.append(statistics_dict)

    df = pd.DataFrame.from_records(statistics)
    excel_data = BytesIO()
    df.to_excel(excel_data, index=False, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=score_statistics.xlsx'
    response['Content-Disposition'] = f'attachment; filename={year}_{exam_round}_score_statistics.xlsx'

    return response


def export_students_score_view(request, **kwargs):
    variable = PrimeScoreAdminDetailViewMixin(request, **kwargs)
    year = variable.year
    exam_round = variable.round

    queryset = (
        variable.statistics_model.objects
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

    excel_data = BytesIO()
    df.to_excel(excel_data, index=False, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={year}_{exam_round}_score_catalog.xlsx'

    return response


admin_list_view = AdminListView.as_view()
admin_detail_view = AdminDetailView.as_view()
admin_print_view = AdminPrintView.as_view()
admin_student_print_view = AdminStudentPrintView.as_view()
admin_all_student_print_view = AdminAllStudentPrintView.as_view()
