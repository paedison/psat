from django.db.models import F, Case, When, Value, CharField
from django.shortcuts import render, redirect

from psat import models as psat_models
from score import models as score_models


class DetailView:
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    detail_base_template = 'score/score_detail.html'

    def __init__(self, request, exam_id, view_type='detail'):
        self.request: any = request
        self.exam_id: int = exam_id
        self.view_type: str = view_type

    @property
    def template_name(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > main(GET): main page
        :return: str
        """
        base = self.detail_base_template
        main = f'{base}#detail_main'
        scored_form = f'{base}#scored_form'
        if self.view_type == 'detail':
            return main if self.request.htmx else base
        elif self.view_type == 'submit':
            return scored_form

    @property
    def user(self): return self.request.user
    @property
    def exam(self): return psat_models.Exam.objects.get(id=self.exam_id)

    @property
    def problems(self):
        temporary_answers = score_models.TemporaryAnswer.objects.filter(
            user=self.user, problem__exam=self.exam).order_by('problem__id').select_related('problem')

        problems = self.exam.problems.all().annotate(
            submitted_answer=Case(
                When(temporary_answers__in=temporary_answers, then=F('temporary_answers__answer')),
                default=Value(''),  # Set the default value to an empty string or None if needed
                output_field=CharField()  # Define the output field type (CharField in this case)
            )
        )
        return problems

    @property
    def info(self) -> dict:
        """ Get all the info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',  # Different in dashboard views
        }

    @property
    def context(self) -> dict:
        """ Get the context data. """
        return {
            'info': self.info,
            'title': f'{self.exam.full_title} 답안 제출',
            'exam_id': self.exam_id,
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'problems': self.problems,
        }

    def rendering(self) -> render:
        return render(self.request, self.template_name, self.context)


class SubmitView:
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    detail_base_template = 'score/score_detail.html'

    def __init__(self, request, problem_id, view_type='submit'):
        self.request: any = request
        self.problem_id: int = problem_id
        self.view_type: str = view_type

    @property
    def template_name(self) -> str: return f'{self.detail_base_template}#scored_form'
    @property
    def user(self): return self.request.user
    @property
    def problem(self) -> psat_models.Problem: return psat_models.Problem.objects.get(id=self.problem_id)
    @property
    def submitted_answer(self) -> int: return int(self.request.POST.get('answer'))

    @property
    def temporary_ans(self) -> score_models.TemporaryAnswer:
        """ Return the one TemporaryAnswer object. """
        return score_models.TemporaryAnswer.objects.get(user=self.user, problem=self.problem)

    @property
    def scored_problem(self):
        try:
            temporary = score_models.TemporaryAnswer.objects.get(user=self.user, problem=self.problem)
            temporary.answer = self.submitted_answer
        except score_models.TemporaryAnswer.DoesNotExist:
            temporary = score_models.TemporaryAnswer.objects.create(
                user=self.user, problem=self.problem, answer=self.submitted_answer)
        temporary.save()
        return temporary

    @property
    def context(self) -> dict: return {'scored': self.scored_problem}

    def rendering(self) -> render:
        if self.request.method == 'GET':
            return redirect('score:detail', exam_id=self.problem.exam_id)
        else:

            return render(self.request, self.template_name, self.context)


def detail_view(request, exam_id):
    view = DetailView(request, exam_id)
    return view.rendering()


def submit_view(request, problem_id):
    view = SubmitView(request, view_type='submit', problem_id=problem_id)
    return view.rendering()
