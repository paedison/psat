from django.db.models import F, Q
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from reference.models.psat_models import PsatProblem, Psat


class BaseViewMixin(ConstantIconSet):
    menu = 'psat'
    problem_id: int

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
                '': self.ICON_MEMO['true'] + '메모 남긴 문제',
                'True': self.ICON_MEMO['true'] + '메모 남긴 문제',
                'False': self.ICON_MEMO['false'] + '메모 없는 문제',
                'None': self.ICON_MEMO['false'] + '메모 없는 문제',
            },
            'tag': {
                '': self.ICON_TAG['true'] + '태그 남긴 문제',
                'True': self.ICON_TAG['true'] + '태그 남긴 문제',
                'False': self.ICON_TAG['false'] + '태그 없는 문제',
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

        self.ip_address: str = request.META.get('REMOTE_ADDR')

        self.url_options: dict = self.get_url_options()
        self.base_url: str = reverse_lazy('psat:list', args=[self.view_type])
        self.pagination_url: str = f'{self.base_url}{self.url_options}'

    def get_url_options(self) -> dict:
        return (
            f'?year={self.year}&ex={self.ex}&sub={self.sub}&page={self.page_number}'
            f'&is_liked={self.is_liked}&rating={self.rating}&is_correct={self.is_correct}'
            f'&has_memo={self.has_memo}&has_tag={self.has_tag}&data={self.search_data}'
        )

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
            '': '', '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'pass': 'pass', 'None': None,
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
            'problem': '기출문제',
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
            if self.year and not self.ex and not self.sub:  # year
                title_parts.append(f'{self.psat.year}년 PSAT')
            elif not self.year and self.ex and not self.sub:  # ex
                title_parts.append(f'{self.psat.exam.name} PSAT')
            elif not self.year and not self.ex and self.sub:  # sub
                title_parts.append(f'{self.psat.subject.name} PSAT')
            elif self.year and self.ex and not self.sub:  # year, ex
                title_parts.append(f'{self.psat.year}년 {self.psat.exam.name}')
            elif self.year and not self.ex and self.sub:  # year, sub
                title_parts.append(f'{self.psat.year}년 {self.psat.subject.name}')
            elif not self.year and self.ex and self.sub:  # ex, sub
                title_parts.append(f'{self.psat.exam.name} {self.psat.subject.name}')
            elif self.year and self.ex and self.sub:  # year, ex, sub
                title_parts.append(f'{self.psat.year}년 {self.psat.exam.name} {self.psat.subject.name}')
            elif not self.year and not self.ex and not self.sub:  # all
                title_parts.append(f'전체 PSAT')
            sub_title = f'{" ".join(title_parts)} {title_snippet[self.view_type]}'
        else:
            for key, item in key_dict.items():
                if key == self.view_type:
                    sub_title = self.sub_title_dict[key][item]

        return sub_title, options

    def get_info(self) -> dict:
        """ Get the meta-info for the current view. """
        color_dict = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
            'memo': 'warning',
            'tag': 'primary',
        }
        return {
            'menu': 'psat',
            'view_type': self.view_type,
            'color': color_dict[self.view_type],
        }

    def get_custom_data(self) -> dict:
        """ Get all kinds of custom data. """
        problem_id = self.kwargs.get('problem_id')

        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        custom_data = (
            PsatProblem.objects
            .annotate(year=F('psat__year'), exam=F('psat__exam__name'), subject=F('psat__subject__name'))
            .order_by('-psat__year', 'id'))

        if problem_id:
            problem = PsatProblem.objects.get(id=problem_id)
            problem_data = custom_data.filter(psat_id=problem.psat_id).values(*values_list_keys)
        else:
            problem_data = {}

        if self.user_id:
            like_data = (
                self.get_list_queryset('like').annotate(is_liked=F('likes__is_liked'))
                .values(*values_list_keys, 'is_liked'))
            rate_data = (
                self.get_list_queryset('rate').annotate(rating=F('rates__rating'))
                .values(*values_list_keys, 'rating'))
            solve_data = (
                self.get_list_queryset('solve')
                .annotate(user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
                .values(*values_list_keys, 'user_answer', 'is_correct'))
            if self.has_memo:
                memo_data = custom_data.filter(memos__isnull=False, memos__user_id=self.user_id).values(*values_list_keys)
            else:
                memo_data = custom_data.exclude(memos__isnull=False, memos__user_id=self.user_id).values(*values_list_keys)
            if self.has_tag:
                tag_data = custom_data.filter(tags__isnull=False, tags__user_id=self.user_id).values(*values_list_keys)
            else:
                tag_data = custom_data.exclude(tags__isnull=False, tags__user_id=self.user_id).values(*values_list_keys)
        else:
            like_data = rate_data = solve_data = memo_data = tag_data = None

        return {
            'problem': problem_data,
            'like': like_data,
            'rate': rate_data,
            'solve': solve_data,
            'memo': memo_data,
            'tag': tag_data,
        }

    def get_list_queryset(self, view_type):
        """ Get list queryset for current view type. """
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

        memos_isnull = not self.has_memo if self.has_memo in [True, False] else None
        tags_isnull = not self.has_tag if self.has_tag in [True, False] else None
        custom_field = {
            'problem': (None, 'pass'),
            'like': ('likes__is_liked', self.is_liked),
            'rate': ('rates__rating', self.rating),
            'solve': ('solves__is_correct', self.is_correct),
            'memo': ('memos__isnull', memos_isnull),
            'tag': ('tags__isnull', tags_isnull),
            'search': ('data__contains', self.search_data),
        }
        field, value = custom_field[view_type]

        if value == 'pass':
            pass
        elif value == '':
            problem_filter &= Q(**{f'{view_type}s__isnull': False})
        else:
            if value is None:
                return queryset.exclude(**{f'{view_type}s__user_id': self.user_id})
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
        problem_filter &= Q(**user_id_filter[view_type])

        return queryset.filter(problem_filter)
