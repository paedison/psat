from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from psat.models import Open, Like, Rate, Solve, Memo, Tag
from reference.models import PsatProblem, Exam, Subject
from dashboard.models.psat_data_models import (
    PsatOpenLog,
    PsatLikeLog,
    PsatRateLog,
    PsatSolveLog,
)


class PsatCommonVariableSet(ConstantIconSet):
    """Represent PSAT common variable."""
    menu = 'psat'
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def ip_address(self) -> str:
        return self.request.META.get('REMOTE_ADDR')

    @property
    def view_type(self) -> str:
        """Get view type from [ problem, like, rate, solve ]. """
        return self.kwargs.get('view_type', 'problem')

    @property
    def color(self) -> str:
        ret = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
        }
        return ret[self.view_type]

    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'color': self.color,
        }


class PsatProblemVariableSet(PsatCommonVariableSet):
    """Represent PSAT single problem variable."""

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

    @property
    def find_filter(self) -> dict:
        filter_dict = {'problem_id': self.problem_id}
        if self.user_id:
            filter_dict.update({'user_id': self.user_id})
        else:
            filter_dict.update({'ip_address': self.ip_address})
        return filter_dict


class PsatCustomVariableSet:
    """Represent PSAT custom data variable."""
    request: any
    psat_id: int
    user_id: int
    view_type: str
    problem_id: int

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
        custom_data_dict = {
            'problem': self.problem_data,
            'like': self.like_data,
            'rate': self.rate_data,
            'solve': self.solve_data,
        }
        return custom_data_dict[self.view_type]


class PsatListViewMixIn(
    PsatCommonVariableSet,
    PsatCustomVariableSet,
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
            )).distinct().values_list('psat__year', 'year_suffix').order_by('-psat__year')
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
    PsatProblemVariableSet,
    PsatCustomVariableSet,
):
    """Represent PSAT detail view mixin."""
    url_name = 'psat_v2:detail'

    def get_open_instance(self):
        with transaction.atomic():
            instance, is_created = Open.objects.get_or_create(**self.find_filter)
            recent_log = PsatOpenLog.objects.filter(**self.find_filter).last()
            if recent_log:
                repetition = recent_log.repetition + 1
            else:
                repetition = 1
            create_filter = self.find_filter.copy()
            extra_filter = {
                'data_id': instance.id,
                'repetition': repetition,
            }
            create_filter.update(extra_filter)
            PsatOpenLog.objects.create(**create_filter)

    ##########################
    # Navigation & list data #
    ##########################

    @property
    def prev_next_prob(self):
        if self.request.method == 'GET':
            custom_list = list(self.custom_data.values_list('id', flat=True))
            prev_prob = next_prob = None
            last_id = len(custom_list) - 1
            q = custom_list.index(self.problem_id)
            if q != 0:
                prev_prob = self.custom_data[q-1]
            if q != last_id:
                next_prob = self.custom_data[q+1]
            return prev_prob, next_prob

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

    @property
    def my_tag(self):
        if self.request.user.is_authenticated:
            return Tag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()


class PsatCustomUpdateViewMixIn(
    PsatProblemVariableSet,
):
    """Represent PSAT custom data update view mixin."""
    @property
    def is_liked(self) -> bool:
        is_liked = self.request.POST.get('is_liked', '')
        bool_dict = {
            'True': True,
            'False': False,
            'None': False,
        }
        return '' if is_liked == '' else not bool_dict[is_liked]

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
    def update_filter(self) -> dict:
        filter_expr = {
            'problem': {},
            'like': {'is_liked': self.is_liked},
            'rate': {'rating': self.rating},
            'solve': {
                'answer': self.answer,
                'is_correct': self.answer == self.problem.answer,
            },
        }
        return filter_expr[self.view_type]

    @property
    def create_filter(self) -> dict:
        create_filter = self.find_filter.copy()
        create_filter.update(self.update_filter)
        return create_filter

    @property
    def data_instance(self):
        return self.get_data_instance()

    def get_data_instance(self):
        if self.data_model:
            try:
                instance = self.data_model.objects.get(**self.find_filter)
                update_filter = self.update_filter.copy()
                for key, item in update_filter.items():
                    setattr(instance, key, item)
                instance.save()
            except ObjectDoesNotExist:
                instance = self.data_model.objects.create(**self.create_filter)
            return instance

    def make_log_instance(self):
        if self.data_instance:
            filter_expr = self.create_filter.copy()
            model_dict = {
                'like': PsatLikeLog,
                'rate': PsatRateLog,
                'solve': PsatSolveLog,
            }
            model = model_dict[self.view_type]
            data_id = self.data_instance.id
            recent_log = model.objects.filter(**self.find_filter).order_by('-id').first()
            repetition = recent_log.repetition + 1 if recent_log else 1
            filter_expr.update(
                {'repetition': repetition, 'data_id': data_id}
            )
            model.objects.create(**filter_expr)


class PsatSolveModalViewMixIn:
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
