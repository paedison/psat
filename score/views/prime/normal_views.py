from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from .viewmixins.base_view_mixins import PrimeScoreBaseViewMixin
from .viewmixins.normal_view_mixins import PrimeScoreListViewMixin, PrimeScoreDetailViewMixin


class ListView(LoginRequiredMixin, TemplateView):
    """ Represent information related PrimeTemporaryAnswer and PrimeConfirmedAnswer models. """
    template_name = 'score/prime/score_list.html'
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
        variable = PrimeScoreListViewMixin(self.request, **self.kwargs)

        page_obj, page_range = variable.get_paginator_info()
        info = variable.get_info()

        return {
            # base info
            'info': info,
            'title': 'Score',
            'page_obj': page_obj,
            'page_range': page_range,

            # icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
        }


class DetailView(LoginRequiredMixin, TemplateView):
    template_name = 'score/prime/score_detail.html'
    login_url = settings.LOGIN_URL
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PrimeScoreDetailViewMixin(self.request, **self.kwargs)

        info = variable.get_info()
        all_answers = variable.get_all_answers()
        student_score = variable.get_student_score()  # score, rank, rank_ratio
        all_score_stat = variable.get_all_score_stat()
        all_answer_rates = variable.get_all_answer_rates()

        return {
            # base info
            'info': info,
            'year': variable.year,
            'round': variable.round,
            'title': 'Score',
            'sub_title': variable.sub_title,

            # icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,

            # score_student.html
            'student': variable.student,

            # score_sheet.html, score_chart.html
            'student_score': student_score,
            'stat_total': all_score_stat['전체'],
            'stat_department': all_score_stat['직렬'],

            # score_answers.html
            'answers_eoneo': all_answers['언어'],
            'answers_jaryo': all_answers['자료'],
            'answers_sanghwang': all_answers['상황'],
            'answers_heonbeob': all_answers['헌법'],

            'rates_eoneo': all_answer_rates['언어'],
            'rates_jaryo': all_answer_rates['자료'],
            'rates_sanghwang': all_answer_rates['상황'],
            'rates_heonbeob': all_answer_rates['헌법'],
        }


class PrintView(DetailView):
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


class NoStudentModalView(LoginRequiredMixin, TemplateView):
    """ Represent modal view when there is no PSAT student data. """
    template_name = 'score/prime/snippets/score_modal.html#no_student_modal'
    login_url = settings.LOGIN_URL


class StudentConnectModalView(LoginRequiredMixin, TemplateView):
    """ Represent modal view for creating PSAT student data. """
    template_name = 'score/prime/snippets/score_modal.html#student_connect'
    login_url = settings.LOGIN_URL

    def get_context_data(self, **kwargs) -> dict:
        variable = PrimeScoreBaseViewMixin(self.request, **self.kwargs)

        year, exam_round = self.kwargs['year'], self.kwargs['round']
        prime = variable.category_model.objects.filter(
            year=year, round=exam_round).select_related('exam').first()
        exam = prime.exam.name
        return {
            'header': f'{year}년 대비 제{exam_round}회 {exam} 수험 정보 입력',
            'year': year,
            'round': exam_round,
        }


@login_required
def student_connect_view(request):
    """ Create new PSAT student instance. """
    models = PrimeScoreBaseViewMixin(request=request)
    if request.method == 'POST':
        form = models.student_form(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            year = student.year
            round_ = student.round
            serial = student.serial
            name = student.name
            password = student.password
            try:
                student = models.student_model.objects.get(
                    year=year,
                    round=round_,
                    serial=serial,
                    name=name,
                    password=password,
                )
                student.user_id = request.user.id
                student.save()
                return redirect(reverse_lazy('prime:detail_year_round', args=[year, round_]))
            except models.student_model.DoesNotExist:
                pass


list_view = ListView.as_view()

detail_view = DetailView.as_view()
detail_print_view = PrintView.as_view()

no_student_modal_view = NoStudentModalView.as_view()
student_connect_modal_view = StudentConnectModalView.as_view()
