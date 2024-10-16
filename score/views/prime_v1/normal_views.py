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
        return variable.get_context_data()


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
        return variable.get_context_data()


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
                return redirect(reverse_lazy('score_old:prime-detail-year-round', args=[year, round_]))
            except models.student_model.DoesNotExist:
                pass


list_view = ListView.as_view()

detail_view = DetailView.as_view()
detail_print_view = PrintView.as_view()

no_student_modal_view = NoStudentModalView.as_view()
student_connect_modal_view = StudentConnectModalView.as_view()
