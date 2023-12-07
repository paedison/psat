from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from vanilla import TemplateView

from .viewmixins.base_view_mixins import PrimeScoreBaseViewMixin


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
        context = {
            'header': f'{year}년 대비 제{exam_round}회 {exam} 수험 정보 입력',
            'year': year,
            'round': exam_round,
        }
        return context


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


no_student_modal_view = NoStudentModalView.as_view()
student_connect_modal_view = StudentConnectModalView.as_view()
