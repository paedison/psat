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
    object: Problem
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
    def my_tag(self) -> ProblemTag | None:
        if self.request.user.is_authenticated:
            return ProblemTag.objects.filter(user=self.request.user, problem=self.problem).first()
        return None

    @property
    def problem_memo(self) -> ProblemMemo | None:
        if self.request.user.is_authenticated:
            return ProblemMemo.objects.filter(user=self.request.user, problem=self.problem).first()
        return None

    def get_problem_url(self, problem_id) -> reverse_lazy:
        return reverse_lazy(f'psat:{self.view_type}_detail', args=[problem_id])

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}Detail',
            'title': self.object.full_title(),
            'target_id': f'{self.view_type}DetailContent',
            'current_url': self.get_problem_url(self.problem_id),
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'problem_id': self.problem_id,
        }


class BaseDetailView(PSATDetailInfoMixIn, DetailView):
    """Represent PSAT base detail view."""
    model = Problem
    template_name = 'psat/problem_detail.html'
    context_object_name = 'problem'

    def get(self, request, *args, **kwargs) -> render:
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated:
            self.update_open_status()
        # self.create_log_for_psat_detail()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        val = self.request.POST.get('difficulty') or self.request.POST.get('answer')
        if self.view_type == 'answer':
            return self.post_answer(request, val, **kwargs)
        else:
            return self.post_other(request, val, **kwargs)

    def post_answer(self, request, answer, **kwargs) -> HttpResponse:
        """Handle POST request when view_type is answer."""
        if answer is None:
            message, html = '<div class="text-danger">정답을 선택해주세요.</div>', ''
        else:
            obj = self.update_evaluation_status(int(answer))
            is_correct = obj.submitted_answer == obj.correct_answer()
            text = ['success', '정답'] if is_correct else ['danger', '오답']
            message = f'<div class="text-{text[0]}">{text[1]}입니다.</div>'
            context = self.get_context_data(**kwargs)
            html = render(request, self.icon_template, context).content.decode('utf-8')
        response = json.dumps({
            'message': message,
            'html': html,
        })
        # self.create_log_for_psat_post_answer(answer)
        return HttpResponse(response, content_type='application/json')

    def post_other(self, request, val, **kwargs) -> HttpResponse:
        """Handle POST request when view_type is not answer."""
        self.update_evaluation_status(val)
        context = self.get_context_data(**kwargs)
        html = render(request, self.icon_template, context).content.decode('utf-8')
        # self.create_log_for_psat_post_other()
        return HttpResponse(html)

    def update_evaluation_status(self, val=None) -> Evaluation:
        """Update POST request when view_type is answer."""
        obj, created = Evaluation.objects.get_or_create(
            user=self.request.user, problem_id=self.problem_id)
        if self.view_type == 'like':
            obj.update_like()
        elif self.view_type == 'rate':
            obj.update_rate(val)
        elif self.view_type == 'answer':
            obj.update_answer(val)
        return obj

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['problem_memo'] = self.problem_memo
        context['my_tag'] = self.my_tag
        context['anchor_id'] = self.problem_id - int(self.object.number)
        context['problem'] = get_evaluation_info(self.request.user, self.object)
        if self.request.method == 'GET':
            self.update_context_data(context)
        return context

    def update_context_data(self, context) -> None:
        prob_data = prob_list = None
        if self.request.user.is_authenticated and self.view_type != 'problem':
            prob_data, prob_list = self.get_prob_data_list()
            list_by_exam = list(
                prob_data.values_list(
                    'exam__id', 'exam__year', 'exam__exam2',
                    'exam__subject', 'number', 'id'))
            list_by_exam_organized = self.organize_list(list_by_exam)
            context['list_data'] = list_by_exam_organized
        prev_prob, next_prob = self.get_prev_next_prob(prob_data, prob_list)
        context['info'] = self.info
        context['prev_prob'] = prev_prob
        context['next_prob'] = next_prob

    def get_prob_data_list(self) -> [Problem, list]:
        problem_filter = Q(evaluation__user=self.request.user)
        field = None
        value = 0
        if self.view_type == 'like':
            field = 'evaluation__is_liked__gte'
            value = 1
        elif self.view_type == 'rate':
            field = 'evaluation__difficulty_rated__gte'
        elif self.view_type == 'answer':
            field = 'evaluation__is_correct__gte'
        problem_filter &= Q(**{field: value})
        prob_data = Problem.objects.filter(problem_filter)
        prob_list = prob_data.values_list('id', flat=True)
        return prob_data, prob_list

    def organize_list(self, input_list) -> list:
        """ Return organized list divided by 5 items. """
        # Create a dictionary to store instances based on the first value
        organized_dict = {}
        for item in input_list:
            key = item[0]
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam2, subject, number, problem_id = item[1:6]
            number, problem_id = int(number), int(problem_id)
            list_item = {
                'exam_name': f"{year}년 '{exam2}' {subject}",
                'problem_number': number,
                'problem_id': problem_id,
                'problem_url': self.get_problem_url(problem_id)
            }
            organized_dict[key].append(list_item)

        # Create a list to store the final organized result
        organized_list = []
        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i + 5]
                organized_list.extend(row)
        return organized_list

    def get_prev_next_prob(self, prob_data=None, prob_list=None) -> [Problem, Problem]:
        problem = Problem.objects
        prev_prob = next_prob = None
        last_id: int = problem.order_by('-id')[0].id
        if self.view_type == 'problem':
            if self.problem_id != 1:
                prev_prob = problem.get(id=self.problem_id - 1)
            if self.problem_id != last_id:
                next_prob = problem.get(id=self.problem_id + 1)
        else:
            page_list = list(prob_list)
            last_id = len(page_list) - 1
            q = page_list.index(self.problem_id)
            if q != 0:
                prev_prob = prob_data.filter(id=page_list[q - 1]).first()
            if q != last_id:
                next_prob = prob_data.filter(id=page_list[q + 1]).first()
        return prev_prob, next_prob

    def update_open_status(self) -> object:
        user, problem_id = self.request.user, self.problem_id
        obj, created = Evaluation.objects.get_or_create(
            user=user, problem_id=problem_id)
        obj.update_open()
        return obj


class ProblemDetailView(BaseDetailView):
    view_type = 'problem'


class LikeDetailView(BaseDetailView):
    view_type = 'like'


class RateDetailView(BaseDetailView):
    view_type = 'rate'


class AnswerDetailView(BaseDetailView):
    view_type = 'answer'


problem_detail_view = ProblemDetailView.as_view()
like_detail_view = LikeDetailView.as_view()
rate_detail_view = RateDetailView.as_view()
answer_detail_view = AnswerDetailView.as_view()
