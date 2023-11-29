from django.core.paginator import Paginator
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from .base_view_mixins import BaseViewMixin


class PsatListViewMixIn(BaseViewMixin):
    menu = 'psat'

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.title = self.get_title()

        select_options: dict = self.get_select_options()
        self.year_option: list[tuple] = select_options['year_option']
        self.ex_option: list[tuple] = select_options['ex_option']
        self.sub_option: list[tuple] = select_options['sub_option']
        self.like_option: list[tuple] = select_options['like_option']
        self.rate_option: list[tuple] = select_options['rate_option']
        self.solve_option: list[tuple] = select_options['solve_option']
        self.memo_option: list[tuple] = select_options['memo_option']
        self.tag_option: list[tuple] = select_options['tag_option']

    def get_title(self) -> str:
        title_dict = {
            'problem': '기출문제',
            'like': '즐겨찾기',
            'rate': '난이도',
            'solve': '정답확인',
            'memo': '메모',
            'tag': '태그',
            'search': '검색 결과',
        }
        return title_dict[self.view_type]

    def get_queryset(self):
        return self.get_list_queryset(self.view_type)

    def get_select_options(self) -> dict:
        def get_option(target) -> list[tuple]:
            target_option = []
            for t in target:
                if t not in target_option:
                    target_option.append(t)
            return target_option

        queryset = self.get_queryset()

        year_list = (
            queryset.annotate(
                year=F('psat__year'),
                year_suffix=Cast(Concat(F('psat__year'), Value('년')), CharField()))
            .distinct().values_list('year', 'year_suffix').order_by('-psat__year'))
        ex_list = (
            queryset.annotate(ex=F('psat__exam__abbr'), exam=F('psat__exam__label'))
            .distinct().values_list('ex', 'exam').order_by('psat__exam_id'))
        sub_list = (
            queryset.annotate(sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .distinct().values_list('sub', 'subject').order_by('psat__subject_id'))
        new_sub_list = [(s[0], f'{self.ICON_SUBJECT[s[0]]}{s[1]}') for s in sub_list]

        url_like = reverse_lazy('psat:list', args=['like'])
        url_rate = reverse_lazy('psat:list', args=['rate'])
        url_solve = reverse_lazy('psat:list', args=['solve'])
        url_memo = reverse_lazy('psat:list', args=['memo'])
        url_tag = reverse_lazy('psat:list', args=['tag'])

        url_like_opt = f'{url_like}?is_liked='
        url_rate_opt = f'{url_rate}?rating='
        url_solve_opt = f'{url_solve}?is_correct='
        url_memo_opt = f'{url_memo}?has_memo='
        url_tag_opt = f'{url_tag}?has_tag='

        year_option = {
            'var': 'year',
            'text': '연도',
            'total': '전체 연도',
            'current': self.year,
            'options': get_option(year_list),
        }
        ex_option = {
            'var': 'ex',
            'text': '시험',
            'total': '전체 시험',
            'current': self.ex,
            'options': get_option(ex_list),
        }
        sub_option = {
            'var': 'sub',
            'text': '과목',
            'total': '전체 과목',
            'current': self.sub,
            'options': get_option(new_sub_list),
        }
        like_option = {
            'var': 'like',
            'text': self.ICON_LIKE['filter'],
            'current': self.is_liked,
            'options': [
                    ('', self.sub_title_dict['like'][''], f'{url_like}'),
                    (True, self.sub_title_dict['like']['True'], f'{url_like_opt}True'),
                    (False, self.sub_title_dict['like']['False'], f'{url_like_opt}False'),
                    (None, self.sub_title_dict['like']['None'], f'{url_like_opt}None'),
                ],
        }
        rate_option = {
            'var': 'rate',
            'text': self.ICON_RATE['filter'],
            'current': self.rating,
            'options': [
                ('', '난이도 지정', f'{url_rate}'),
                (5, self.ICON_RATE['star5'], f'{url_rate_opt}5'),
                (4, self.ICON_RATE['star4'], f'{url_rate_opt}4'),
                (3, self.ICON_RATE['star3'], f'{url_rate_opt}3'),
                (2, self.ICON_RATE['star2'], f'{url_rate_opt}2'),
                (1, self.ICON_RATE['star1'], f'{url_rate_opt}1'),
                (None, '난이도 미지정', f'{url_rate_opt}None'),
            ]
        }
        solve_option = {
            'var': 'solve',
            'text': self.ICON_SOLVE['filter'],
            'current': self.is_correct,
            'options': [
                ('', self.sub_title_dict['solve'][''], f'{url_solve}'),
                (True, self.sub_title_dict['solve']['True'], f'{url_solve_opt}True'),
                (False, self.sub_title_dict['solve']['False'], f'{url_solve_opt}False'),
                (None, self.sub_title_dict['solve']['None'], f'{url_solve_opt}None'),
            ]
        }
        memo_option = {
            'var': 'memo',
            'text': self.ICON_MEMO['filter'],
            'current': self.has_memo,
            'options': [
                (True, self.sub_title_dict['memo']['True'], f'{url_memo_opt}True'),
                (False, self.sub_title_dict['memo']['False'], f'{url_memo_opt}None'),
            ]
        }
        tag_option = {
            'var': 'tag',
            'text': self.ICON_TAG['filter'],
            'current': self.has_tag,
            'options': [
                (True, self.sub_title_dict['tag']['True'], f'{url_tag_opt}True'),
                (False, self.sub_title_dict['tag']['False'], f'{url_tag_opt}None'),
            ]
        }

        return {
            'year_option': year_option,
            'ex_option': ex_option,
            'sub_option': sub_option,
            'like_option': like_option,
            'rate_option': rate_option,
            'solve_option': solve_option,
            'memo_option': memo_option,
            'tag_option': tag_option,
        }

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        queryset = self.get_queryset()

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(number=self.page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
