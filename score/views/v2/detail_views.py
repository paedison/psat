from django.db.models import F, Case, When, Value, CharField, Max
from vanilla import TemplateView

from reference import models as reference_models
from score import models as score_models


class DetailView(TemplateView):
    menu = 'score'
    template_name = 'score/score_detail.html'

    request: any

    @property
    def user_id(self):
        return self.request.user.id

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
        return reference_models.Psat.objects.get(exam_id=exam_id)

    def get_problems(self):
        temporary_answers = (
            score_models.PsatTemporaryAnswer.objects
            .filter(user_id=self.user_id, problem__exam=self.exam)
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
    template_name = 'score/v2/snippets/score_answers.html#scored_form'

    @property
    def user_id(self):
        return self.request.user.id

    @property
    def problem_id(self):
        return int(self.kwargs.get('problem_id'))

    @property
    def answer(self):
        return int(self.request.POST.get('answer'))

    def get_scored_problem(self):
        try:
            scored = score_models.PsatTemporaryAnswer.objects.get(
                user_id=self.user_id, problem_id=self.problem_id)
            scored.answer = self.answer
        except score_models.PsatTemporaryAnswer.DoesNotExist:
            scored = score_models.PsatTemporaryAnswer.objects.create(
                user_id=self.user_id, problem_id=self.problem_id, answer=self.answer)
        scored.save()
        return scored

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['scored'] = self.get_scored_problem()
        return context

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


detail_view = DetailView.as_view()
submit_view = SubmitView.as_view()
