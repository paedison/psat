from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from psat.models import Like, Rate, Solve, Memo, Tag
from reference.models import PsatProblem, Exam, Subject


class PsatCommonVariableSet:
    """Represent PSAT common variable."""
    menu = 'psat'
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def view_type(self) -> str:
        """Get view type from [ problem, like, rate, solve ]. """
        return self.kwargs.get('view_type', 'problem')

    @property
    def color(self) -> str:
        color_dict = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
        }
        return color_dict[self.view_type]

    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
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
    user_id: int

    @property
    def like_data(self):
        return Like.objects.filter(user_id=self.user_id).only(
            'timestamp', 'problem_id', 'is_liked')

    @property
    def rate_data(self):
        return Rate.objects.filter(user_id=self.user_id).only(
            'timestamp', 'problem_id', 'rating')

    @property
    def solve_data(self):
        return Solve.objects.filter(user_id=self.user_id).only(
            'timestamp', 'problem_id', 'answer', 'is_correct')


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

    ########
    # Urls #
    ########

    @property
    def base_url(self) -> str:
        return reverse_lazy(self.url_name, args=[self.view_type])

    @property
    def pagination_url(self) -> str:
        return (f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
                f'&user_id={self.request.user.id}&is_liked={self.is_liked}'
                f'&rating={self.rating}&is_correct={self.is_correct}'
                f'&data={self.search_data}')

    #########
    # Title #
    #########

    @property
    def title(self) -> str:
        title_dict = {
            'problem': 'PSAT 기출문제',
            'like': 'PSAT 즐겨찾기',
            'rate': 'PSAT 난이도',
            'solve': 'PSAT 정답확인',
            'search': 'PSAT 검색 결과',
        }
        return title_dict[self.view_type]

    @property
    def sub_title(self):
        exam_list = dict(Exam.objects.filter(category__name='PSAT').values_list('abbr', 'label'))
        subject_list = dict(Subject.objects.filter(category__name='PSAT').values_list('abbr', 'name'))
        title_parts = []
        sub_title = ''
        if self.view_type == 'problem':
            if self.year or self.ex or self.sub:
                if self.year != '':
                    title_parts.append(f'{self.year}년')
                if self.ex != '':
                    title_parts.append(f'"{exam_list[self.ex]}"')
                if self.sub != '':
                    title_parts.append(subject_list[self.sub])
                sub_title = f'[{" ".join(title_parts)}]'
        return sub_title

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


class PsatDetailViewMixIn(
    PsatCommonVariableSet,
    PsatProblemVariableSet,
    PsatIconConstantSet,
):
    """Represent PSAT detail view mixin."""
    url_name = 'psat_v2:detail'

    ##########################
    # Navigation & list data #
    ##########################

    @property
    def prev_next_prob(self):
        custom_list = list(self.custom_data.values_list('id', flat=True))
        if self.request.method == 'GET':
            last_id = len(custom_list) - 1
            q = custom_list.index(self.problem_id)
            prev_prob = self.custom_data.get(id=custom_list[q - 1]) if q != 0 else None
            next_prob = self.custom_data.get(id=custom_list[q + 1]) if q != last_id else None
            return prev_prob, next_prob

    @property
    def custom_data(self):
        filter_dict = {
            'problem': {'psat': self.psat_id},
            'like': {
                'likes__user_id': self.user_id,
                'likes__is_liked': True,
            },
            'rate': {'rates__user_id': self.user_id},
            'solve': {'solves__user_id': self.user_id},
        }
        return (
            PsatProblem.objects.filter(**filter_dict[self.view_type])
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .prefetch_related('psat', 'psat__exam', 'psat__subject')
        )

    @property
    def list_data(self) -> list:
        organized_dict = {}
        organized_list = []
        target_data = self.custom_data.values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number'
        )

        for prob in target_data:
            key = prob['psat_id']
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam2, subject = prob['psat__year'], prob['psat__exam__name'], prob['psat__subject__name']
            problem_url = reverse_lazy(
                self.url_name,
                kwargs={'view_type': self.view_type, 'problem_id': prob['id']}
            )
            list_item = {
                'exam_name': f"{year}년 '{exam2}' {subject}",
                'problem_number': prob['number'],
                'problem_id': prob['id'],
                'problem_url': problem_url
            }
            organized_dict[key].append(list_item)

        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i + 5]
                organized_list.extend(row)
        return organized_list

    ##############
    # Memo & tag #
    ##############

    @property
    def memo(self):
        if self.request.user.is_authenticated:
            return Memo.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
        return None

    @property
    def my_tag(self):
        if self.request.user.is_authenticated:
            return Tag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
        return None


class PsatCustomUpdateViewMixIn(
    PsatCommonVariableSet,
    PsatProblemVariableSet,
    PsatIconConstantSet,
):
    """Represent PSAT custom data update view mixin."""
    @property
    def rating(self) -> int:
        rating = self.request.POST.get('rating', '')
        return '' if rating == '' else int(rating)

    @property
    def answer(self) -> int:
        answer = self.request.POST.get('answer', '')
        return '' if answer == '' else int(answer)

    @property
    def data_model(self):
        model_dict = {
            'problem': None,
            'like': Like,
            'rate': Rate,
            'solve': Solve,
        }
        return model_dict[self.view_type]

    @property
    def option_name(self) -> str:
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        return option_dict[self.view_type]

    @property
    def data_instance(self):
        filter_expr = {
            'user_id': self.user_id,
            'problem': self.problem,
        }
        if self.data_model:
            try:
                instance = self.data_model.objects.get(**filter_expr)
                if self.view_type == 'like':
                    instance.is_liked = not instance.is_liked
                elif self.view_type == 'rate':
                    instance.rating = self.rating
                elif self.view_type == 'solve':
                    instance.answer = self.answer
                    instance.is_correct = self.answer == self.problem.answer
                instance.save()
            except ObjectDoesNotExist:
                additional_expr = {
                    'like': {'is_liked': True},
                    'rate': {'rating': self.rating},
                    'solve': {
                        'answer': self.answer,
                        'is_correct': self.answer == self.problem.answer,
                    },
                }
                filter_expr.update(additional_expr[self.view_type])
                instance = self.data_model.objects.create(**filter_expr)
            return instance


class PsatSolveModalViewMixIn(
    PsatIconConstantSet,
):
    """Represent PSAT Solve data update modal view mixin."""
    request: any

    @property
    def problem_id(self) -> int:
        return int(self.request.POST.get('problem_id'))

    @property
    def answer(self) -> int | None:
        answer = self.request.POST.get('answer')
        return int(answer) if answer else None

    @property
    def is_correct(self) -> bool | None:
        problem = PsatProblem.objects.get(id=self.problem_id)
        return None if self.answer is None else (self.answer == problem.answer)
