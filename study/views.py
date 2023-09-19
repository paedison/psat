from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.shortcuts import render
from django.urls import reverse_lazy

from common import constants
from psat.views.list_views import ListViewSetting
from . import models

psat_icon_set = constants.icon.PSAT_ICON_SET
menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


class StudyViewSetting(ListViewSetting):
    """ Represent all properties and methods for list views. """
    menu = 'study'
    url_name = 'study:list'
    list_base_template = 'study/problem_list.html'

    @property
    def base_url(self) -> str: return reverse_lazy(self.url_name, args=[self.view_type])

    @property
    def pagination_url(self) -> str:
        return (f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
                f'&user={self.request.user.id}&is_liked={self.is_liked}'
                f'&star_count={self.star_count}&is_correct={self.is_correct}'
                f'&data={self.search_data}')

    @property
    def chapter(self) -> str: return self.request.GET.get('chapter', '')
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
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        If view_type == 'search', 'GET' for pagination, 'POST' for search in search bar
        :return: str
        """
        base = self.list_base_template
        main = f'{base}#list_main'
        content = f'{base}#content'
        method = self.request.method
        if self.view_type == 'search':
            return content if method == 'GET' else main
        else:
            if method == 'GET':
                return content if self.request.htmx else base
            else:
                return main

    @property
    def problem_filter(self) -> Q:
        """ Get problem filter corresponding to the year, ex, sub. """
        ids_list = list(models.AlphaQuestion.objects.values_list('problem_id', flat=True))
        problem_filter = Q(id__in=ids_list)
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
        return models.Problem.objects.filter(problem_filter).order_by(
            'study_alphaquestions__id')

    # @property
    # def queryset(self) -> models.Problem.objects:
    #     opt_dict = {
    #         'problem': ('', ''),
    #         'like': ('evaluation__is_liked', self.is_liked),
    #         'rate': ('evaluation__difficulty_rated', self.star_count),
    #         'answer': ('evaluation__is_correct', self.is_correct),
    #         'search': ('', '')
    #     }
    #     return self.get_filtered_queryset(*opt_dict[self.view_type])
    #
    # @property
    # def year_list(self) -> queryset:
    #     return self.queryset.annotate(
    #         year_suffix=Cast(
    #             Concat(F('exam__year'), Value('년')), CharField()
    #         )).values_list('exam__year', 'year_suffix')
    #
    # @property
    # def ex_list(self) -> queryset:
    #     return self.queryset.values_list('exam__ex', 'exam__exam2')
    #
    # @property
    # def sub_list(self) -> queryset:
    #     return self.queryset.values_list('exam__sub', 'exam__subject')
    #
    # @staticmethod
    # def get_option(target) -> list[tuple]:
    #     target_option = []
    #     for t in target:
    #         if t not in target_option:
    #             target_option.append(t)
    #     return target_option

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

    @property
    def page_obj(self) -> object: return self.get_paginator_info()[0]
    @property
    def page_range(self) -> object: return self.get_paginator_info()[1]

    @property
    def context(self) -> dict:
        context = super().context
        context['title'] = 'Study'
        context['icon'] = menu_icon_set['dashboard']
        context['problem_study'] = self.view_type == 'problem'
        context['like_study'] = self.view_type == 'like'
        context['rate_study'] = self.view_type == 'rate'
        context['answer_study'] = self.view_type == 'answer'

        return context

    def rendering(self) -> render:
        return render(self.request, self.template_name, self.context)


def base_view(request, view_type='problem'):
    study_view_setting = StudyViewSetting(request, view_type)
    return study_view_setting.rendering()
