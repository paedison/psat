import json

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from vanilla import DetailView

from common.constants import icon, color
from .list_views import get_evaluation_info
from ..models import Problem, Evaluation, ProblemMemo, ProblemTag


class PSATDetailInfoMixIn:
    """ Represent PSAT detail information mixin. """
    kwargs: dict
    view_type: str
    prob_data: object
    request: WSGIRequest

    icon_container = 'psat/snippets/icon_container.html'

    @property
    def problem_id(self) -> int: return int(self.kwargs.get('problem_id'))
    @property
    def problem(self) -> Problem: return Problem.objects.get(id=self.problem_id)
    @property
    def object(self) -> Problem: return self.problem
    @property
    def icon_template(self) -> str: return f'{self.icon_container}#{self.view_type}'
    @property
    def prob_list(self) -> list: return self.prob_data.values_list('id', flat=True)
    @property
    def prev_prob(self) -> Problem: return self.get_prev_next_prob(self.prob_data, self.prob_list)[0]
    @property
    def next_prob(self) -> Problem: return self.get_prev_next_prob(self.prob_data, self.prob_list)[1]
    @property
    def list_data(self) -> list: return self.get_detail_list(self.prob_data)

    @property
    def evaluation(self) -> Evaluation:
        return Evaluation.objects.get_or_create(user=self.request.user, problem=self.problem)[0]

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
            list_item = {
                'exam_name': f"{prob.exam.year}년 '{prob.exam.exam2}' {prob.exam.subject}",
                'problem_number': prob.number,
                'problem_id': prob.id,
                'problem_url': self.get_reverse_lazy(prob.id)
            }
            organized_dict[key].append(list_item)
        return organized_dict

    def get_prev_next_prob(self, prob_data=None, prob_list=None) -> [Problem, Problem]:
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
            return ProblemTag.objects.filter(user=self.request.user, problem=self.problem).first()
        return None

    @property
    def problem_memo(self) -> ProblemMemo | None:
        if self.request.user.is_authenticated:
            return ProblemMemo.objects.filter(user=self.request.user, problem=self.problem).first()
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
    template_name = 'psat/problem_detail.html'
    context_object_name = 'problem'

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
        return context


class ProblemDetailView(BaseDetailView):
    view_type = 'problem'
    @property
    def prob_data(self) -> object: return Problem.objects.filter(exam=self.problem.exam)


class LikeDetailView(BaseDetailView):
    view_type = 'like'

    @property
    def prob_data(self) -> object:
        return Problem.objects.filter(evaluation__user=self.request.user, evaluation__is_liked__gte=1)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_like()
        context = self.get_context_data(**kwargs)
        html = render(request, self.icon_template, context).content.decode('utf-8')
        return HttpResponse(html)


class RateDetailView(BaseDetailView):
    view_type = 'rate'
    @property
    def difficulty(self) -> str: return self.request.POST.get('difficulty')

    @property
    def prob_data(self) -> object:
        return Problem.objects.filter(
            evaluation__user=self.request.user, evaluation__difficulty_rated__gte=0)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_rate(self.difficulty)
        context = self.get_context_data(**kwargs)
        html = render(request, self.icon_template, context).content.decode('utf-8')
        return HttpResponse(html)


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
        """Handle POST request when view_type is answer."""
        if self.answer is None:
            message, html = '<div class="text-danger">정답을 선택해주세요.</div>', ''
        else:
            self.evaluation.update_answer(self.answer)
            is_correct = self.answer == self.evaluation.correct_answer()
            text = ['success', '정답'] if is_correct else ['danger', '오답']
            message = f'<div class="text-{text[0]}">{text[1]}입니다.</div>'
            context = self.get_context_data(**kwargs)
            html = render(request, self.icon_template, context).content.decode('utf-8')
        response = json.dumps({
            'message': message,
            'html': html,
        })
        return HttpResponse(response, content_type='application/json')


problem_detail_view = ProblemDetailView.as_view()
like_detail_view = LikeDetailView.as_view()
rate_detail_view = RateDetailView.as_view()
answer_detail_view = AnswerDetailView.as_view()
