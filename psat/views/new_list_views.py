from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.shortcuts import render
from django.urls import reverse_lazy

from common import constants
from .. import filters
from .. import models

psat_icon_set = constants.icon.PSAT_ICON_SET
like_none_icon = psat_icon_set['likeNone']
star_none_icon = psat_icon_set['starNone']

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET

list_base_template = 'psat/new_problem_list.html'


def get_template_name(request) -> str:
    list_main_template = f'{list_base_template}#list_main'
    list_content_template = f'{list_base_template}#content'
    if request.method == 'GET':
        if request.htmx:
            return list_content_template
        else:
            return list_base_template
    elif request.method == 'POST':
        return list_main_template


def get_year_ex_sub(request) -> (str | int, str, str):
    year = request.GET.get('exam__year', '')
    year = '' if year == '' else int(year)
    ex = request.GET.get('exam__ex', '')
    sub = request.GET.get('exam__sub', '')
    return year, ex, sub


def get_option(target):
    target_option = []
    for t in target:
        if t not in target_option:
            target_option.append(t)
    return target_option


def get_year_ex_sub_list(queryset) -> list:
    year_list = queryset.annotate(
        year_suffix=Cast(Concat(F('exam__year'), Value('년')), CharField())
    ).values_list('exam__year', 'year_suffix')
    ex_list = queryset.values_list('exam__ex', 'exam__exam2')
    sub_list = queryset.values_list('exam__sub', 'exam__subject')

    year_option = get_option(year_list)
    ex_option = get_option(ex_list)
    sub_option = get_option(sub_list)

    return year_option, ex_option, sub_option


def get_filtered_queryset(user, sub, field, value) -> models.Problem.objects:
    """ Get filtered queryset for like, rate, answer views. """
    problem_filter = Q(evaluation__user=user)
    if sub != '':
        problem_filter &= Q(exam__sub=sub)
    if value == '':
        problem_filter &= Q(**{field+'__isnull': False})
    else:
        problem_filter &= Q(**{field: value})
    return models.Problem.objects.filter(problem_filter)


def get_paginator_info(request, paginate_by: int, queryset):
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=3, on_ends=1)
    for obj in page_obj:
        get_evaluation_info(request.user, obj)
    return page_obj, page_range


def get_evaluation_info(user, obj: models.Problem) -> models.Problem:
    source = None
    if user.is_authenticated:
        source = models.Evaluation.objects.filter(
            user=user, problem=obj).first()

    obj.opened_at = source.opened_at if source else None
    obj.opened_times = source.opened_times if source else 0

    obj.liked_at = source.liked_at if source else None
    obj.is_liked = source.is_liked if source else None
    obj.like_icon = source.like_icon() if source else like_none_icon

    obj.rated_at = source.rated_at if source else None
    obj.difficulty_rated = source.difficulty_rated if source else None
    obj.rate_icon = source.rate_icon() if source else star_none_icon

    obj.answered_at = source.answered_at if source else None
    obj.submitted_answered = source.submitted_answer if source else None
    obj.is_correct = source.is_correct if source else None
    obj.answer_icon = source.answer_icon() if source else ''

    return obj


def get_info(view_type, **kwargs):
    title = {
        'problem': 'PSAT 기출문제',
        'like': 'PSAT 즐겨찾기',
        'rate': 'PSAT 난이도',
        'answer': 'PSAT 정답확인',
        'search': 'PSAT 검색 결과',
    }
    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': title[view_type],
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
    }
    if kwargs:
        for key, item in kwargs.items():
            info[key] = item
    return info


def problem(request):
    view_type = 'problem'
    base_url = reverse_lazy('psat:problem_list')
    template_name = get_template_name(request)

    queryset = models.Problem.objects.all()
    problem_filter = filters.PsatProblemFilter(request.GET, queryset=queryset)

    year, ex, sub = get_year_ex_sub(request)
    year_option, ex_option, sub_option = get_year_ex_sub_list(problem_filter.qs)

    pagination_url = f'{base_url}?exam__year={year}&exam__ex={ex}&exam__sub={sub}'
    page_obj, page_range = get_paginator_info(request, 10, problem_filter.qs)

    info = get_info(
        view_type, pagination_url=pagination_url, base_url=base_url, year=year, ex=ex, sub=sub,
        year_option=year_option, ex_option=ex_option, sub_option=sub_option)
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'problem_list': True,
    }
    return render(request, template_name, context)


def like(request):
    view_type = 'like'
    base_url = reverse_lazy('psat:like_list')
    template_name = get_template_name(request)

    sub = request.GET.get('exam__sub', '')
    field = 'evaluation__is_liked'
    is_liked_str = request.GET.get('evaluation__is_liked', '')
    is_liked_dict = {'True': True, 'False': False}
    is_liked = '' if is_liked_str == '' else is_liked_dict[is_liked_str]

    queryset = get_filtered_queryset(request.user, sub, field, is_liked)

    _, _, sub_option = get_year_ex_sub_list(queryset)
    like_option = [(True, '즐겨찾기 추가 문제'), (False, '즐겨찾기 제외 문제')]

    pagination_url = f'{base_url}?evaluation__user={request.user.id}&exam__sub={sub}&evaluation__is_liked={is_liked}'
    page_obj, page_range = get_paginator_info(request, 10, queryset)

    info = get_info(
        view_type, pagination_url=pagination_url, base_url=base_url,
        sub=sub, sub_option=sub_option, is_liked=is_liked, like_option=like_option)
    context = {
        'info': info,
        'page_obj': page_obj,
        'page_range': page_range,
        'like_list': True,
    }
    return render(request, template_name, context)


def rate(request):
    view_type = 'rate'
    base_url = reverse_lazy('psat:rate_list')
    template_name = get_template_name(request)

    sub = request.GET.get('exam__sub', '')
    field = 'evaluation__difficulty_rated'
    difficulty_rated_str = request.GET.get('evaluation__difficulty_rated', '')
    difficulty_rated = '' if difficulty_rated_str == '' else int(difficulty_rated_str)

    queryset = get_filtered_queryset(request.user, sub, field, difficulty_rated)

    _, _, sub_option = get_year_ex_sub_list(queryset)
    rate_option = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]

    pagination_url = f'{base_url}?evaluation__user={request.user.id}&exam__sub={sub}&evaluation__difficulty_rated={difficulty_rated}'
    page_obj, page_range = get_paginator_info(request, 10, queryset)

    info = get_info(
        view_type, pagination_url=pagination_url, base_url=base_url,
        sub=sub, sub_option=sub_option, difficulty_rated=difficulty_rated, rate_option=rate_option)
    context = {
        'info': info,
        'page_obj': page_obj,
        'page_range': page_range,
        'rate_list': True,
    }
    return render(request, template_name, context)


def answer(request):
    view_type = 'answer'
    base_url = reverse_lazy('psat:answer_list')
    template_name = get_template_name(request)

    sub = request.GET.get('exam__sub', '')
    field = 'evaluation__is_correct'
    is_correct_str = request.GET.get('evaluation__is_correct', '')
    is_correct_dict = {'': None, 'True': True, 'False': False}
    is_correct = '' if is_correct_str == '' else is_correct_dict[is_correct_str]

    queryset = get_filtered_queryset(request.user, sub, field, is_correct)

    _, _, sub_option = get_year_ex_sub_list(queryset)
    answer_option = [(True, '맞힌 문제'), (False, '틀린 문제')]

    pagination_url = f'{base_url}?evaluation__User{request.user.id}&exam__sub={sub}&evaluation__is_liked={is_correct}'
    page_obj, page_range = get_paginator_info(request, 10, queryset)

    info = get_info(
        view_type, pagination_url=pagination_url, base_url=base_url,
        sub=sub, sub_option=sub_option, is_correct=is_correct, answer_option=answer_option)
    context = {
        'info': info,
        'page_obj': page_obj,
        'page_range': page_range,
        'answer_list': True,
    }
    return render(request, template_name, context)


def search(request):
    view_type = 'search'
    base_url = reverse_lazy('psat:search')

    if request.method == 'GET':  # For pagination
        template_name = f'{list_base_template}#content'
        q = request.GET.get('data')
        queryset = models.Problem.objects.filter(problemdata__data__contains=q)
        problem_filter = filters.PsatProblemFilter(request.GET, queryset=queryset)
    else:  # For search in search bar
        template_name = f'{list_base_template}#list_main'
        q = request.POST.get('data')
        queryset = models.Problem.objects.filter(problemdata__data__contains=q)
        problem_filter = filters.PsatProblemFilter(request.POST, queryset=queryset)

    year, ex, sub = get_year_ex_sub(request)
    year_list, ex_list, sub_list = get_year_ex_sub_list(problem_filter.qs)
    pagination_url = f'{base_url}?data={q}&exam__year={year}&exam__ex={ex}&exam__sub={sub}'

    page_obj, page_range = get_paginator_info(request, 10, problem_filter.qs)
    info = get_info(
        view_type, pagination_url=pagination_url, base_url=base_url, year=year, ex=ex, sub=sub,
        year_list=year_list, ex_list=ex_list, sub_list=sub_list)
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'search_list': True,
    }
    return render(request, template_name, context)
