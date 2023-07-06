# Python Standard Function Import
import json
import urllib.parse
from datetime import datetime

# Django Core Import
from django.http import HttpResponse
from django.utils.timezone import make_aware

# Custom App Import
from log.models import RequestLog, ProblemLog, LikeLog, RateLog, AnswerLog
from psat.models import Evaluation


def create_request_log(request, info=None, extra=''):
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


def create_log(request, info, extra=''):
    user_id = request.user.id
    session_key = request.COOKIES.get('sessionid')
    log_url = urllib.parse.unquote(request.get_full_path())
    method = request.method

    log_for_list = ['problemList', 'likeList', 'rateList', 'answerList', 'postList']
    log_for_detail = ['problemDetail', 'likeDetail', 'rateDetail', 'answerDetail', 'postDetail']
    log_for_board = ['postCreate', 'postUpdate', 'commentCreate', 'commentUpdate']
    log_for_delete = ['postDelete', 'commentDelete']

    log_type = info.get('type')
    title = info.get('title')
    sub = info.get('sub', '')
    page = info.get('page', '1')
    answer = info.get('answer', '')
    problem_id = info.get('problem_id', '')
    post_id = info.get('post_id', '')
    comment_id = info.get('comment_id', '')
    request_log_content = f'{log_type}({method}) - {title}'

    if log_type in log_for_list:
        request_log_content += f'({sub} p.{page})'
    elif log_type in log_for_detail:
        if method == 'GET':
            if log_type == 'postDetail':
                request_log_content += f'(Post ID:{post_id})'
            else:
                ProblemLog.objects.create(user_id=user_id, session_key=session_key, problem_id=problem_id)
        elif method == 'POST':
            obj = Evaluation.objects.get(user_id=user_id, problem_id=problem_id)
            if log_type == 'likeDetail':
                request_log_content += f'(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})'
                LikeLog.objects.create(user_id=user_id, problem_id=problem_id, is_liked=obj.is_liked)
            elif log_type == 'rateDetail':
                request_log_content += f'(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})'
                RateLog.objects.create(user_id=user_id, problem_id=problem_id, difficulty_rated=obj.difficulty_rated)
            elif log_type == 'answerDetail':
                if answer is None:
                    request_log_content += '(Answer Trial Failed)'
                else:
                    request_log_content += f'(Answered Times: {obj.answered_times}, Submitted Answer: {obj.submitted_answer}, Is Correct: {obj.is_correct})'
                    AnswerLog.objects.create(user_id=user_id, problem_id=problem_id, submitted_answer=obj.submitted_answer, is_correct=obj.is_correct)
    elif log_type in log_for_board:
        extra1 = [log_type[:i] for i in range(len(log_type)) if log_type[i].isupper()][0].capitalize()
        extra2 = log_type[len(extra1):].capitalize()
        request_log_content += f'({extra1} {extra2}'
        if method == 'GET':
            request_log_content += ' Attempt)'
        if method == 'POST':
            request_log_content += ' Successfully)'
    elif log_type in log_for_delete:
        request_log_content += f'(Post ID {post_id} Deleted Successfully)'

    RequestLog.objects.create(user_id=user_id, session_key=session_key, log_url=log_url, log_content=request_log_content)
