from django.core.paginator import Paginator
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat, Cast
from django.shortcuts import render
from django.urls import reverse_lazy

from common import constants
from .. import filters
from .. import models
# from ..models import Problem, Exam, Evaluation

psat_icon_set = constants.icon.PSAT_ICON_SET
like_none_icon = psat_icon_set['likeNone']
star_none_icon = psat_icon_set['starNone']

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


def get_list(target):
    target_list = []
    for t in target:
        if t not in target_list:
            target_list.append(t)
    return target_list


def get_paginator_page_range(paginate_by: int, queryset, page_number: str):
    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_evaluation_info(user, obj: models.Problem) -> models.Problem:
    problem_id = obj.prob_id
    source = None
    if user.is_authenticated:
        source = models.Evaluation.objects.filter(
            user=user, problem_id=problem_id).first()

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


def problem(request):
    view_type = 'problem'
    template_name = 'psat/new_problem_list.html#content' if request.htmx else 'psat/new_problem_list.html'
    problem_filter = filters.PsatProblemFilter(
        request.GET, queryset=models.Problem.objects.all())
    base_url = reverse_lazy('psat:new_problem_list')

    year = request.GET.get('exam__year', '')
    ex = request.GET.get('exam__ex', '')
    sub = request.GET.get('exam__sub', '')
    pagination_url = f'{base_url}?exam__year={year}&exam__ex={ex}&exam__sub={sub}'

    exam_objects = models.Exam.objects.all()
    if year:
        exam_objects = exam_objects.filter(year=year)
    if ex:
        exam_objects = exam_objects.filter(ex=ex)
    if sub:
        exam_objects = exam_objects.filter(sub=sub)

    year_list_raw = exam_objects.annotate(
        year_suffix=Cast(Concat(F('year'), Value('년')), CharField())
    ).values_list('year', 'year_suffix')
    ex_list_raw = exam_objects.values_list('ex', 'exam2')
    sub_list_raw = exam_objects.values_list('sub', 'subject')

    year_list = get_list(year_list_raw)
    ex_list = get_list(ex_list_raw)
    sub_list = get_list(sub_list_raw)

    page_number = request.GET.get('page', 1)
    page_obj, page_range = get_paginator_page_range(10, problem_filter.qs, page_number)

    for obj in page_obj:
        get_evaluation_info(request.user, obj)

    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': 'PSAT 기출문제',
        'pagination_url': pagination_url,
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
        'year': year,
        'ex': ex,
        'sub': sub,
        'year_list': year_list,
        'ex_list': ex_list,
        'sub_list': sub_list,
    }
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'base_url': base_url,
        'pagination_url': pagination_url,
        'problem_list': True,
    }
    return render(request, template_name, context)


def like(request):
    view_type = 'like'
    template_name = 'psat/new_problem_list.html#content' if request.htmx else 'psat/new_problem_list.html'
    problem_filter = filters.PsatLikeFilter(
        request.GET, queryset=models.Problem.objects.filter(
            evaluation__user=request.user, evaluation__is_liked__gte=0))
    base_url = reverse_lazy('psat:new_like_list')

    sub = request.GET.get('exam__sub', '')
    sub_list = [('언어', '언어논리'), ('자료', '자료해석'), ('상황', '상황판단')]

    is_liked_str = request.GET.get('evaluation__is_liked', '')
    is_liked_dict = {'': None, 'True': True, 'False': False}
    is_liked = is_liked_dict[is_liked_str]

    liked_list = [(True, '즐겨찾기 추가 문제'), (False, '즐겨찾기 제외 문제')]
    pagination_url = f'{base_url}?&exam__sub={sub}&evaluation__is_liked={is_liked}'

    page_number = request.GET.get('page', 1)
    page_obj, page_range = get_paginator_page_range(10, problem_filter.qs, page_number)

    for obj in page_obj:
        get_evaluation_info(request.user, obj)

    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': 'PSAT 즐겨찾기',
        'pagination_url': pagination_url,
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
        'sub': sub,
        'sub_list': sub_list,
        'is_liked': is_liked,
        'liked_list': liked_list,
    }
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'base_url': base_url,
        'pagination_url': pagination_url,
        'like_list': True,
    }
    return render(request, template_name, context)


def rate(request):
    view_type = 'rate'
    template_name = 'psat/new_problem_list.html#content' if request.htmx else 'psat/new_problem_list.html'
    problem_filter = filters.PsatRateFilter(
        request.GET, queryset=models.Problem.objects.filter(
            evaluation__user=request.user, evaluation__difficulty_rated__gte=0))
    base_url = reverse_lazy('psat:new_rate_list')

    sub = request.GET.get('exam__sub', '')
    sub_list = [('언어', '언어논리'), ('자료', '자료해석'), ('상황', '상황판단')]

    difficulty_rated_str = request.GET.get('evaluation__difficulty_rated', '')
    difficulty_rated_dict = {'': None, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5}
    difficulty_rated = difficulty_rated_dict[difficulty_rated_str]

    rated_list = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    pagination_url = f'{base_url}?&exam__sub={sub}&evaluation__difficulty_rated={difficulty_rated}'

    page_number = request.GET.get('page', 1)
    page_obj, page_range = get_paginator_page_range(10, problem_filter.qs, page_number)

    for obj in page_obj:
        get_evaluation_info(request.user, obj)

    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': 'PSAT 즐겨찾기',
        'pagination_url': pagination_url,
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
        'sub': sub,
        'sub_list': sub_list,
        'difficulty_rated': difficulty_rated,
        'rated_list': rated_list,
    }
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'base_url': base_url,
        'pagination_url': pagination_url,
        'rate_list': True,
    }
    return render(request, template_name, context)


def answer(request):
    view_type = 'answer'
    template_name = 'psat/new_problem_list.html#content' if request.htmx else 'psat/new_problem_list.html'
    problem_filter = filters.PsatAnswerFilter(
        request.GET, queryset=models.Problem.objects.filter(
            evaluation__user=request.user, evaluation__is_correct__gte=0))
    base_url = reverse_lazy('psat:new_answer_list')

    sub = request.GET.get('exam__sub', '')
    sub_list = [('언어', '언어논리'), ('자료', '자료해석'), ('상황', '상황판단')]

    is_correct_str = request.GET.get('evaluation__is_correct', '')
    is_correct_dict = {'': None, 'True': True, 'False': False}
    is_correct = is_correct_dict[is_correct_str]

    answered_list = [(True, '맞힌 문제'), (False, '틀린 문제')]
    pagination_url = f'{base_url}?&exam__sub={sub}&evaluation__is_liked={is_correct}'

    page_number = request.GET.get('page', 1)
    page_obj, page_range = get_paginator_page_range(10, problem_filter.qs, page_number)

    for obj in page_obj:
        get_evaluation_info(request.user, obj)

    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': 'PSAT 정답확인',
        'pagination_url': pagination_url,
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
        'sub': sub,
        'sub_list': sub_list,
        'is_correct': is_correct,
        'answered_list': answered_list,
    }
    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'base_url': base_url,
        'pagination_url': pagination_url,
        'answer_list': True,
    }
    return render(request, template_name, context)
