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


class ModalView(BaseMixin, TemplateView):
    menu = 'score'
    template_name = 'snippets/modal.html#score_confirmed'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            all_confirmed=False, message='이미 제출한 답안은<br/>수정할 수 없습니다.')
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        temporary = score_models.TemporaryAnswer.objects.filter(
            user=self.user, problem__exam=self.exam).order_by('problem__id')

        if self.exam.problems.count() != temporary.count():
            context = self.get_context_data(
                all_confirmed=False, message='모든 문제의 답안을<br/>제출해주세요.')
        else:
            for temp in temporary:
                # Create new ConfirmedAnswer instance and delete TemporaryAnswer instance
                score_models.ConfirmedAnswer.objects.create(
                    user=self.user, problem=temp.problem, answer=temp.answer)
                temp.delete()
            context = self.get_context_data(
                all_confirmed=True, exam_id=self.exam_id,
                message='답안이 정상적으로<br/>제출되었습니다.')
        return self.render_to_response(context)


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


modal = ModalView.as_view()
confirmed = ConfirmedDetailView.as_view()
