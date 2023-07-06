# Python Standard Function Import
import json
from datetime import datetime

# Django Core Import
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import DetailView

# Custom App Import
from common.constants.icon import *
from log.views import create_log
from psat.models import Exam, Problem, Evaluation
from psat.views.common_views import get_evaluation_info

now = make_aware(datetime.now())
exam = Exam.objects
problem = Problem.objects
evaluation = Evaluation.objects

icon_like_template = 'psat/snippets/icon_like.html'
icon_rate_template = 'psat/snippets/icon_rate.html'
icon_answer_template = 'psat/snippets/icon_answer.html'


class BaseDetailView(DetailView):
    model = Problem
    template_name = 'psat/problem_detail.html'
    context_object_name = 'problem'
    pk_url_kwarg = 'problem_id'
    object = title = problem_id = None
    info = {}
    like_data = like_list = rate_data = rate_list = answer_data = answer_list = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.problem_id = kwargs.get('problem_id')
        self.object = problem.get(id=self.problem_id)

        if self.request.user.is_authenticated:
            self.like_data = problem.filter(evaluation__user=self.request.user, evaluation__is_liked=True)
            self.rate_data = problem.filter(evaluation__user=self.request.user, evaluation__difficulty_rated__gte=1)
            self.answer_data = problem.filter(evaluation__user=self.request.user, evaluation__is_correct__gte=0)
            self.like_list = self.like_data.values_list('id', flat=True)
            self.rate_list = self.rate_data.values_list('id', flat=True)
            self.answer_list = self.answer_data.values_list('id', flat=True)

        self.title = self.object.full_title()
        self.info = {
            'category': 'problem',
            'type': 'problemDetail',
            'title': self.title,
            'target_id': 'problemDetailContent',
            'icon': MENU_PROBLEM_ICON,
            'color': 'primary',
            'problem_id': self.problem_id,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated:
            self.update_open_status_in_evaluation_model()
        create_log(self.request, self.info)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = get_evaluation_info(self.request, self.object)
        prev_prob, next_prob = self.get_prev_next_prob()
        context['problem'] = self.object
        context['info'] = self.info
        context['prev_prob'] = prev_prob
        context['next_prob'] = next_prob
        return context

    def get_prev_next_prob(self, prob_data=None, prob_list=None):
        page_list = list(prob_list)
        try:
            curr_index = page_list.index(self.problem_id)
            last_index = len(page_list) - 1
            prev_prob = prob_data.get(id=page_list[curr_index - 1]) if curr_index != 0 else ''
            next_prob = prob_data.get(id=page_list[curr_index + 1]) if curr_index != last_index else ''
        except ValueError:
            prev_prob = next_prob = None
        return prev_prob, next_prob

    def update_open_status_in_evaluation_model(self):
        user, problem_id = self.request.user, self.problem_id
        obj, created = evaluation.get_or_create(user=user, problem_id=problem_id)
        obj.update_open_status()
        return obj


class ProblemDetailView(BaseDetailView):
    def get_prev_next_prob(self, **kwargs):
        max_id = problem.order_by('-id')[0].id
        prev_prob = problem.get(id=self.problem_id - 1) if self.problem_id != 1 else ''
        next_prob = problem.get(id=self.problem_id + 1) if self.problem_id != max_id else ''
        return prev_prob, next_prob

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anchor_id'] = self.problem_id - self.object.number
        return context


class LikeDetailView(BaseDetailView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'like',
            'type': 'likeDetail',
            'title': self.title,
            'target_id': 'likeDetailContent',
            'icon': SOLID_HEART_ICON,
            'color': 'danger',
            'problem_id': self.problem_id,
        }

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.update_like_status_in_evaluation_model()
        context = self.get_context_data(**kwargs)
        html = render(request, icon_like_template, context).content.decode('utf-8')
        create_log(self.request, self.info)
        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_by_exam = list(self.like_data.values_list('exam__id', 'exam__year', 'exam__exam2', 'exam__subject', 'number', 'id'))
        list_by_exam_organized = organize_list(list_by_exam, 'like')
        context['list_data'] = list_by_exam_organized
        context['like_data'] = self.like_data
        return context

    def update_like_status_in_evaluation_model(self):
        user, problem_id = self.request.user, self.problem_id
        obj, created = evaluation.get_or_create(user=user, problem_id=problem_id)
        obj.update_like_status()
        return obj

    def get_prev_next_prob(self, **kwargs):
        return super().get_prev_next_prob(self.like_data, self.like_list)


class RateDetailView(BaseDetailView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'rate',
            'type': 'rateDetail',
            'title': self.title,
            'target_id': 'rateDetailContent',
            'icon': SOLID_STAR_ICON,
            'color': 'warning',
            'problem_id': self.problem_id,
        }

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        difficulty = self.request.POST.get('difficulty')
        self.update_rate_status_in_evaluation_model(difficulty)
        context = self.get_context_data(**kwargs)
        html = render(request, icon_rate_template, context).content.decode('utf-8')
        create_log(self.request, self.info)
        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rate_data'] = self.rate_data
        list_by_exam = list(self.rate_data.values_list('exam__id', 'exam__year', 'exam__exam2', 'exam__subject', 'number', 'id'))
        list_by_exam_organized = organize_list(list_by_exam, 'rate')
        context['list_data'] = list_by_exam_organized
        return context

    def update_rate_status_in_evaluation_model(self, difficulty):
        user, problem_id = self.request.user, self.problem_id
        obj, created = evaluation.get_or_create(user=user, problem_id=problem_id)
        obj.update_rate_status(difficulty)
        return obj

    def get_prev_next_prob(self, **kwargs):
        return super().get_prev_next_prob(self.rate_data, self.rate_list)


class AnswerDetailView(BaseDetailView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'answer',
            'type': 'answerDetail',
            'title': self.title,
            'target_id': 'answerDetailContent',
            'icon': SOLID_CHECK_ICON,
            'color': 'success',
            'problem_id': self.problem_id,
        }

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        answer = self.info['answer'] = self.request.POST.get('answer')
        if answer is None:
            message, html = '<div class="text-danger">정답을 선택해주세요.</div>', ''
        else:
            obj, message = self.update_answer_status_in_evaluation_model(int(answer))
            context = self.get_context_data(**kwargs)
            html = render(request, icon_answer_template, context).content.decode('utf-8')
        create_log(self.request, self.info)
        response = json.dumps({
            'message': message,
            'html': html,
        })
        return HttpResponse(response, content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer_data'] = self.answer_data
        list_by_exam = list(self.answer_data.values_list('exam__id', 'exam__year', 'exam__exam2', 'exam__subject', 'number', 'id'))
        list_by_exam_organized = organize_list(list_by_exam, 'answer')
        context['list_data'] = list_by_exam_organized
        return context

    def update_answer_status_in_evaluation_model(self, answer):
        user, problem_id = self.request.user, self.problem_id
        obj, created = evaluation.get_or_create(user=user, problem_id=problem_id)
        obj.update_answer_status(answer)

        is_correct = obj.submitted_answer == obj.correct_answer()
        text = ['success', '정답'] if is_correct else ['danger', '오답']
        message = f'<div class="text-{text[0]}">{text[1]}입니다.</div>'
        return obj, message

    def get_prev_next_prob(self, **kwargs):
        return super().get_prev_next_prob(self.answer_data, self.answer_list)


def organize_list(input_list, detail_type):
    # Create a dictionary to store instances based on the first value
    organized_dict = {}
    for item in input_list:
        key = item[0]
        if key not in organized_dict:
            organized_dict[key] = []
        list_item = {
            'exam_name': f"{item[1]}년 '{item[2]} {item[3]}'",
            'problem_number': int(item[4]),
            'problem_id': int(item[5]),
            'problem_url': reverse_lazy(f'psat:{detail_type}_detail', args=[int(item[5])])
        }
        organized_dict[key].append(list_item)

    # Create a list to store the final organized result
    organized_list = []
    for key, items in organized_dict.items():
        num_empty_instances = 5 - (len(items) % 5)
        if num_empty_instances < 5:
            items.extend([None] * num_empty_instances)
        for i in range(0, len(items), 5):
            row = items[i:i+5]
            organized_list.extend(row)

    return organized_list
