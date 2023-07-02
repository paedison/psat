# Python Standard Function Import

# Django Core Import

# Custom App Import
from common.constants.icon import *
from psat.models import Evaluation

# Third Party Library Import


def get_evaluation_info(request, obj):
    user = request.user

    if user.is_authenticated:
        try:
            target = Evaluation.objects.get(user=user, problem_id=obj.problem_id())

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

