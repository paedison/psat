# Python Standard Function Import
import json
from datetime import datetime

# Django Core Import
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import make_aware
from django.views.generic import DetailView

# Custom App Import
from common.constants.icon import *
from psat.models import Exam, Problem, Evaluation
from psat.views.common_views import get_evaluation_info

now = make_aware(datetime.now())
exam = Exam.objects
problem = Problem.objects
evaluation = Evaluation.objects


class BaseDetailView(DetailView):
    model = Problem
    template_name = 'psat/problem_detail.html'
    context_object_name = 'problem'
    pk_url_kwarg = 'problem_id'
    object = title = None
    problem_id = None
    prev_prob = next_prob = None
    info = {}
    like_data = like_list = rate_data = rate_list = answer_data = answer_list = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.problem_id = kwargs.get('problem_id')
        self.object = problem.get(id=self.problem_id)

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
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        self.update_open_status_in_evaluation_model()

        from log.views import create_request_log, create_problem_log
        create_request_log(self.request, self.info)
        create_problem_log(self.request, self.problem_id)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = get_evaluation_info(self.request, self.object)
        context['problem'] = self.object
        context['info'] = self.info
        context['prev_prob'] = self.prev_prob
        context['next_prob'] = self.next_prob

        return context

    def get_prev_next_prob(self, prob_data=None, prob_list=None):
        page_list = list(prob_list)
        curr_index = page_list.index(self.problem_id)
        last_index = len(page_list) - 1
        prev_prob = prob_data.get(id=page_list[curr_index - 1]) if curr_index != 0 else ''
        next_prob = prob_data.get(id=page_list[curr_index + 1]) if curr_index != last_index else ''

        return prev_prob, next_prob

    def update_open_status_in_evaluation_model(self):
        user = self.request.user
        problem_id = self.problem_id
        try:
            obj = evaluation.get(user=user, problem_id=problem_id)
            obj.update_open_status()
        except ObjectDoesNotExist:
            obj = evaluation.create(user=user, problem_id=problem_id, liked_at=now, liked_times=1, is_liked=True)
        return obj


class ProblemDetailView(BaseDetailView):
    def get_prev_next_prob(self, **kwargs):
        prev_prob = next_prob = None
        max_id = problem.order_by('-id')[0].id
        if self.problem_id != 1:
            prev_prob = problem.get(id=self.problem_id - 1)
        if self.problem_id != max_id:
            next_prob = problem.get(id=self.problem_id + 1)

        return prev_prob, next_prob

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anchor_id = self.problem_id - self.object.number
        context['anchor_id'] = anchor_id

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
        }

    def post(self, request, *args, **kwargs):
        obj = self.update_like_status_in_evaluation_model()
        context = self.get_context_data(**kwargs)
        html = render(request, 'psat/snippets/icon_like.html', context).content.decode('utf-8')

        from log.views import create_request_log
        extra = f"(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})"
        create_request_log(request, self.info, extra)

        from log.models import LikeLog
        LikeLog.objects.create(user=request.user, problem_id=obj.problem_id, is_liked=obj.is_liked)

        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['like_data'] = self.like_data
        return context

    def update_like_status_in_evaluation_model(self):
        user = self.request.user
        problem_id = self.problem_id
        try:
            obj = evaluation.get(user=user, problem_id=problem_id)
            obj.update_like_status()
        except ObjectDoesNotExist:
            obj = evaluation.create(user=user, problem_id=problem_id, liked_at=now, liked_times=1, is_liked=True)
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
        }

    def post(self, request, *args, **kwargs):
        difficulty = self.request.POST.get('difficulty')
        obj = self.update_rate_status_in_evaluation_model(difficulty)
        context = self.get_context_data(**kwargs)
        html = render(request, 'psat/snippets/icon_rate.html', context).content.decode('utf-8')

        from log.views import create_request_log
        extra = f"(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})"
        create_request_log(request, self.info, extra)

        from log.models import RateLog
        RateLog.objects.create(user=request.user, problem_id=obj.problem_id, difficulty_rated=obj.difficulty_rated)

        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rate_data'] = self.rate_data
        return context

    def update_rate_status_in_evaluation_model(self, difficulty):
        user = self.request.user
        problem_id = self.problem_id
        try:
            obj = evaluation.get(user=user, problem_id=problem_id)
            obj.update_rate_status(difficulty)
        except ObjectDoesNotExist:
            obj = evaluation.create(user=user, problem_id=problem_id, rated_at=now, rated_times=1, difficulty_rated=difficulty)
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
        }

    def post(self, request, *args, **kwargs):
        answer = int(self.request.POST.get('answer'))
        obj, message = self.update_answer_status_in_evaluation_model(answer)
        context = self.get_context_data(**kwargs)
        html = render(request, 'psat/snippets/icon_answer.html', context).content.decode('utf-8')
        response_data = {
            'message': message,
            'html': html,
        }
        json_data = json.dumps(response_data)

        from log.views import create_request_log
        extra = f"(Answered Times: {obj.answered_times}, Submitted Answer: {obj.submitted_answer}, Is Correct: {obj.is_correct})"
        create_request_log(request, self.info, extra)

        from log.models import AnswerLog
        AnswerLog.objects.create(user=request.user, problem_id=obj.problem_id, submitted_answer=obj.submitted_answer, is_correct=obj.is_correct)

        return HttpResponse(json_data, content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer_data'] = self.answer_data
        return context

    def update_answer_status_in_evaluation_model(self, answer):
        user = self.request.user
        problem_id = self.problem_id
        obj = ''
        correct_message = '<div class="text-success">정답입니다.</div>'
        wrong_message = '<div class="text-danger">오답입니다.</div>'
        warning_message = '<div class="text-danger">정답을 선택해주세요.</div>'

        if answer:
            try:
                obj = evaluation.get(user=user, problem_id=problem_id)
                obj.update_answer_status(answer)
            except ObjectDoesNotExist:
                obj = evaluation.create(user=user, problem_id=problem_id, answered_at=now, answered_times=1, submitted_answer=answer)
                obj.save()
            if obj.submitted_answer == obj.correct_answer():
                message = correct_message
            else:
                message = wrong_message
        else:
            message = warning_message

        return obj, message

    def get_prev_next_prob(self, **kwargs):
        return super().get_prev_next_prob(self.answer_data, self.answer_list)
