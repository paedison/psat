from django.db.models import F, Case, When, Value, CharField, Max
from vanilla import TemplateView

from psat import models as psat_models
from score import models as score_models


class DetailView(TemplateView):
    menu = 'score'
    template_name = 'score/score_detail.html'

    request: any

    def get_template_names(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > main(GET): main page
        :return: str
        """
        base_template = self.template_name
        main_template = f'{base_template}#detail_main'
        return main_template if self.request.htmx else base_template

    @property
    def exam(self):
        exam_id = self.kwargs.get('exam_id')
        return psat_models.Exam.objects.get(id=exam_id)

    def get_problems(self):
        user = self.request.user
        temporary_answers = (
            score_models.TemporaryAnswer.objects
            .filter(user=user, problem__exam=self.exam)
            .order_by('problem__id').select_related('problem')
        )
        problems = (
            self.exam.problems.all()
            .annotate(submitted_answer=Case(
                When(temporary_answers__in=temporary_answers,
                     then=F('temporary_answers__answer')),
                default=Value(''),
                output_field=CharField())
            )
        )
        return problems

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        update_list = {
            'info': info,
            'title': f'{self.exam.full_title} 답안 제출',
            'exam': self.exam,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'problems': self.get_problems(),
        }
        context.update(update_list)
        return context


class SubmitView(TemplateView):
    menu = 'score'
    template_name = 'score/score_detail.html#scored_form'

    def get_scored_problem(self):
        user = self.request.user
        problem_id = self.kwargs.get('problem_id')
        problem = psat_models.Problem.objects.get(id=problem_id)
        answer = int(self.request.POST.get('answer'))

        try:
            scored = score_models.TemporaryAnswer.objects.get(
                user=user, problem=problem)
            scored.answer = answer
        except score_models.TemporaryAnswer.DoesNotExist:
            scored = score_models.TemporaryAnswer.objects.create(
                user=user, problem=problem, answer=answer)
        scored.save()
        return scored

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['scored'] = self.get_scored_problem()
        return context

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ConfirmedView(TemplateView):
    menu = 'score'
    template_name = 'score/score_confirmed.html'

    request: any

    @property
    def exam(self):
        exam_id = self.kwargs.get('exam_id')
        return psat_models.Exam.objects.get(id=exam_id)

    def get_confirmed_answers(self):
        """ Return the ConfirmedAnswer objects. """
        user = self.request.user
        confirmed_times = (
            score_models.ConfirmedAnswer.objects
            .filter(user=user, problem__exam=self.exam)
            .aggregate(Max('confirmed_times'))['confirmed_times__max']
        )
        confirmed = (
            score_models.ConfirmedAnswer.objects
            .filter(user=user, problem__exam=self.exam, confirmed_times=confirmed_times)
            .order_by('problem__id')
        )
        return confirmed

    def get_template_names(self):
        return f'{self.template_name}#detail_main' if self.request.htmx else self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        update_list = {
            'info': info,
            'title': f'{self.exam.full_title} 성적 확인',
            'exam': self.exam,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'confirmed_answers': self.get_confirmed_answers(),
        }
        context.update(update_list)
        return context


detail_view = DetailView.as_view()
submit_view = SubmitView.as_view()
confirmed_view = ConfirmedView.as_view()
