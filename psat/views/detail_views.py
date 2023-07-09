# Python Standard Function Import
import json

# Django Core Import
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView

# Custom App Import
from common.constants.icon import *
from log.views import CreateLogMixIn
from .list_views import EvaluationInfoMixIn, QuerysetFieldMixIn
from ..models import Problem, Evaluation


class PsatDetailInfoMixIn:
    """ Represent PSAT detail information mixin. """
    kwargs: dict
    category: str
    icon_template_dict = {
        'like': 'psat/snippets/icon_like.html',
        'rate': 'psat/snippets/icon_rate.html',
        'answer': 'psat/snippets/icon_answer.html',
    }

    @property
    def problem_id(self) -> int:
        """ Return problem ID. """
        return int(self.kwargs.get('problem_id'))

    @property
    def object(self) -> Problem:
        """ Return detail view object. """
        return Problem.objects.get(id=self.problem_id)

    @property
    def info(self) -> dict:
        """ Return information dictionary of the detail. """
        return {
            'category': self.category,
            'type': f'{self.category}Detail',
            'title': self.object.full_title(),
            'target_id': f'{self.category}DetailContent',
            'icon': ICON_LIST[self.category],
            'color': COLOR_LIST[self.category],
            'problem_id': self.problem_id
        }

    @property
    def icon_template(self) -> str:
        """ Return icon template pathname. """
        return self.icon_template_dict[self.category]


class BaseDetailView(
    PsatDetailInfoMixIn,
    EvaluationInfoMixIn,
    QuerysetFieldMixIn,
    CreateLogMixIn,
    DetailView,
):
    """ Represent PSAT base detail view. """
    model = Problem
    template_name = 'psat/problem_detail.html'
    context_object_name = 'problem'
    pk_url_kwarg = 'problem_id'

    def get(self, request, *args, **kwargs) -> render:
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated:
            self.update_open_status()
        self.create_log_for_psat_detail()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        val = self.request.POST.get('difficulty') or self.request.POST.get('answer')
        if self.category == 'answer':
            return self.post_answer(request, val, **kwargs)
        else:
            return self.post_other(request, val, **kwargs)

    def post_answer(self, request, answer, **kwargs) -> HttpResponse:
        """ Handle POST request when category is answer. """
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
        # create_log(self.request, self.info)
        self.create_log_for_psat_post_answer(answer)
        return HttpResponse(response, content_type='application/json')

    def post_other(self, request, val, **kwargs) -> HttpResponse:
        """ Handle POST request when category is not answer. """
        self.update_evaluation_status(val)
        context = self.get_context_data(**kwargs)
        html = render(request, self.icon_template, context).content.decode('utf-8')
        # create_log(self.request, self.info)
        self.create_log_for_psat_post_other()
        return HttpResponse(html)

    def update_evaluation_status(self, val=None) -> Evaluation:
        """ Update POST request when category is answer. """
        obj, created = Evaluation.objects.get_or_create(
            user=self.request.user, problem_id=self.problem_id)
        if self.category == 'like':
            obj.update_like()
        elif self.category == 'rate':
            obj.update_rate(val)
        elif self.category == 'answer':
            obj.update_answer(val)
        return obj

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['anchor_id'] = self.problem_id - int(self.object.number)
        updated_object = self.get_evaluation_info(self.object)
        context['problem'] = updated_object
        self.update_context_data(context)
        return context

    def update_context_data(self, context) -> None:
        """ Update context data. """
        prob_data = prob_list = None
        if self.request.user.is_authenticated:
            prob_data, prob_list = self.get_prob_data_list()
            list_by_exam = list(
                prob_data.values_list(
                    'exam__id', 'exam__year', 'exam__exam2', 'exam__subject', 'number', 'id'))
            list_by_exam_organized = self.organize_list(list_by_exam)
            context['list_data'] = list_by_exam_organized
        prev_prob, next_prob = self.get_prev_next_prob(prob_data, prob_list)
        context['info'] = self.info
        context['prev_prob'] = prev_prob
        context['next_prob'] = next_prob

    def get_prob_data_list(self) -> [object, object]:
        """ Return problem data and list. """
        field = self.queryset_field[0]
        problem_filter = Q(evaluation__user=self.request.user)
        if self.category != 'problem':
            val = 1 if self.category == 'like' else 0
            problem_filter &= Q(**{field: val})
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
                'exam_name': f"{year}년 '{exam2} {subject}'",
                'problem_number': number,
                'problem_id': problem_id,
                'problem_url': reverse_lazy(f'psat:{self.category}_detail', args=[problem_id])
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

    def get_prev_next_prob(self, prob_data=None, prob_list=None) -> [object, object]:
        """ Return previous and next problems. """
        problem = Problem.objects
        if self.category == 'problem':
            last = problem.order_by('-id')[0].id
            prev_prob = problem.get(id=self.problem_id - 1) if self.problem_id != 1 else ''
            next_prob = problem.get(id=self.problem_id + 1) if self.problem_id != last else ''
        else:
            try:
                page_list = list(prob_list)
                q = page_list.index(self.problem_id)
                last = len(page_list) - 1
                prev_prob = prob_data.get(id=page_list[q - 1]) if q != 0 else ''
                next_prob = prob_data.get(id=page_list[q + 1]) if q != last else ''
            except ValueError:
                prev_prob = next_prob = None
        return prev_prob, next_prob

    def update_open_status(self) -> object:
        """ Update open status. """
        user, problem_id = self.request.user, self.problem_id
        obj, created = Evaluation.objects.get_or_create(user=user, problem_id=problem_id)
        obj.update_open()
        return obj


class ProblemDetailView(BaseDetailView):
    category = 'problem'


class LikeDetailView(BaseDetailView):
    category = 'like'


class RateDetailView(BaseDetailView):
    category = 'rate'


class AnswerDetailView(BaseDetailView):
    category = 'answer'
