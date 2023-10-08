from django.db.models import Max
from vanilla import TemplateView

from psat import models as psat_models
from score import models as score_models


class BaseMixin:
    request: any
    kwargs: dict
    @property
    def user(self): return self.request.user
    @property
    def exam_id(self): return self.kwargs.get('exam_id')
    @property
    def exam(self): return psat_models.Exam.objects.get(id=self.exam_id)


class ConfirmedDetailView(BaseMixin, TemplateView):
    menu = 'score'
    view_type = 'confirmed'
    template_name = 'score/score_confirmed.html'

    @property
    def confirmed_answers(self) -> score_models.ConfirmedAnswer.objects:
        """ Return the ConfirmedAnswer objects. """
        confirmed_times = score_models.ConfirmedAnswer.objects.filter(
            user=self.user, problem__exam=self.exam).aggregate(
            Max('confirmed_times'))['confirmed_times__max']
        return score_models.ConfirmedAnswer.objects.filter(
            user=self.user, problem__exam=self.exam, confirmed_times=confirmed_times
        ).order_by('problem__id')

    def get_template_names(self):
        return f'{self.template_name}#detail_main' if self.request.htmx else self.template_name

    @property
    def info(self) -> dict:
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',  # Different in dashboard views
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_list = {
            'title': f'{self.exam.full_title} 성적 확인',
            'exam_id': self.exam_id,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'confirmed_answers': self.confirmed_answers,
        }
        context.update(update_list)
        return context


confirmed_view = ConfirmedDetailView.as_view()
