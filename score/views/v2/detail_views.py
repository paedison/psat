from vanilla import TemplateView

from score import models as score_models


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


submit_view = SubmitView.as_view()
