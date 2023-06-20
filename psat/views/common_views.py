# Python Standard Function Import
from datetime import datetime

# Django Core Import
from django.contrib.sessions.backends import db
from django.utils.timezone import make_aware

# Custom App Import
from common.constants.icon import *
from psat.models import Exam, Problem, Evaluation

# Third Party Library Import

now = make_aware(datetime.now())
exam = Exam.objects
problem = Problem.objects
evaluation = Evaluation.objects

custom_urls = {
    'list': '/psat/',
    'detail': '/psat/detail/',
    'like': '/psat/like/',
    'rate': '/psat/rate/',
    'answer': '/psat/answer/',
}

custom_icons ={
    'solid_heart': '<i class="fa-solid fa-heart"></i>',
    'empty_heart': '<i class="fa-regular fa-heart"></i>',
    'solid_star': '<i class="fa-solid fa-star"></i>',
    'empty_star': '<i class="fa-regular fa-star"></i>',
    'solid_check': '<i class="fa-solid fa-circle-check"></i>',
    'empty_xmark': '<i class="fa-solid fa-circle-xmark"></i>',
}


def get_evaluation_info(request, obj):
    user = request.user

    if user.is_authenticated:
        try:
            target = evaluation.get(user=user, problem_id=obj.problem_id())

            obj.opened_at = target.opened_at
            obj.opened_times = target.opened_times

            obj.liked_at = target.liked_at
            obj.is_liked = target.is_liked
            obj.like_icon = target.like_icon()

            obj.rated_at = target.rated_at
            obj.difficulty_rated = target.difficulty_rated
            obj.rate_icon = target.rate_icon()

            obj.answered_at = target.answered_at
            obj.submitted_answered = target.submitted_answer
            obj.is_correct = target.is_correct
            obj.answer_icon = target.answer_icon()

        except Evaluation.DoesNotExist:
            obj.opened_at = None
            obj.opened_times = 0

            obj.liked_at = None
            obj.is_liked = None
            obj.like_icon = EMPTY_HEART_ICON

            obj.rated_at = None
            obj.difficulty_rated = None
            obj.rate_icon = STAR0_ICON

            obj.answered_at = None
            obj.submitted_answered = None
            obj.is_correct = None
            obj.answer_icon = ''
    return obj


def start_session_for_anonymous_user(request):
    if not request.user.is_authenticated and not request.session.session_key:
        session_engine = db.SessionStore()
        session_engine.create()
        request.session = session_engine


def create_log(request, info_type, log_url, log_type='open', log_content=''):
    _user = request.user
    _id = request.session.session_key

    # if _user.is_authenticated:
    #     log.create(
    #         user=_user,
    #         info_type=info_type,
    #         log_url=log_url,
    #         log_type=log_type,
    #         log_content=log_content,
    #     )
    # else:
    #     anonymous_log.create(
    #         session_id=_id,
    #         info_type=info_type,
    #         log_url=log_url,
    #         log_type=log_type,
    #         log_content=log_content,
    #     )



