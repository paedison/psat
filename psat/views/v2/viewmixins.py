from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from psat.models import Like, Rate, Solve, Memo, Tag
from reference.models import PsatProblem, Exam, Subject


class PsatIconSet:
    icon_like = {
        'true': '<i class="fa-solid fa-heart"></i>',
        'false': '<i class="fa-regular fa-heart"></i>',
    }
    icon_rate = {
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
    icon_solve = {
        'wrong': '<i class="fa-solid fa-circle-xmark"></i>',
        'correct': '<i class="fa-solid fa-circle-check"></i>',
    }
    icon_nav = {
        'left_arrow': '<i class="fa-solid fa-arrow-left"></i>',
        'prev_prob': '<i class="fa-solid fa-arrow-up"></i>',
        'next_prob': '<i class="fa-solid fa-arrow-down"></i>',
        'list': '<i class="fa-solid fa-list"></i>',
    }
    icon_solve_none = ''
    icon_answerCheck = '<i class="fa-solid fa-check"></i>'
    icon_filter = '<i class="fa-solid fa-filter"></i>'
    icon_all = '<i class="fa-solid fa-bars fa-fw"></i>'
    icon_eoneo = '<i class="fa-solid fa-language fa-fw"></i>'
    icon_jaryo = '<i class="fa-solid fa-table-cells-large fa-fw"></i>'
    icon_sanghwang = '<i class="fa-solid fa-scale-balanced fa-fw"></i>'
    icon_search = '<i class="fa-solid fa-magnifying-glass fa-fw"></i>'
    icon_tag = '<i class="fa-solid fa-tag fa-fw"></i>'

    icon_menu = {
        'psat': '<i class="fa-solid fa-layer-group fa-fw"></i>',
        'problem': '<i class="fa-solid fa-file-lines fa-fw"></i>',
        'like': '<i class="fa-solid fa-heart fa-fw"></i>',
        'rate': '<i class="fa-solid fa-star fa-fw"></i>',
        'solve': '<i class="fa-solid fa-circle-check fa-fw"></i>',
        'search': '<i class="fa-solid fa-magnifying-glass fa-fw"></i>',
    }


class PsatListViewMixIn(PsatIconSet):
    """
    Represent PSAT list view mixin.
    view_type(str): One of [ problem, like, rate, solve ]
    """
    kwargs: dict
    view_type: str  # One of [ problem, like, rate, solve ]
    request: any
    prob_data: PsatProblem.objects

    url_name = 'psat_v2:list'
    menu = 'psat'

    #######################
    # List view variables #
    #######################

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def view_type(self) -> str:
        return self.kwargs.get('view_type', 'problem')

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
        else:
            return self.request.POST.get('data', '')

    ##################
    # List view urls #
    ##################

    @property
    def base_url(self) -> str:
        return reverse_lazy(self.url_name, args=[self.view_type])

    @property
    def pagination_url(self) -> str:
        return (f'{self.base_url}?year={self.year}&ex={self.ex}&sub={self.sub}'
                f'&user_id={self.request.user.id}&is_liked={self.is_liked}'
                f'&rating={self.rating}&is_correct={self.is_correct}'
                f'&data={self.search_data}')

    ##########################
    # List view info & title #
    ##########################

    @property
    def info(self) -> dict:
        """ Get all the info for the current view. """
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',  # Different in dashboard views
        }

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

    ############################
    # List view filter options #
    ############################

    @staticmethod
    def get_option(target) -> list[tuple]:
        target_option = []
        for t in target:
            if t not in target_option:
                target_option.append(t)
        return target_option

    @property
    def like_option(self) -> list[tuple]:
        return [(True, f'{self.icon_like["true"]}즐겨찾기 추가 문제'),
                (False, f'{self.icon_like["false"]}즐겨찾기 제외 문제')]

    @property
    def rate_option(self) -> list[tuple]:
        return [(5, self.icon_rate['star5']),
                (4, self.icon_rate['star4']),
                (3, self.icon_rate['star3']),
                (2, self.icon_rate['star2']),
                (1, self.icon_rate['star1'])]

    @property
    def solve_option(self) -> list[tuple]:
        return [(True, f'{self.icon_solve["correct"]}맞힌 문제'),
                (False, f'{self.icon_solve["wrong"]}틀린 문제')]

    ###########################
    # List view queryset info #
    ###########################

    @property
    def problem_filter(self) -> Q:
        """ Get problem filter corresponding to the year, ex, sub. """
        problem_filter = Q()
        if self.year != '':
            problem_filter &= Q(psat__year=self.year)
        if self.ex != '':
            problem_filter &= Q(psat__exam__abbr=self.ex)
        if self.sub != '':
            problem_filter &= Q(psat__subject__abbr=self.sub)
        return problem_filter

    def get_filtered_queryset(self, field='', value=''):
        """ Get filtered queryset for like, rate, solve views. """
        problem_filter = self.problem_filter
        additional_filter = {
            'problem': {},
            'like': {'likes__user_id': self.request.user.id},
            'rate': {'rates__user_id': self.request.user.id},
            'solve': {'solves__user_id': self.request.user.id},
        }
        if self.view_type == 'search':
            problem_filter &= Q(data__contains=self.search_data)
        else:
            problem_filter &= Q(**additional_filter[self.view_type])
            if self.view_type != 'problem':
                if value == '':
                    problem_filter &= Q(**{field + '__isnull': False})
                else:
                    problem_filter &= Q(**{field: value})
        return PsatProblem.objects.filter(problem_filter)

    @property
    def queryset(self):
        opt_dict = {
            'problem': {'', ''},
            'like': {'likes__is_liked': self.is_liked},
            'rate': {'rates__rating': self.rating},
            'solve': {'solves__is_correct': self.is_correct},
            'search': {'', ''}
        }
        return self.get_filtered_queryset(*opt_dict[self.view_type])

    @property
    def year_option(self) -> list[tuple]:
        year_list = self.queryset.annotate(
            year_suffix=Cast(
                Concat(F('psat__year'), Value('년')), CharField()
            )).values_list('psat__year', 'year_suffix')
        return self.get_option(year_list)

    @property
    def ex_option(self) -> list[tuple]:
        ex_list = self.queryset.values_list('psat__exam__abbr', 'psat__exam__label')
        return self.get_option(ex_list)

    @property
    def sub_option(self) -> list[tuple]:
        sub_list = self.queryset.values_list('psat__subject__abbr', 'psat__subject__name')
        return self.get_option(sub_list)


class PsatDetailViewMixIn(PsatIconSet):
    """
    Represent PSAT detail mixin.
    view_type(str): One of [ problem, like, rate, solve ]
    """
    kwargs: dict
    view_type: str  # One of [ problem, like, rate, solve ]
    request: any
    prob_data: PsatProblem.objects

    url_name = 'psat_v2:detail'
    menu = 'psat'

    #########################
    # Detail view variables #
    #########################

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def view_type(self) -> str:
        return self.kwargs.get('view_type', 'problem')

    @property
    def problem_id(self) -> int:
        return int(self.kwargs.get('problem_id'))

    @property
    def problem(self):
        return PsatProblem.objects.get(id=self.problem_id)

    @property
    def object(self): return self.problem

    @property
    def prob_list(self) -> list:
        return self.prob_data.values_list('id', flat=True)

    @property
    def rating(self) -> int:
        rating = self.request.POST.get('rating', '')
        return '' if rating == '' else int(rating)

    @property
    def answer(self) -> int:
        answer = self.request.POST.get('answer', '')
        return '' if answer == '' else int(answer)

    ############################
    # Detail view info & title #
    ############################

    @property
    def info(self) -> dict:
        return {
            'menu': self.menu,
            'view_type': self.view_type,
            'type': f'{self.view_type}Detail',
        }

    @property
    def title(self) -> str:
        year = self.problem.psat.year
        exam2 = self.problem.psat.exam.name
        subject = self.problem.psat.subject.name
        number = self.problem.number
        return f"{year}년 '{exam2}' {subject} {number}번"

    ##################################
    # Detail view template variables #
    ##################################

    @property
    def num_range(self):
        if self.problem.psat.exam.abbr == '민경' or '칠급':
            return range(1, 26)
        else:
            return range(1, 41)

    ###################################################
    # Methods for getting page objective & navigation #
    ###################################################

    def get_detail_list(self, prob_data: any) -> list:
        organized_dict: dict = self.get_organized_dict(prob_data)
        return get_organized_list(organized_dict)

    def get_organized_dict(self, prob_data: any) -> dict:
        """ Return a dictionary sorted by exam. """
        organized_dict = {}
        for prob in prob_data:
            key = prob.psat.exam.id
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam2, subject = prob.psat.year, prob.psat.exam.name, prob.psat.subject.name
            list_item = {
                'exam_name': f"{year}년 '{exam2}' {subject}",
                'problem_number': prob.number,
                'problem_id': prob.id,
                'problem_url': self.get_reverse_lazy(prob.id)
            }
            organized_dict[key].append(list_item)
        return organized_dict

    def get_probs(self, prob_data=None, prob_list=None):
        prev_prob = next_prob = None
        page_list = list(prob_list)
        last_id = len(page_list) - 1
        q = page_list.index(self.problem_id)
        if q != 0:
            prev_prob = prob_data.filter(id=page_list[q - 1]).first()
        if q != last_id:
            next_prob = prob_data.filter(id=page_list[q + 1]).first()
        return prev_prob, next_prob

    ###############################
    # Page objective & navigation #
    ###############################

    @property
    def prob_data(self):
        filter_dict = {
            'problem': {'psat': self.problem.psat.id},
            'like': {
                'likes__user_id': self.user_id,
                'likes__is_liked': True,
            },
            'rate': {
                'rates__user_id': self.user_id,
                'rates__rating__gte': 0,
            },
            'solve': {
                'solves__user_id': self.user_id,
                'solves__is_correct__gte': 0,
            },
        }
        return PsatProblem.objects.filter(**filter_dict[self.view_type])

    @property
    def prev_prob(self):
        if self.request.method == 'GET':
            return self.get_probs(self.prob_data, self.prob_list)[0]

    @property
    def next_prob(self):
        if self.request.method == 'GET':
            return self.get_probs(self.prob_data, self.prob_list)[1]

    @property
    def list_data(self) -> list:
        return self.get_detail_list(self.prob_data)

    @property
    def my_tag(self) -> Tag | None:
        if self.request.user.is_authenticated:
            return Tag.objects.filter(user_id=self.user_id, problem=self.problem).first()
        return None

    @property
    def memo(self) -> Memo | None:
        if self.request.user.is_authenticated:
            return Memo.objects.filter(user_id=self.user_id, problem=self.problem).first()
        return None

    def get_reverse_lazy(self, problem_id):
        return reverse_lazy(self.url_name, kwargs={'view_type': self.view_type, 'problem_id': problem_id})

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


def get_organized_list(target: dict) -> list:
    """ Return organized list divided by 5 items. """
    organized_list = []
    for key, items in target.items():
        num_empty_instances = 5 - (len(items) % 5)
        if num_empty_instances < 5:
            items.extend([None] * num_empty_instances)
        for i in range(0, len(items), 5):
            row = items[i:i + 5]
            organized_list.extend(row)
    return organized_list


class PsatCustomInfo:
    request: any

    def get_custom_info(self, obj):
        user = self.request.user
        user_id = user.id
        problem_id = obj.id

        if user.is_authenticated:
            like_instance = Like.objects.filter(
                user_id=user_id, problem_id=problem_id).first()
            obj.liked_at = like_instance.timestamp if like_instance else None
            obj.is_liked = like_instance.is_liked if like_instance else None

            rate_instance = Rate.objects.filter(
                user_id=user_id, problem_id=problem_id).first()
            obj.rated_at = rate_instance.timestamp if rate_instance else None
            obj.rating = rate_instance.rating if rate_instance else None

            solve_instance = Solve.objects.filter(
                user_id=user_id, problem_id=problem_id).first()
            obj.solved_at = solve_instance.timestamp if solve_instance else None
            obj.answer = solve_instance.answer if solve_instance else None
            obj.is_correct = solve_instance.is_correct if solve_instance else None

            # obj.opened_at = source.opened_at if source else None
            # obj.opened_times = source.opened_times if source else 0
        return obj
