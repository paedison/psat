# Python Standard Function Import
import json
import urllib.parse

# Django Core Import
from django.http import HttpResponse

# Custom App Import
from .models import RequestLog, ProblemLog, LikeLog, RateLog, AnswerLog
from psat.models import Evaluation


def create_request_log(request, info=None, extra='') -> HttpResponse:
    """ Create Request Log """
    user_id = request.user.id
    session_key = request.COOKIES.get('sessionid')
    log_url = urllib.parse.unquote(request.get_full_path())
    method = request.method

    if info is None:
        log_type = request.POST.get('info[type]')
        title = request.POST.get('info[title]')
    else:
        log_type = info['type']
        title = info['title']

    extra += request.POST.get('extra', '')
    log_content = f'{log_type}({method}) - {title}{extra}'
    RequestLog.objects.create(
        user_id=user_id,
        session_key=session_key,
        log_url=log_url,
        log_content=log_content)

    response_data = {
        'message': 'logged',
    }
    json_data = json.dumps(response_data)
    return HttpResponse(json_data, content_type='application/json')


def create_log(request, info, page_obj=None) -> None:
    user_id = request.user.id
    session_key = request.COOKIES.get('sessionid')
    log_url = urllib.parse.unquote(request.get_full_path())
    method = request.method

    list_dict = [
        'problemList', 'likeList', 'rateList', 'answerList', 'postList',
        'likeDashboard', 'rateDashboard', 'answerDashboard',
    ]
    detail_dict = ['problemDetail', 'likeDetail', 'rateDetail', 'answerDetail', 'postDetail']
    board_dict = ['postCreate', 'postUpdate', 'commentCreate', 'commentUpdate']
    delete_dict = ['postDelete', 'commentDelete']

    log_type = info.get('type')
    title = info.get('title')
    sub = info.get('sub', '')
    page = page_obj.number if page_obj else 1
    answer = info.get('answer', '')
    problem_id = info.get('problem_id', '')
    post_id = info.get('post_id', '')
    # comment_id = info.get('comment_id', '')
    log_content = f'{log_type}({method}) - {title}'

    if log_type in list_dict:
        log_content += f'({sub} p.{page})'
    elif log_type in detail_dict:
        if method == 'GET':
            if log_type == 'postDetail':
                log_content += f'(Post ID:{post_id})'
            else:
                ProblemLog.objects.create(user_id=user_id, session_key=session_key, problem_id=problem_id)
        elif method == 'POST':
            obj = Evaluation.objects.get(user_id=user_id, problem_id=problem_id)
            if log_type == 'likeDetail':
                log_content += f'(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})'
                LikeLog.objects.create(user_id=user_id, problem_id=problem_id, is_liked=obj.is_liked)
            elif log_type == 'rateDetail':
                log_content += f'(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})'
                RateLog.objects.create(user_id=user_id, problem_id=problem_id, difficulty_rated=obj.difficulty_rated)
            elif log_type == 'answerDetail':
                if answer is None:
                    log_content += '(Answer Trial Failed)'
                else:
                    a, b, c = obj.answered_times, obj.submitted_answer, obj.is_correct
                    log_content += f'(Answered Times: {a}, Submitted Answer: {b}, Is Correct: {c})'
                    AnswerLog.objects.create(user_id=user_id, problem_id=problem_id, submitted_answer=b, is_correct=c)
    elif log_type in board_dict:
        extra1 = [log_type[:i] for i in range(len(log_type)) if log_type[i].isupper()][0].capitalize()
        extra2 = log_type[len(extra1):].capitalize()
        log_content += f'({extra1} {extra2}'
        if method == 'GET':
            log_content += ' Attempt)'
        if method == 'POST':
            log_content += ' Successfully)'
    elif log_type in delete_dict:
        log_content += f'(Post ID {post_id} Deleted Successfully)'

    RequestLog.objects.create(user_id=user_id, session_key=session_key, log_url=log_url, log_content=log_content)
