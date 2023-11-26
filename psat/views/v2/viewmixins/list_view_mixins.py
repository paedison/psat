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
        self.page_number: str = request.GET.get('page', '1')
        self.psat: Psat = self.get_psat()

        self.title = self.get_title()

        self.sub_title_dict: dict = {
            'like': {
                '': '즐겨찾기 지정',
                'True': self.ICON_LIKE['true'] + '즐겨찾기 추가',
                'False': self.ICON_LIKE['false'] + '즐겨찾기 제외',
                'None': '즐겨찾기 미지정',
            },
            'rate': {
                '': '난이도 지정',
                '5': self.ICON_RATE['star5'],
                '4': self.ICON_RATE['star4'],
                '3': self.ICON_RATE['star3'],
                '2': self.ICON_RATE['star2'],
                '1': self.ICON_RATE['star1'],
                'None': '난이도 미지정',
            },
            'solve': {
                '': '정답 확인',
                'True': self.ICON_SOLVE['true'] + '맞힌 문제',
                'False': self.ICON_SOLVE['false'] + '틀린 문제',
                'None': '정답 미확인',
            },
            'memo': {
                'True': self.ICON_MEMO['true'] + '메모 남긴 문제',
                'None': self.ICON_MEMO['false'] + '메모 없는 문제'
            },
            'tag': {
                'True': self.ICON_TAG['true'] + '태그 남긴 문제',
                'None': self.ICON_TAG['false'] + '태그 없는 문제',
            }
        }

        sub_title, view_options = self.get_view_options_sub_title()
        self.sub_title: str = sub_title
        self.is_liked: str | bool = view_options['is_liked']
        self.rating: str | int = view_options['rating']
        self.is_correct: str | bool = view_options['is_correct']
        self.has_memo: str | bool = view_options['has_memo']
        self.has_tag: str | bool = view_options['has_tag']
        self.search_data: str = view_options['search_data']

        select_options: dict = self.get_select_options()
        self.year_option: list[tuple] = select_options['year_option']
        self.ex_option: list[tuple] = select_options['ex_option']
        self.sub_option: list[tuple] = select_options['sub_option']
        self.like_option: list[tuple] = select_options['like_option']
        self.rate_option: list[tuple] = select_options['rate_option']
        self.solve_option: list[tuple] = select_options['solve_option']
        self.memo_option: list[tuple] = select_options['memo_option']
        self.tag_option: list[tuple] = select_options['tag_option']

        self.ip_address: str = request.META.get('REMOTE_ADDR')

        self.base_url: str = reverse_lazy('psat:list', args=[self.view_type])
        self.pagination_url: str = (
            f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
            f'&user_id={self.user_id}&is_liked={self.is_liked}'
            f'&rating={self.rating}&is_correct={self.is_correct}'
            f'&has_memo={self.has_memo}&has_tag={self.has_tag}'
            f'&data={self.search_data}'
        )

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

    def get_psat(self) -> Psat:
        psat_filter = Q()
        if self.year:
            psat_filter &= Q(year=self.year)
        if self.ex:
            psat_filter &= Q(exam__abbr=self.ex)
        if self.sub:
            psat_filter &= Q(subject__abbr=self.sub)
        return Psat.objects.filter(psat_filter).select_related('exam', 'subject').first()

    def get_view_options_sub_title(self) -> tuple[str, dict]:
        req_is_liked = self.request.GET.get('is_liked', '')
        req_rating = self.request.GET.get('rating', '')
        req_is_correct = self.request.GET.get('is_correct', '')
        req_has_memo = self.request.GET.get('has_memo', '')
        req_has_tag = self.request.GET.get('has_tag', '')
        req_search_data = self.request.GET.get('data', '') or self.request.POST.get('data', '')

        rating_dict = {
            '': '', '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'pass': 'pass'
        }
        rating = rating_dict[req_rating]

        opt_dict = {'': '', 'True': True, 'False': False, 'None': None}
        options = {
            'is_liked': opt_dict[req_is_liked] if self.view_type == 'like' else 'pass',
            'rating': rating if self.view_type == 'rate' else 'pass',
            'is_correct': opt_dict[req_is_correct] if self.view_type == 'solve' else 'pass',
            'has_memo': opt_dict[req_has_memo] if self.view_type == 'memo' else 'pass',
            'has_tag': opt_dict[req_has_tag] if self.view_type == 'tag' else 'pass',
            'search_data': req_search_data if self.view_type == 'search' else 'pass',
        }

        title_snippet = {
            'problem': 'PSAT 기출문제',
            'search': '검색 결과'
        }
        key_dict = {
            'like': req_is_liked,
            'rate': req_rating,
            'solve': req_is_correct,
            'memo': req_has_memo,
            'tag': req_has_tag,
        }

        sub_title = ''
        if self.view_type in ['problem', 'search']:
            title_parts = []
            if self.year or self.ex or self.sub:
                if self.year != '':
                    title_parts.append(f'{self.psat.year}년')
                if self.ex != '':
                    title_parts.append(self.psat.exam.label)
                if self.sub != '':
                    title_parts.append(self.psat.subject.name)
            else:
                title_parts.append('전체')
            sub_title = f'{" ".join(title_parts)} {title_snippet[self.view_type]}'
        else:
            for key, item in key_dict.items():
                if key == self.view_type:
                    sub_title = self.sub_title_dict[key][item]

        return sub_title, options

    def get_queryset(self):
        problem_filter = Q()
        if self.year != '':
            problem_filter &= Q(psat__year=self.year)
        if self.ex != '':
            problem_filter &= Q(psat__exam__abbr=self.ex)
        if self.sub != '':
            problem_filter &= Q(psat__subject__abbr=self.sub)

        queryset = (
            PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name')))

        memos_isnull = not self.has_memo if self.has_memo is not None else None
        tags_isnull = not self.has_tag if self.has_tag is not None else None
        custom_field = {
            'problem': (None, 'pass'),
            'like': ('likes__is_liked', self.is_liked),
            'rate': ('rates__rating', self.rating),
            'solve': ('solves__is_correct', self.is_correct),
            'memo': ('memos__isnull', memos_isnull),
            'tag': ('tags__isnull', tags_isnull),
            'search': ('data__contains', self.search_data),
        }
        field, value = custom_field[self.view_type]

        if value == 'pass':
            pass
        elif value == '':
            problem_filter &= Q(**{f'{self.view_type}s__isnull': False})
        else:
            if value is None:
                return queryset.exclude(**{f'{self.view_type}s__user_id': self.user_id})
            elif value != '':
                problem_filter &= Q(**{field: value})

        user_id_filter = {
            'problem': {},
            'like': {'likes__user_id': self.user_id},
            'rate': {'rates__user_id': self.user_id},
            'solve': {'solves__user_id': self.user_id},
            'memo': {'memos__user_id': self.user_id},
            'tag': {'tags__user_id': self.user_id},
            'search': {},
        }
        problem_filter &= Q(**user_id_filter[self.view_type])

        return queryset.filter(problem_filter)

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

        like_option = [
            ('', self.sub_title_dict['like'][''], f'{url_like}'),
            (True, self.sub_title_dict['like']['True'], f'{url_like_opt}True'),
            (False, self.sub_title_dict['like']['False'], f'{url_like_opt}False'),
            (None, self.sub_title_dict['like']['None'], f'{url_like_opt}None'),
        ]
        rate_option = [
            ('', '난이도 지정', f'{url_rate}'),
            (5, self.ICON_RATE['star5'], f'{url_rate_opt}5'),
            (4, self.ICON_RATE['star4'], f'{url_rate_opt}4'),
            (3, self.ICON_RATE['star3'], f'{url_rate_opt}3'),
            (2, self.ICON_RATE['star2'], f'{url_rate_opt}2'),
            (1, self.ICON_RATE['star1'], f'{url_rate_opt}1'),
            (None, '난이도 미지정', f'{url_rate_opt}None'),
        ]
        solve_option = [
            ('', self.sub_title_dict['solve'][''], f'{url_solve}'),
            (True, self.sub_title_dict['solve']['True'], f'{url_solve_opt}True'),
            (False, self.sub_title_dict['solve']['False'], f'{url_solve_opt}False'),
            (None, self.sub_title_dict['solve']['None'], f'{url_solve_opt}None'),
        ]
        memo_option = [
            (True, self.sub_title_dict['memo']['True'], f'{url_memo_opt}True'),
            (None, self.sub_title_dict['memo']['None'], f'{url_memo_opt}None'),
        ]
        tag_option = [
            (True, self.sub_title_dict['tag']['True'], f'{url_tag_opt}True'),
            (None, self.sub_title_dict['tag']['None'], f'{url_tag_opt}None'),
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
