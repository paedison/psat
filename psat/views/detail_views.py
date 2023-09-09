import json

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from vanilla import DetailView, TemplateView

from common.constants import icon, color
from .list_views import get_evaluation_info
from ..models import Problem, Evaluation, ProblemMemo, ProblemTag


class PSATDetailInfoMixIn:
    """ Represent PSAT detail information mixin. """
    kwargs: dict
    view_type: str
    prob_data: Problem.objects
    request: any

    icon_container = 'psat/snippets/icon_container.html'
    base_template = 'psat/problem_detail.html'

    @property
    def problem_id(self) -> int: return int(self.kwargs.get('problem_id'))
    @property
    def problem(self) -> Problem: return Problem.objects.get(id=self.problem_id)
    @property
    def object(self) -> Problem: return self.problem
    @property
    def icon_id(self) -> str: return self.request.GET.get('id')
    @property
    def icon_template(self) -> str: return f'{self.icon_container}#{self.view_type}'
    @property
    def prob_list(self) -> list: return self.prob_data.values_list('id', flat=True)
    @property
    def list_data(self) -> list: return self.get_detail_list(self.prob_data)

    @property
    def prev_prob(self) -> Problem:
        return self.get_probs(self.prob_data, self.prob_list)[0]

    @property
    def next_prob(self) -> Problem:
        return self.get_probs(self.prob_data, self.prob_list)[1]

    @property
    def evaluation(self) -> Evaluation:
        return Evaluation.objects.get_or_create(
            user=self.request.user, problem=self.problem)[0]

    def get_detail_list(self, prob_data: object) -> list:
        organized_dict: dict = self.get_organized_dict(prob_data)
        return get_organized_list(organized_dict)

    def get_organized_dict(self, prob_data: object) -> dict:
        """ Return a dictionary sorted by exam. """
        organized_dict = {}
        for prob in prob_data:
            key = prob.exam.id
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam2, subject = prob.exam.year, prob.exam.exam2, prob.exam.subject
            list_item = {
                'exam_name': f"{year}년 '{exam2}' {subject}",
                'problem_number': prob.number,
                'problem_id': prob.id,
                'problem_url': self.get_reverse_lazy(prob.id)
            }
            organized_dict[key].append(list_item)
        return organized_dict

    def get_probs(self, prob_data=None, prob_list=None) -> [Problem, Problem]:
        prev_prob = next_prob = None
        page_list = list(prob_list)
        last_id = len(page_list) - 1
        q = page_list.index(self.problem_id)
        if q != 0:
            prev_prob = prob_data.filter(id=page_list[q - 1]).first()
        if q != last_id:
            next_prob = prob_data.filter(id=page_list[q + 1]).first()
        return prev_prob, next_prob

    @property
    def my_tag(self) -> ProblemTag | None:
        if self.request.user.is_authenticated:
            return ProblemTag.objects.filter(user=self.request.user,
                                             problem=self.problem).first()
        return None

    @property
    def problem_memo(self) -> ProblemMemo | None:
        if self.request.user.is_authenticated:
            return ProblemMemo.objects.filter(user=self.request.user,
                                              problem=self.problem).first()
        return None

    def get_reverse_lazy(self, problem_id) -> reverse_lazy:
        return reverse_lazy(f'psat:{self.view_type}_detail', args=[problem_id])

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}Detail',
            'title': self.object.full_title(),
            'current_url': self.get_reverse_lazy(self.problem_id),
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'problem_id': self.problem_id,
        }


def get_organized_list(target: dict) -> list:
    """ Return organized list divided by 5 items. """
    organized_list = []
    for key, items in target.items():
        num_empty_instances = 5 - (len(items) % 5)
        if num_empty_instances < 5:
            items.extend([None] * num_empty_instances)
        for i in range(0, len(items), 5):
            row = items[i:i + 5]
            organized_list.extend(row)
    return organized_list


class BaseDetailView(PSATDetailInfoMixIn, DetailView):
    """Represent PSAT base detail view."""
    model = Problem
    context_object_name = 'problem'

    @property
    def template_name(self):
        if self.request.method == 'GET':
            return self.base_template
        elif self.request.method == 'POST':
            return self.icon_template

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated:
            self.evaluation.update_open()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['problem_memo'] = self.problem_memo
        context['my_tag'] = self.my_tag
        context['anchor_id'] = self.problem_id - int(self.object.number)
        context['problem'] = get_evaluation_info(self.request.user, self.object)
        if self.request.method == 'GET':
            context['prev_prob'] = self.prev_prob
            context['next_prob'] = self.next_prob
            context['list_data'] = self.list_data
        if self.request.htmx:
            icon_id = self.request.GET.get('id')
            context['problem_id'] = self.problem_id
            context['icon_id'] = icon_id
        return context


class ProblemDetailView(BaseDetailView):
    view_type = 'problem'
    @property
    def prob_data(self): return Problem.objects.filter(exam=self.problem.exam)


class LikeDetailView(BaseDetailView):
    view_type = 'like'

    @property
    def prob_data(self):
        return Problem.objects.filter(evaluation__user=self.request.user,
                                      evaluation__is_liked__gte=1)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_like()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RateDetailView(BaseDetailView):
    view_type = 'rate'
    @property
    def difficulty(self) -> int: return int(self.request.POST.get('difficulty'))

    @property
    def template_name(self):
        if self.request.method == 'GET':
            return self.base_template
        elif self.request.method == 'POST':
            return self.icon_template

    @property
    def prob_data(self):
        return Problem.objects.filter(evaluation__user=self.request.user,
                                      evaluation__difficulty_rated__gte=0)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_rate(self.difficulty)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class AnswerDetailView(BaseDetailView):
    view_type = 'answer'

    @property
    def answer(self) -> int | None:
        answer = self.request.POST.get('answer')
        answer = int(answer) if answer else None
        return answer

    @property
    def prob_data(self) -> object:
        return Problem.objects.filter(
            evaluation__user=self.request.user, evaluation__is_correct__gte=0)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_answer(self.answer)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RateDetailModalView(PSATDetailInfoMixIn, TemplateView):
    template_name = 'psat/snippets/modal_container.html#rate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem_id'] = self.problem_id
        context['icon_id'] = self.icon_id
        return context


class AnswerDetailModalView(PSATDetailInfoMixIn, TemplateView):
    template_name = 'psat/snippets/modal_container.html#answer'

    @property
    def answer(self) -> int | None:
        answer = self.request.POST.get('answer')
        answer = int(answer) if answer else None
        return answer

    @property
    def is_correct(self) -> bool | None:
        return None if self.answer is None else (
                self.answer == self.evaluation.correct_answer())

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = self.answer
        context['is_correct'] = self.is_correct
        context['problem_id'] = self.problem_id
        return context


problem_detail_view = ProblemDetailView.as_view()
like_detail_view = LikeDetailView.as_view()
rate_detail_view = RateDetailView.as_view()
answer_detail_view = AnswerDetailView.as_view()
rate_detail_modal_view = RateDetailModalView.as_view()
answer_detail_modal_view = AnswerDetailModalView.as_view()
