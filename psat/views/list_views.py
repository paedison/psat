from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.shortcuts import render
from django.urls import reverse_lazy

from common import constants
from .. import models

psat_icon_set = constants.icon.PSAT_ICON_SET
menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


class ListViewSetting:
    menu = 'psat'
    list_base_template = 'psat/new_problem_list.html'

    def __init__(self, request, view_type):
        self.request = request
        self.view_type = view_type

    @property
    def base_url(self) -> str: return reverse_lazy('psat:list', args=[self.view_type])

    @property
    def pagination_url(self) -> str:
        return (f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
                f'&user={self.request.user.id}&is_liked={self.is_liked}'
                f'&star_count={self.star_count}&is_correct={self.is_correct}'
                f'&data={self.search_data}')

    @property
    def year_str(self) -> str: return self.request.GET.get('year', '')
    @property
    def year(self) -> str | int: return '' if self.year_str == '' else int(self.year_str)
    @property
    def ex(self) -> str: return self.request.GET.get('ex', '')
    @property
    def sub(self) -> str: return self.request.GET.get('sub', '')

    @property
    def is_liked(self) -> str | bool:
        is_liked = self.request.GET.get('is_liked', '')
        is_liked_dict = {'True': True, 'False': False}
        return '' if is_liked == '' else is_liked_dict[is_liked]

    @property
    def star_count(self) -> str | int:
        star_count = self.request.GET.get('star_count', '')
        return '' if star_count == '' else int(star_count)

    @property
    def is_correct(self) -> str | bool:
        is_correct = self.request.GET.get('is_correct', '')
        is_correct_dict = {'': None, 'True': True, 'False': False}
        return '' if is_correct == '' else is_correct_dict[is_correct]

    @property
    def search_data(self) -> str:
        if self.request.method == 'GET':
            return self.request.GET.get('data', '')
        else:
            return self.request.POST.get('data', '')

    @property
    def template_name(self) -> str:
        list_base = self.list_base_template  # base(GET) > main(POST) > content(GET)
        list_main = f'{list_base}#list_main'
        list_content = f'{list_base}#content'
        method = self.request.method
        if self.view_type == 'search':
            # 'GET' for pagination, 'POST' for search in search bar
            return list_content if method == 'GET' else list_main
        else:
            if method == 'GET':
                return list_content if self.request.htmx else list_base
            else:
                return list_main

    @property
    def problem_filter(self) -> Q:
        problem_filter = Q()
        if self.year != '':
            problem_filter &= Q(exam__year=self.year)
        if self.ex != '':
            problem_filter &= Q(exam__ex=self.ex)
        if self.sub != '':
            problem_filter &= Q(exam__sub=self.sub)
        return problem_filter

    def get_filtered_queryset(self, field='', value='') -> models.Problem.objects:
        """ Get filtered queryset for like, rate, answer views. """
        problem_filter = self.problem_filter
        if self.view_type == 'search':
            problem_filter &= Q(problemdata__data__contains=self.search_data)
        else:
            if self.view_type != 'problem':
                problem_filter &= Q(evaluation__user=self.request.user)
                if value == '':
                    problem_filter &= Q(**{field + '__isnull': False})
                else:
                    problem_filter &= Q(**{field: value})
        return models.Problem.objects.filter(problem_filter)

    @property
    def queryset(self) -> models.Problem.objects:
        opt_dict = {
            'problem': ('', ''),
            'like': ('evaluation__is_liked', self.is_liked),
            'rate': ('evaluation__difficulty_rated', self.star_count),
            'answer': ('evaluation__is_correct', self.is_correct),
            'search': ('', '')
        }
        return self.get_filtered_queryset(*opt_dict[self.view_type])

    @property
    def year_list(self) -> queryset:
        return self.queryset.annotate(
            year_suffix=Cast(
                Concat(F('exam__year'), Value('년')), CharField()
            )).values_list('exam__year', 'year_suffix')

    @property
    def ex_list(self) -> queryset:
        return self.queryset.values_list('exam__ex', 'exam__exam2')

    @property
    def sub_list(self) -> queryset:
        return self.queryset.values_list('exam__sub', 'exam__subject')

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    @property
    def year_option(self) -> list[tuple]: return self.get_option(self.year_list)
    @property
    def ex_option(self) -> list[tuple]: return self.get_option(self.ex_list)
    @property
    def sub_option(self) -> list[tuple]: return self.get_option(self.sub_list)

    @property
    def like_option(self) -> list[tuple]:
        return [(True, f'{psat_icon_set["likeTrue"]}즐겨찾기 추가 문제'),
                (False, f'{psat_icon_set["likeFalse"]}즐겨찾기 제외 문제')]

    @property
    def answer_option(self) -> list[tuple]:
        return [(True, f'{psat_icon_set["answerTrue"]}맞힌 문제'),
                (False, f'{psat_icon_set["answerFalse"]}틀린 문제')]

    @property
    def rate_option(self) -> list[tuple]:
        return [(5, psat_icon_set['star5']),
                (4, psat_icon_set['star4']),
                (3, psat_icon_set['star3']),
                (2, psat_icon_set['star2']),
                (1, psat_icon_set['star1'])]

    def get_paginator_info(self) -> tuple[object, object]:
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(self.queryset, 10)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=3, on_ends=1)
        for obj in page_obj:
            get_evaluation_info(self.request.user, obj)
        return page_obj, page_range

    @property
    def page_obj(self) -> object: return self.get_paginator_info()[0]
    @property
    def page_range(self) -> object: return self.get_paginator_info()[1]

    @property
    def info(self) -> dict:
        title = {
            'problem': 'PSAT 기출문제',
            'like': 'PSAT 즐겨찾기',
            'rate': 'PSAT 난이도',
            'answer': 'PSAT 정답확인',
            'search': 'PSAT 검색 결과',
        }
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': title[self.view_type],
            'icon': menu_icon_set[self.view_type],
            'color': color_set[self.view_type],
            'base_url': self.base_url,
            'pagination_url': self.pagination_url,
            'year': self.year,
            'ex': self.ex,
            'sub': self.sub,
            'year_option': self.year_option,
            'ex_option': self.ex_option,
            'sub_option': self.sub_option,
            'is_liked': self.is_liked,
            'like_option': self.like_option,
            'star_count': self.star_count,
            'rate_option': self.rate_option,
            'is_correct': self.is_correct,
            'answer_option': self.answer_option,
            'data': self.search_data,
        }

    @property
    def context(self) -> dict:
        return {
            'info': self.info,
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'problem_list': self.view_type == 'problem',
            'like_list': self.view_type == 'like',
            'rate_list': self.view_type == 'rate',
            'answer_list': self.view_type == 'answer',
            'search_list': self.view_type == 'search',
        }

    def rendering(self) -> render:
        return render(self.request, self.template_name, self.context)


def get_evaluation_info(user, obj: models.Problem) -> models.Problem:
    source = None
    if user.is_authenticated:
        source = models.Evaluation.objects.filter(user=user, problem=obj).first()

    obj.opened_at = source.opened_at if source else None
    obj.opened_times = source.opened_times if source else 0

    obj.liked_at = source.liked_at if source else None
    obj.is_liked = source.is_liked if source else None
    obj.like_icon = source.like_icon() if source else psat_icon_set['likeNone']

    obj.rated_at = source.rated_at if source else None
    obj.difficulty_rated = source.difficulty_rated if source else None
    obj.rate_icon = source.rate_icon() if source else psat_icon_set['starNone']

    obj.answered_at = source.answered_at if source else None
    obj.submitted_answered = source.submitted_answer if source else None
    obj.is_correct = source.is_correct if source else None
    obj.answer_icon = source.answer_icon() if source else ''

    return obj


def base_view(request, view_type='problem'):
    list_view_setting = ListViewSetting(request, view_type)
    return list_view_setting.rendering()


# def problem(request):
#     problem_view = ListViewSetting(request, view_type='problem')
#     return problem_view.rendering()
#
#
# def like(request):
#     problem_view = ListViewSetting(request, view_type='like')
#     return problem_view.rendering()
#
#
# def rate(request):
#     problem_view = ListViewSetting(request, view_type='rate')
#     return problem_view.rendering()
#
#
# def answer(request):
#     problem_view = ListViewSetting(request, view_type='answer')
#     return problem_view.rendering()
#
#
# def search(request):
#     problem_view = ListViewSetting(request, view_type='search')
#     return problem_view.rendering()
#
#
# def get_template_name(request) -> str:
#     list_main_template = f'{list_base_template}#list_main'
#     list_content_template = f'{list_base_template}#content'
#     if request.method == 'GET':
#         if request.htmx:
#             return list_content_template
#         else:
#             return list_base_template
#     elif request.method == 'POST':
#         return list_main_template
#
#
# def get_year_ex_sub(request) -> (str | int, str, str):
#     year = request.GET.get('exam__year', '')
#     year = '' if year == '' else int(year)
#     ex = request.GET.get('exam__ex', '')
#     sub = request.GET.get('exam__sub', '')
#     return year, ex, sub
#
#
# def get_problem_filter(request):
#     year, ex, sub = get_year_ex_sub(request)
#     problem_filter = Q()
#     if year != '':
#         problem_filter &= Q(exam__year=year)
#     if ex != '':
#         problem_filter &= Q(exam__ex=ex)
#     if sub != '':
#         problem_filter &= Q(exam__sub=sub)
#     return problem_filter
#
#
#
# def get_option(target):
#     target_option = []
#     for t in target:
#         if t not in target_option:
#             target_option.append(t)
#     return target_option
#
#
# def get_year_ex_sub_option(queryset) -> (list, list, list):
#     year_list = queryset.annotate(
#         year_suffix=Cast(Concat(F('exam__year'), Value('년')), CharField())
#     ).values_list('exam__year', 'year_suffix')
#     ex_list = queryset.values_list('exam__ex', 'exam__exam2')
#     sub_list = queryset.values_list('exam__sub', 'exam__subject')
#
#     year_option = get_option(year_list)
#     ex_option = get_option(ex_list)
#     sub_option = get_option(sub_list)
#
#     return year_option, ex_option, sub_option
#
#
# def get_filtered_queryset(user, sub, field, value) -> models.Problem.objects:
#     """ Get filtered queryset for like, rate, answer views. """
#     problem_filter = Q(evaluation__user=user)
#     if sub != '':
#         problem_filter &= Q(exam__sub=sub)
#     if value == '':
#         problem_filter &= Q(**{field+'__isnull': False})
#     else:
#         problem_filter &= Q(**{field: value})
#     return models.Problem.objects.filter(problem_filter)
#
#
# def get_paginator_info(request, paginate_by: int, queryset):
#     page_number = request.GET.get('page', 1)
#     paginator = Paginator(queryset, paginate_by)
#     page_obj = paginator.get_page(page_number)
#     page_range = paginator.get_elided_page_range(
#         number=page_number, on_each_side=3, on_ends=1)
#     for obj in page_obj:
#         get_evaluation_info(request.user, obj)
#     return page_obj, page_range
#
#
# def get_info(view_type, **kwargs):
#     title = {
#         'problem': 'PSAT 기출문제',
#         'like': 'PSAT 즐겨찾기',
#         'rate': 'PSAT 난이도',
#         'answer': 'PSAT 정답확인',
#         'search': 'PSAT 검색 결과',
#     }
#     info = {
#         'menu': view_type,
#         'view_type': view_type,
#         'type': f'{view_type}List',
#         'title': title[view_type],
#         'icon': menu_icon_set[view_type],
#         'color': color_set[view_type],
#     }
#     if kwargs:
#         for key, item in kwargs.items():
#             info[key] = item
#     return info
#
#
# def problem(request):
#     view_type = 'problem'
#     base_url = reverse_lazy('psat:problem_list')
#     template_name = get_template_name(request)
#
#     year, ex, sub = get_year_ex_sub(request)
#     problem_filter = Q()
#     if year != '':
#         problem_filter &= Q(exam__year=year)
#     if ex != '':
#         problem_filter &= Q(exam__ex=ex)
#     if sub != '':
#         problem_filter &= Q(exam__sub=sub)
#
#     queryset = models.Problem.objects.filter(problem_filter)
#     year_option, ex_option, sub_option = get_year_ex_sub_option(queryset)
#
#     pagination_url = f'{base_url}?exam__year={year}&exam__ex={ex}&exam__sub={sub}'
#     page_obj, page_range = get_paginator_info(request, 10, queryset)
#
#     info = get_info(
#         view_type, pagination_url=pagination_url, base_url=base_url,
#         year=year, ex=ex, sub=sub,
#         year_option=year_option, ex_option=ex_option, sub_option=sub_option)
#     context = {
#         'info': info,
#         'page_obj': page_obj,
#         'page_range': page_range,
#         'problem_list': True,
#     }
#     return render(request, template_name, context)
#
#
# def like(request):
#     view_type = 'like'
#     base_url = reverse_lazy('psat:like_list')
#     template_name = get_template_name(request)
#
#     sub = request.GET.get('exam__sub', '')
#     field = 'evaluation__is_liked'
#     is_liked_str = request.GET.get('evaluation__is_liked', '')
#     is_liked_dict = {'True': True, 'False': False}
#     is_liked = '' if is_liked_str == '' else is_liked_dict[is_liked_str]
#
#     queryset = get_filtered_queryset(request.user, sub, field, is_liked)
#     _, _, sub_option = get_year_ex_sub_option(queryset)
#     like_option = [(True, '즐겨찾기 추가 문제'), (False, '즐겨찾기 제외 문제')]
#
#     pagination_url = f'{base_url}?evaluation__user={request.user.id}&exam__sub={sub}&evaluation__is_liked={is_liked}'
#     page_obj, page_range = get_paginator_info(request, 10, queryset)
#
#     info = get_info(
#         view_type, pagination_url=pagination_url, base_url=base_url,
#         sub=sub, sub_option=sub_option, is_liked=is_liked, like_option=like_option)
#     context = {
#         'info': info,
#         'page_obj': page_obj,
#         'page_range': page_range,
#         'like_list': True,
#     }
#     return render(request, template_name, context)
#
#
# def rate(request):
#     view_type = 'rate'
#     base_url = reverse_lazy('psat:rate_list')
#     template_name = get_template_name(request)
#
#     sub = request.GET.get('exam__sub', '')
#     field = 'evaluation__difficulty_rated'
#     difficulty_rated_str = request.GET.get('evaluation__difficulty_rated', '')
#     star_count = '' if difficulty_rated_str == '' else int(difficulty_rated_str)
#
#     queryset = get_filtered_queryset(request.user, sub, field, star_count)
#     _, _, sub_option = get_year_ex_sub_option(queryset)
#     rate_option = [
#         (1, '★☆☆☆☆'),
#         (2, '★★☆☆☆'),
#         (3, '★★★☆☆'),
#         (4, '★★★★☆'),
#         (5, '★★★★★'),
#     ]
#
#     pagination_url = f'{base_url}?evaluation__user={request.user.id}
#     &exam__sub={sub}&evaluation__difficulty_rated={star_count}'
#     page_obj, page_range = get_paginator_info(request, 10, queryset)
#
#     info = get_info(
#         view_type, pagination_url=pagination_url, base_url=base_url,
#         sub=sub, sub_option=sub_option, star_count=star_count, rate_option=rate_option)
#     context = {
#         'info': info,
#         'page_obj': page_obj,
#         'page_range': page_range,
#         'rate_list': True,
#     }
#     return render(request, template_name, context)
#
#
# def answer(request):
#     view_type = 'answer'
#     base_url = reverse_lazy('psat:answer_list')
#     template_name = get_template_name(request)
#
#     sub = request.GET.get('exam__sub', '')
#     field = 'evaluation__is_correct'
#     is_correct_str = request.GET.get('evaluation__is_correct', '')
#     is_correct_dict = {'': None, 'True': True, 'False': False}
#     is_correct = '' if is_correct_str == '' else is_correct_dict[is_correct_str]
#
#     queryset = get_filtered_queryset(request.user, sub, field, is_correct)
#     _, _, sub_option = get_year_ex_sub_option(queryset)
#     answer_option = [(True, '맞힌 문제'), (False, '틀린 문제')]
#
#     pagination_url = f'{base_url}?evaluation__User{request.user.id}
#     &exam__sub={sub}&evaluation__is_correct={is_correct}'
#     page_obj, page_range = get_paginator_info(request, 10, queryset)
#
#     info = get_info(
#         view_type, pagination_url=pagination_url, base_url=base_url,
#         sub=sub, sub_option=sub_option, is_correct=is_correct, answer_option=answer_option)
#     context = {
#         'info': info,
#         'page_obj': page_obj,
#         'page_range': page_range,
#         'answer_list': True,
#     }
#     return render(request, template_name, context)
#
#
# def search(request):
#     view_type = 'search'
#     base_url = reverse_lazy('psat:search')
#
#     if request.method == 'GET':  # For pagination
#         template_name = f'{list_base_template}#content'
#         q = request.GET.get('data')
#         queryset = models.Problem.objects.filter(problemdata__data__contains=q)
#         problem_filter = filters.PsatProblemFilter(request.GET, queryset=queryset)
#     else:  # For search in search bar
#         template_name = f'{list_base_template}#list_main'
#         q = request.POST.get('data')
#         queryset = models.Problem.objects.filter(problemdata__data__contains=q)
#         problem_filter = filters.PsatProblemFilter(request.POST, queryset=queryset)
#
#     year, ex, sub = get_year_ex_sub(request)
#     year_list, ex_list, sub_list = get_year_ex_sub_option(problem_filter.qs)
#     pagination_url = f'{base_url}?data={q}&exam__year={year}&exam__ex={ex}&exam__sub={sub}'
#
#     page_obj, page_range = get_paginator_info(request, 10, problem_filter.qs)
#     info = get_info(
#         view_type, pagination_url=pagination_url, base_url=base_url, year=year, ex=ex, sub=sub,
#         year_list=year_list, ex_list=ex_list, sub_list=sub_list)
#     context = {
#         'info': info,
#         'form': problem_filter.form,
#         'page_obj': page_obj,
#         'page_range': page_range,
#         'search_list': True,
#     }
#     return render(request, template_name, context)
