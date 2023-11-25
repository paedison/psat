from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_view_mixins import PsatViewInfo, PsatCustomDataSet
from reference.models.psat_models import Psat, PsatProblem


class ListVariable(ConstantIconSet):
    menu = 'psat'

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs

        self.user_id: int | None = request.user.id if request.user.is_authenticated else None
        self.view_type: str = kwargs.get('view_type', 'problem')

        year: str = request.GET.get('year', '')
        self.year: int | str = '' if year == '' else int(year)

        self.ex: str = request.GET.get('ex', '')
        self.sub: str = request.GET.get('sub', '')
        self.page_number: str | int = request.GET.get('page', 1)

        options = self.get_request_options()
        self.is_liked: str | bool = options['is_liked']
        self.rating: str | int = options['rating']
        self.is_correct: str | bool = options['is_correct']
        self.has_memo: str | bool = options['has_memo']
        self.has_tag: str | bool = options['has_tag']
        self.search_data: str = options['search_data']

        self.ip_address: str = request.META.get('REMOTE_ADDR')

        self.base_url: str = reverse_lazy('psat:list', args=[self.view_type])
        self.pagination_url: str = (
            f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
            f'&user_id={self.user_id}&is_liked={self.is_liked}'
            f'&rating={self.rating}&is_correct={self.is_correct}'
            f'&data={self.search_data}'
        )

    def get_request_options(self) -> dict:
        true_false_dict = {'True': True, 'False': False}

        req_is_liked = self.request.GET.get('is_liked') if self.view_type == 'like' else ''
        req_rating = self.request.GET.get('rating') if self.view_type == 'rate' else ''
        req_is_correct = self.request.GET.get('is_correct') if self.view_type == 'solve' else ''
        req_has_memo = self.request.GET.get('has_memo') if self.view_type == 'memo' else ''
        req_has_tag = self.request.GET.get('has_tag') if self.view_type == 'tag' else ''
        req_search_data = self.request.GET.get('data', '') or self.request.POST.get('data', '')

        return {
            'is_liked': '' if req_is_liked == '' else true_false_dict[req_is_liked],
            'rating': '' if req_rating == '' else int(req_rating),
            'is_correct': '' if req_is_correct == '' else true_false_dict[req_is_correct],
            'has_memo': '' if req_has_memo == '' else true_false_dict[req_has_memo],
            'has_tag': '' if req_has_tag == '' else true_false_dict[req_has_tag],
            'search_data': req_search_data if self.view_type == 'search' else '',
        }

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
        problem_filter = Q()
        if self.year != '':
            problem_filter &= Q(psat__year=self.year)
        if self.ex != '':
            problem_filter &= Q(psat__exam__abbr=self.ex)
        if self.sub != '':
            problem_filter &= Q(psat__subject__abbr=self.sub)

        custom_field = {
            'problem': (None, None),
            'like': ('likes__is_liked', self.is_liked),
            'rate': ('rates__rating', self.rating),
            'solve': ('solves__is_correct', self.is_correct),
            'memo': (None, None),
            'tag': (None, None),
            'search': (None, None),
        }
        field, value = custom_field[self.view_type]
        if value == '':
            field += '__isnull'
            value = False
        if field is not None:
            problem_filter &= Q(**{field: value})

        additional_filter = {
            'problem': {},
            'like': {'likes__user_id': self.user_id},
            'rate': {'rates__user_id': self.user_id},
            'solve': {'solves__user_id': self.user_id},
            'memo': {'memos__user_id': self.user_id},
            'tag': {'tags__user_id': self.user_id},
            'search': {'data__contains': self.search_data},
        }
        problem_filter &= Q(**additional_filter[self.view_type])

        return (
            PsatProblem.objects.filter(problem_filter)
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
        )

    def get_sub_title(self) -> str:
        psat_filter = Q()
        if self.year:
            psat_filter &= Q(year=self.year)
        if self.ex:
            psat_filter &= Q(exam__abbr=self.ex)
        if self.sub:
            psat_filter &= Q(subject__abbr=self.sub)
        psat = Psat.objects.filter(psat_filter).select_related('exam', 'subject').first()

        title_parts = []
        sub_title = ''

        if self.view_type == 'problem':
            if self.year or self.ex or self.sub:
                if self.year != '':
                    title_parts.append(f'{psat.year}년')
                if self.ex != '':
                    title_parts.append(psat.exam.label)
                if self.sub != '':
                    title_parts.append(psat.subject.name)
                sub_title = f'{" ".join(title_parts)} PSAT 기출문제'
            else:
                sub_title = '전체 PSAT 기출문제'

        elif self.view_type == 'like':
            if self.is_liked:
                sub_title = self.ICON_LIKE['true'] + ' 즐겨찾기 추가'
            else:
                sub_title = self.ICON_LIKE['false'] + ' 즐겨찾기 제외'

        elif self.view_type == 'rate':
            sub_title = self.ICON_RATE[f'star{self.rating}']

        elif self.view_type == 'solve':
            if self.is_correct:
                sub_title = self.ICON_SOLVE['true'] + ' 맞힌 문제'
            else:
                sub_title = self.ICON_SOLVE['false'] + ' 틀린 문제'

        elif self.view_type == 'memo':
            if self.has_memo:
                sub_title = self.ICON_MEMO['true'] + ' 메모 달린 문제'
            else:
                sub_title = self.ICON_MEMO['false'] + ' 메모 없는 문제'

        elif self.view_type == 'tag':
            if self.has_tag:
                sub_title = self.ICON_TAG['true'] + ' 태그 달린 문제'
            else:
                sub_title = self.ICON_TAG['false'] + ' 태그 없는 문제'

        elif self.view_type == 'search':
            if self.year or self.ex or self.sub:
                if self.year != '':
                    title_parts.append(f'{psat.year}년')
                if self.ex != '':
                    title_parts.append(psat.exam.label)
                if self.sub != '':
                    title_parts.append(psat.subject.name)
                sub_title = f'{" ".join(title_parts)} 검색 결과'
            else:
                sub_title = '전체 검색 결과'

        return sub_title

    def get_options(self) -> dict:
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

        like_option = [
            (True, f'{self.ICON_LIKE["true"]}즐겨찾기 추가'),
            (False, f'{self.ICON_LIKE["false"]}즐겨찾기 제외')
        ]
        rate_option = [
            (5, self.ICON_RATE['star5']),
            (4, self.ICON_RATE['star4']),
            (3, self.ICON_RATE['star3']),
            (2, self.ICON_RATE['star2']),
            (1, self.ICON_RATE['star1'])
        ]
        solve_option = [
            (True, f'{self.ICON_SOLVE["true"]}맞힌 문제'),
            (False, f'{self.ICON_SOLVE["false"]}틀린 문제')
        ]
        memo_option = [
            (True, f'{self.ICON_MEMO["true"]}메모 남긴 문제'),
            (False, f'{self.ICON_MEMO["false"]}메모 없는 문제')
        ]
        tag_option = [
            (True, f'{self.ICON_TAG["true"]}태그 달린 문제'),
            (False, f'{self.ICON_TAG["false"]}태그 없는 문제')
        ]

        return {
            'year_option': get_option(year_list),
            'ex_option': get_option(ex_list),
            'sub_option': get_option(new_sub_list),
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


class PsatListViewMixIn(
    ConstantIconSet,
    PsatViewInfo,
    PsatCustomDataSet,
):
    """Represent PSAT list view mixin."""

    @staticmethod
    def get_list_variable(request, **kwargs):
        return ListVariable(request, **kwargs)
