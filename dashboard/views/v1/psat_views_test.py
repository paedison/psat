from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from vanilla import TemplateView

from dashboard.models import PsatLikeLog, PsatRateLog, PsatSolveLog
from reference.models import PsatProblem


class PsatCommonVariableSet:
    """Represent PSAT common variable."""
    menu = 'psat'
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    # @property
    # def view_type(self) -> str:
    #     """Get view type from [ problem, like, rate, solve ]. """
    #     return self.kwargs.get('view_type', 'problem')

    @property
    def color(self) -> str:
        return {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
        }

    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': self.menu,
            'color': self.color,
        }


class PsatProblemVariableSet:
    """Represent PSAT single problem variable."""
    kwargs: dict

    @property
    def problem_id(self) -> int:
        return int(self.kwargs.get('problem_id'))

    @property
    def problem(self):
        return (
            PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .get(id=self.problem_id)
        )

    @property
    def psat_id(self) -> int:
        return self.problem.psat_id


class PsatCustomVariableSet:
    """Represent PSAT custom data variable."""
    psat_id: int
    user_id: int

    @property
    def problem_data(self):
        return PsatProblem.objects.filter(psat_id=self.psat_id).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number',
        )

    @property
    def like_data(self):
        return (
            PsatProblem.objects.filter(likes__user_id=self.user_id, likes__is_liked=True)
            .prefetch_related('likes').order_by('-psat__year', 'id')
            .values(
                'id', 'psat_id', 'psat__year', 'psat__exam__name',
                'psat__subject__name', 'number', 'likes__is_liked',
            )
        )

    @property
    def rate_data(self):
        return (
            PsatProblem.objects.filter(rates__user_id=self.user_id)
            .prefetch_related('rates').order_by('-psat__year', 'id')
        ).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number', 'rates__rating',
        )

    @property
    def solve_data(self):
        return (
            PsatProblem.objects.filter(solves__user_id=self.user_id)
            .prefetch_related('solves').order_by('-psat__year', 'id')
        ).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number', 'solves__is_correct',
        )

    @property
    def custom_data(self):
        return {
            'problem': self.problem_data,
            'like': self.like_data,
            'rate': self.rate_data,
            'solve': self.solve_data,
        }


class PsatIconConstantSet:
    """Represent PSAT icon constant."""
    ICON_LIKE = {
        'true': '<i class="fa-solid fa-heart"></i>',
        'false': '<i class="fa-regular fa-heart"></i>',
    }
    ICON_RATE = {
        'star0': (
            f'<i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i>'
            f'<i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i>'
            f'<i class="fa-regular fa-star"></i>'
        ),
        'star1': (
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-regular fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i><i class="fa-regular fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i>'
        ),
        'star2': (
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i><i class="fa-regular fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i>'
        ),
        'star3': (
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-regular fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i>'
        ),
        'star4': (
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-regular fa-star m-0"></i>'
        ),
        'star5': (
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-solid fa-star m-0"></i><i class="fa-solid fa-star m-0"></i>'
            f'<i class="fa-solid fa-star m-0"></i>'
        ),
    }
    ICON_SOLVE = {
        'none': '',
        'wrong': '<i class="fa-solid fa-circle-xmark"></i>',
        'correct': '<i class="fa-solid fa-circle-check"></i>',
    }
    ICON_NAV = {
        'left_arrow': '<i class="fa-solid fa-arrow-left"></i>',
        'prev_prob': '<i class="fa-solid fa-arrow-up"></i>',
        'next_prob': '<i class="fa-solid fa-arrow-down"></i>',
        'list': '<i class="fa-solid fa-list"></i>',
    }
    ICON_MENU = {
        'psat': '<i class="fa-solid fa-layer-group fa-fw"></i>',
        'problem': '<i class="fa-solid fa-file-lines fa-fw"></i>',
        'like': '<i class="fa-solid fa-heart fa-fw"></i>',
        'rate': '<i class="fa-solid fa-star fa-fw"></i>',
        'solve': '<i class="fa-solid fa-circle-check fa-fw"></i>',
        'search': '<i class="fa-solid fa-magnifying-glass fa-fw"></i>',
    }
    ICON_FILTER = '<i class="fa-solid fa-filter"></i>'
    ICON_SUBJECT = {
        '전체': '<i class="fa-solid fa-bars fa-fw"></i>',
        '언어': '<i class="fa-solid fa-language fa-fw"></i>',
        '자료': '<i class="fa-solid fa-table-cells-large fa-fw"></i>',
        '상황': '<i class="fa-solid fa-scale-balanced fa-fw"></i>',
        '헌법': '<i class="fa-solid fa-gavel"></i>',
    }
    icon_search = '<i class="fa-solid fa-magnifying-glass fa-fw"></i>'
    icon_tag = '<i class="fa-solid fa-tag fa-fw"></i>'


class PsatListViewMixIn(
    PsatCommonVariableSet,
    PsatCustomVariableSet,
    PsatIconConstantSet,
):
    """Represent PSAT list view mixin."""
    url_name = 'psat_v2:list'

    #############
    # Variables #
    #############

    @property
    def year(self) -> str | int:
        year = self.request.GET.get('year', '')
        return '' if year == '' else int(year)

    @property
    def ex(self) -> str:
        return self.request.GET.get('ex', '')

    @property
    def sub(self) -> str:
        return self.request.GET.get('sub', '')

    @property
    def page_number(self):
        return self.request.GET.get('page', 1)

    @property
    def is_liked(self) -> str | bool:
        is_liked = self.request.GET.get('is_liked', '')
        is_liked_dict = {'True': True, 'False': False}
        return '' if is_liked == '' else is_liked_dict[is_liked]

    @property
    def rating(self) -> str | int:
        rating = self.request.GET.get('rating', '')
        return '' if rating == '' else int(rating)

    @property
    def is_correct(self) -> str | bool:
        is_correct = self.request.GET.get('is_correct', '')
        is_correct_dict = {'': None, 'True': True, 'False': False}
        return '' if is_correct == '' else is_correct_dict[is_correct]

    @property
    def search_data(self) -> str:
        if self.request.method == 'GET':
            return self.request.GET.get('data', '')
        return self.request.POST.get('data', '')

    #########
    # Title #
    #########

    @property
    def title(self) -> str:
        return {
            'problem': 'PSAT 기출문제',
            'like': 'PSAT 즐겨찾기',
            'rate': 'PSAT 난이도',
            'solve': 'PSAT 정답확인',
            'search': 'PSAT 검색 결과',
        }

    ##################
    # Filter options #
    ##################

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    @property
    def year_option(self) -> list[tuple]:
        year_list = self.queryset.annotate(
            year_suffix=Cast(
                Concat(F('psat__year'), Value('년')), CharField()
            )).distinct().values_list('psat__year', 'year_suffix').order_by('psat__year')
        return self.get_option(year_list)

    @property
    def ex_option(self) -> list[tuple]:
        ex_list = self.queryset.distinct().values_list(
            'psat__exam__abbr', 'psat__exam__label').order_by('psat__exam_id')
        return self.get_option(ex_list)

    @property
    def sub_option(self) -> list[tuple]:
        sub_list = self.queryset.distinct().values_list(
            'psat__subject__abbr', 'psat__subject__name').order_by('psat__subject_id')
        new_sub_list = [
            (sub[0], f'{self.ICON_SUBJECT[sub[0]]}{sub[1]}') for sub in list(sub_list)
        ]
        return self.get_option(new_sub_list)

    @property
    def like_option(self) -> list[tuple]:
        return [(True, f'{self.ICON_LIKE["true"]}즐겨찾기 추가 문제'),
                (False, f'{self.ICON_LIKE["false"]}즐겨찾기 제외 문제')]

    @property
    def rate_option(self) -> list[tuple]:
        return [(5, self.ICON_RATE['star5']),
                (4, self.ICON_RATE['star4']),
                (3, self.ICON_RATE['star3']),
                (2, self.ICON_RATE['star2']),
                (1, self.ICON_RATE['star1'])]

    @property
    def solve_option(self) -> list[tuple]:
        return [(True, f'{self.ICON_SOLVE["correct"]}맞힌 문제'),
                (False, f'{self.ICON_SOLVE["wrong"]}틀린 문제')]

    ########################
    # Queryset & paginator #
    ########################

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        paginator = Paginator(self.queryset, 10)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(
            number=self.page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    @property
    def queryset(self):
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
            'search': {'data__contains': self.search_data},
        }
        problem_filter &= Q(**additional_filter[self.view_type])

        return (
            PsatProblem.objects.filter(problem_filter)
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
        )


class PsatListView(
    PsatListViewMixIn,
    TemplateView,
):
    """ Represent PSAT base list view. """
    template_name = 'psat/v2/problem_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        page_obj, page_range = self.get_paginator_info()
        return {
            # Variables
            'year': self.year,
            'ex': self.ex,
            'sub': self.sub,
            'page_number': self.page_number,
            'is_liked': self.is_liked,
            'rating': self.rating,
            'is_correct': self.is_correct,
            'search_data': self.search_data,

            # Info & title
            'info': self.info,
            'title': self.title,

            # Filter options
            'year_option': self.year_option,
            'ex_option': self.ex_option,
            'sub_option': self.sub_option,
            'like_option': self.like_option,
            'rate_option': self.rate_option,
            'solve_option': self.solve_option,

            # Paginator
            'page_obj': page_obj,
            'page_range': page_range,

            # Custom data
            'like_logs': self.like_data,
            'rate_logs': self.rate_data,
            'solve_logs': self.solve_data,

            # Icons
            'icon_like': self.ICON_LIKE,
            'icon_rate': self.ICON_RATE,
            'icon_solve': self.ICON_SOLVE,
            'icon_filter': self.ICON_FILTER,
        }


base_view = PsatListView.as_view()
