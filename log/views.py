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


class CreateLogMixIn:
    request: WSGIRequest
    info: dict
    category: str
    page_obj: object

    @property
    def user_id(self): return self.request.user.id
    @property
    def session_key(self): return self.request.COOKIES.get('sessionid')
    @property
    def log_url(self): return urllib.parse.unquote(self.request.get_full_path())
    @property
    def method(self): return self.request.method
    @property
    def log_type(self): return self.info.get('type')
    @property
    def title(self): return self.info.get('title')
    @property
    def log_content(self): return f'{self.log_type}({self.method}) - {self.title}'
    @property
    def sub(self): return self.info.get('sub', '')
    @property
    def page(self): return self.page_obj.number if self.page_obj else 1
    @property
    def answer(self): return self.info.get('answer', '')
    @property
    def problem_id(self): return self.info.get('problem_id', '')
    @property
    def post_id(self): return self.info.get('post_id', '')
    @property
    def comment_id(self): return self.info.get('comment_id', '')

    @property
    def evaluation_object(self):
        if self.user_id and self.problem_id:
            obj = Evaluation.objects.get(user_id=self.user_id, problem_id=self.problem_id)
        else:
            obj = None
        return obj

    def create_log_for_list(self, page_obj: object):
        page = page_obj.number if page_obj else 1
        log_content = self.log_content
        log_content += f'({self.sub} p.{page})'
        self.create_request_log(log_content)

    def create_log_for_detail(self):
        log_content = self.log_content
        log_content += f' {self.post_id}'
        self.create_request_log(self.log_content)

    def create_log_for_psat_detail(self):
        self.create_problem_log()
        self.create_request_log(self.log_content)

    def create_log_for_psat_post_answer(self, answer):
        log_content = self.log_content
        obj = self.evaluation_object
        if answer:
            self.create_answer_log()
            a, b, c = obj.answered_times, obj.submitted_answer, obj.is_correct
            log_content += f'(Answered Times: {a}, Submitted Answer: {b}, Is Correct: {c})'
        else:
            log_content += '(Answer Trial Failed)'
        self.create_request_log(log_content)

    def create_log_for_psat_post_other(self):
        log_content = self.log_content
        obj = self.evaluation_object
        if self.log_type == 'likeDetail':
            self.create_like_log()
            log_content += f'(Liked Times: {obj.liked_times}, Is Liked: {obj.is_liked})'
        elif self.log_type == 'rateDetail':
            self.create_rate_log()
            log_content += f'(Rated Times: {obj.rated_times}, Difficulty Rated: {obj.difficulty_rated})'
        self.create_request_log(log_content)

    def create_log_for_board_create_update(self):
        log_content = self.log_content
        extra1 = [self.log_type[:i] for i in range(len(self.log_type)) if self.log_type[i].isupper()][0].capitalize()
        extra2 = self.log_type[len(extra1):].capitalize()
        log_content += f'({extra1} {extra2}'
        if self.method == 'GET':
            log_content += ' Attempt)'
        if self.method == 'POST':
            log_content += ' Successfully)'
        self.create_request_log(log_content)

    def create_log_for_board_delete(self):
        log_content = self.log_content
        log_content += f'(Post ID {self.post_id} Deleted Successfully)'
        self.create_request_log(log_content)

    def create_request_log(self, log_content=None):
        if log_content is None:
            log_content = self.log_content
        RequestLog.objects.create(
            user_id=self.user_id,
            session_key=self.session_key,
            log_url=self.log_url,
            log_content=log_content)

    def create_problem_log(self):
        ProblemLog.objects.create(
            evaluation=self.evaluation_object,
            user_id=self.user_id,
            session_key=self.session_key,
            problem_id=self.problem_id)

    def create_like_log(self):
        LikeLog.objects.create(
            evaluation=self.evaluation_object,
            user_id=self.user_id,
            problem_id=self.problem_id,
            is_liked=self.evaluation_object.is_liked)

    def create_rate_log(self):
        RateLog.objects.create(
            evaluation=self.evaluation_object,
            user_id=self.user_id,
            problem_id=self.problem_id,
            difficulty_rated=self.evaluation_object.difficulty_rated)

    def create_answer_log(self):
        AnswerLog.objects.create(
            evaluation=self.evaluation_object,
            user_id=self.user_id,
            problem_id=self.problem_id,
            submitted_answer=self.evaluation_object.submitted_answer,
            is_correct=self.evaluation_object.is_correct)
