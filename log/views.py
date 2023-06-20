# Django Core Import
import json
import urllib.parse

from django.http import HttpResponse
from django.shortcuts import render

# Custom App Import
from log.models import RequestLog, ProblemLog


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

    RequestLog.objects.create(user_id=user_id, session_key=session_key, log_url=log_url, log_content=log_content)

    response_data = {
        'message': 'logged',
    }
    json_data = json.dumps(response_data)
    return HttpResponse(json_data, content_type='application/json')


def create_problem_log(request, problem_id):
    user_id = request.user.id
    session_key = request.COOKIES.get('sessionid')
    ProblemLog.objects.create(user_id=user_id, session_key=session_key, problem_id=problem_id)
