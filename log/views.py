# Python Standard Function Import
import json
import urllib.parse

# Django Core Import
from django.core.handlers.wsgi import WSGIRequest
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


class CreateLog:
    request: WSGIRequest
    info: dict
    page_obj: object

    list_dict = [
        'problemList', 'likeList', 'rateList', 'answerList', 'postList',
        'likeDashboard', 'rateDashboard', 'answerDashboard',
    ]
    detail_dict = ['problemDetail', 'likeDetail', 'rateDetail', 'answerDetail', 'postDetail']
    board_dict = ['postCreate', 'postUpdate', 'commentCreate', 'commentUpdate']
    delete_dict = ['postDelete', 'commentDelete']

    @property
    def user_id(self):
        return self.request.user.id

    @property
    def session_key(self):
        return self.request.COOKIES.get('sessionid')

    @property
    def log_url(self):
        return urllib.parse.unquote(self.request.get_full_path())

    @property
    def method(self):
        return self.request.method

    @property
    def log_type(self):
        return self.info.get('type')

    @property
    def title(self):
        return self.info.get('title')

    @property
    def log_content(self):
        return f'{self.log_type}({self.method}) - {self.title}'

    @property
    def sub(self):
        return self.info.get('sub', '')

    @property
    def page(self):
        return self.page_obj.number if self.page_obj else 1

    @property
    def answer(self):
        return self.info.get('answer', '')

    @property
    def problem_id(self):
        return self.info.get('problem_id', '')

    @property
    def post_id(self):
        return self.info.get('post_id', '')

    @property
    def comment_id(self):
        return self.info.get('comment_id', '')

    # if log_type in list_dict:
    #     log_content += f'({sub} p.{page})'
    # elif log_type in detail_dict:
    #     if method == 'GET':
    #         if log_type == 'postDetail':
    #             log_content += f'(Post ID:{post_id})'
    #         else:
    #             ProblemLog.objects.create(user_id=user_id, session_key=session_key, problem_id=problem_id)
    #     elif method == 'POST':
    #         obj = Evaluation.objects.get(user_id=user_id, problem_id=problem_id)
    #         if log_type == 'likeDetail':
    #             log_content += f'(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})'
    #             LikeLog.objects.create(user_id=user_id, problem_id=problem_id, is_liked=obj.is_liked)
    #         elif log_type == 'rateDetail':
    #             log_content += f'(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})'
    #             RateLog.objects.create(user_id=user_id, problem_id=problem_id, difficulty_rated=obj.difficulty_rated)
    #         elif log_type == 'answerDetail':
    #             if answer is None:
    #                 log_content += '(Answer Trial Failed)'
    #             else:
    #                 a, b, c = obj.answered_times, obj.submitted_answer, obj.is_correct
    #                 log_content += f'(Answered Times: {a}, Submitted Answer: {b}, Is Correct: {c})'
    #                 AnswerLog.objects.create(user_id=user_id, problem_id=problem_id, submitted_answer=b, is_correct=c)
    # elif log_type in board_dict:
    #     extra1 = [log_type[:i] for i in range(len(log_type)) if log_type[i].isupper()][0].capitalize()
    #     extra2 = log_type[len(extra1):].capitalize()
    #     log_content += f'({extra1} {extra2}'
    #     if method == 'GET':
    #         log_content += ' Attempt)'
    #     if method == 'POST':
    #         log_content += ' Successfully)'
    # elif log_type in delete_dict:
    #     log_content += f'(Post ID {post_id} Deleted Successfully)'
    #
    # RequestLog.objects.create(user_id=user_id, session_key=session_key, log_url=log_url, log_content=log_content)


def get_log_info(request, info, page_obj, extra=None):
    method = request.method
    log_type = info.get('type')
    title = info.get('title')
    log_content = f'{log_type}({method}) - {title}{extra}'
    log_info = {
        'user_id': request.user.id,
        'session_key': request.COOKIES.get('sessionid'),
        'log_url': urllib.parse.unquote(request.get_full_path()),
        'type': log_type,
        'method': method,
        'title': info.get('title'),
        'sub': info.get('sub', ''),
        'page': page_obj.number if page_obj else 1,
        'answer': info.get('answer', ''),
        'problem_id': info.get('problem_id', ''),
        'post_id': info.get('post_id', ''),
        'comment_id': info.get('comment_id', ''),
        'log_content': log_content,
    }
    return log_info


def create_new_request_log(log_info) -> None:
    user_id = log_info['user_id']
    session_key = log_info['session_key']
    log_url = log_info['log_url']
    log_content = log_info['log_content']
    RequestLog.objects.create(
        user_id=user_id,
        session_key=session_key,
        log_url=log_url,
        log_content=log_content,
    )


def get_log_category(log_type, obj):
    field_dict = {
        'likeDetail': {
            'field_1': 'liked_times',
            'field_2': 'is_liked',
        }
    }
    category_dict = {
        'likeDetail': {
            'model': LikeLog,
            'sub_1': 'Liked Times',
            'sub_2': 'Is Liked',
            'sub_3': '',
        },
        'rateDetail': {
            'model': RateLog,
            'field': 'difficulty_rated',
            'sub_1': 'Rated Times',
            'sub_2': 'Difficulty Rated',
            'sub_3': '',
        },
        'answerDetail': {
            'model': AnswerLog,
            'field': 'difficulty_rated',
            'sub_0': 'Answer Trial Failed',
            'sub_1': 'Answered Times',
            'sub_2': 'Submitted Answer',
            'sub_3': 'Is Correct',
        },
    }
    return category_dict[log_type]


def get_log_extra_content(log_type, log_category):
    model, field, sub_0, sub_1, sub_2, sub_3 = log_category[:]
    extra_content = []
    if log_type != 'answerDetail':
        extra_content.append(sub_1)
    #     log_content += f'(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})'
    #     LikeLog.objects.create(user_id=user_id, problem_id=problem_id, is_liked=obj.is_liked)
    # elif log_type == 'rateDetail':
    #     log_content += f'(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})'
    #     RateLog.objects.create(user_id=user_id, problem_id=problem_id, difficulty_rated=obj.difficulty_rated)
    # elif log_type == 'answerDetail':
    #     if answer is None:
    #         log_content += '(Answer Trial Failed)'
    #     else:
    #         a, b, c = obj.answered_times, obj.submitted_answer, obj.is_correct
    #         log_content += f'(Answered Times: {a}, Submitted Answer: {b}, Is Correct: {c})'
    #         AnswerLog.objects.create(user_id=user_id, problem_id=problem_id, submitted_answer=b, is_correct=c)


def create_detail_log(log_category, log_info):
    model, field, sub_0, sub_1, sub_2, sub_3 = log_category[:]
    user_id = log_info['user_id']
    problem_id = log_info['problem_id']
    create_dict = {
        'user_id': log_info['user_id'],
        'problem_id': log_info['problem_id'],
    }
    model.objects.create(user_id=user_id, problem_id=problem_id)
