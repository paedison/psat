from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from searchview.views import SearchView
from vanilla import ListView

from common import constants
from ..forms import ProblemSearchForm
from ..models import Problem, Evaluation, ProblemData

psat_icon_set = constants.icon.PSAT_ICON_SET
like_none_icon = psat_icon_set['likeNone']
star_none_icon = psat_icon_set['starNone']

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET

exam_list = constants.psat.TOTAL['exam_list']
subject_list = constants.psat.TOTAL['subject_list']


def index(request):
    if request:
        return redirect('psat:base')


def get_evaluation_info(user, obj: Problem) -> Problem:
    problem_id = obj.prob_id
    source = None
    if user.is_authenticated:
        source = Evaluation.objects.filter(
            user=user, problem_id=problem_id).first()

    obj.opened_at = source.opened_at if source else None
    obj.opened_times = source.opened_times if source else 0

    obj.liked_at = source.liked_at if source else None
    obj.is_liked = source.is_liked if source else None
    obj.like_icon = source.like_icon() if source else like_none_icon

    obj.rated_at = source.rated_at if source else None
    obj.difficulty_rated = source.difficulty_rated if source else None
    obj.rate_icon = source.rate_icon() if source else star_none_icon

    obj.answered_at = source.answered_at if source else None
    obj.submitted_answered = source.submitted_answer if source else None
    obj.is_correct = source.is_correct if source else None
    obj.answer_icon = source.answer_icon() if source else ''

    return obj


class PSATListInfoMixIn:
    """
    Represent PSAT list information mixin.
    view_type(str): One of [ problem, like, rate, answer ]
    """
    kwargs: dict
    view_type: str
    title: str
    request: any
    pagination_url: str

    list_template = 'psat/problem_list.html'
    list_main_template = f'{list_template}#list_main'
    list_content_template = 'psat/problem_list_content.html'

    @property
    def category(self) -> int: return self.url['sub_code']

    @property
    def year(self) -> int | str:
        year = self.kwargs.get('year', '전체')
        return year if year == '전체' else int(year)

    @property
    def ex(self) -> str: return self.kwargs.get('ex', '전체')

    @property
    def exam2(self) -> str:
        return next((i['exam2'] for i in exam_list if i['ex'] == self.ex), '전체')

    @property
    def sub(self) -> str: return self.kwargs.get('sub', '전체')

    @property
    def subject(self) -> str:
        return next((i['subject'] for i in subject_list if i['sub'] == self.sub), '전체')

    @property
    def sub_code(self) -> int:
        return next((int(i['sub_code']) for i in subject_list if i['sub'] == self.sub), 0)

    @property
    def url(self) -> dict:
        return {
            'year': self.year,
            'ex': self.ex,
            'exam2': self.exam2,
            'sub': self.sub,
            'subject': self.subject,
            'sub_code': self.sub_code,
        }

    @property
    def url_name(self) -> str: return f'psat:{self.view_type}_list'

    def get_reverse_lazy(self, sub, opt=None) -> reverse_lazy:
        args = [opt, sub]
        args = [value for value in args if value is not None]
        _opt = '_opt' if opt else ''
        _sub = '_sub' if sub else ''
        return reverse_lazy(f'{self.url_name}{_opt}{_sub}', args=args)

    @property
    def menu_url(self) -> dict:
        """ Return the navigation tab URLs for LikeListView, RateListView, AnswerListView. """
        return {
            'eoneo': self.get_reverse_lazy('언어'),
            'jaryo': self.get_reverse_lazy('자료'),
            'sanghwang': self.get_reverse_lazy('상황'),
        }

    def get_filtered_queryset(self, field, value) -> Problem.objects:
        """ Get filtered queryset for like, rate, answer views. """
        problem_filter = Q(evaluation__user=self.request.user)
        if self.sub != '전체' and self.sub is not None:
            problem_filter &= Q(exam__sub=self.sub)
        if value is None:
            problem_filter &= Q(**{field+'__isnull': False})
        else:
            problem_filter &= Q(**{field: value})
        return Problem.objects.filter(problem_filter)

    @property
    def is_liked(self) -> str | None: return self.kwargs.get('is_liked')
    @property
    def star_count(self) -> str | None: return self.kwargs.get('star_count')
    @property
    def is_correct(self) -> str | None: return self.kwargs.get('is_correct')

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'menu_url': self.menu_url,
            'category': self.category,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.title,
            'sub': self.sub,
            'sub_code': self.sub_code,
            'pagination_url': self.pagination_url,
            'icon': menu_icon_set[self.view_type],
            'color': color_set[self.view_type],
            'is_liked': self.is_liked,
            'star_count': self.star_count,
            'is_correct': self.is_correct,
        }


class BaseListView(PSATListInfoMixIn, ListView):
    """ Represent PSAT base list view. """
    model = Problem
    context_object_name = 'problem'
    paginate_by = 10
    view_type: str

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_template_names(self) -> str:
        if self.request.method == 'GET':
            if self.request.htmx:
                return self.list_content_template
            else:
                return self.list_template
        elif self.request.method == 'POST':
            return self.list_main_template

    def get_elided_page_range(self, page_number):
        paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
        elided_page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=3, on_ends=1)
        return elided_page_range

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context['page_obj']
        for obj in page_obj:
            get_evaluation_info(self.request.user, obj)

        page_number = self.request.GET.get('page', 1)
        page_range = self.get_elided_page_range(page_number)

        context['url'] = self.url
        context['info'] = self.info
        context['page_range'] = page_range

        return context


class ProblemListView(BaseListView):
    view_type = 'problem'

    @property
    def title(self) -> str:
        title_parts = []
        if self.year != '전체' and self.year is not None:
            title_parts.append(f"{self.year}년")
        if self.ex != '전체' and self.ex is not None:
            title_parts.append(self.url['exam2'])
        if self.sub != '전체' and self.sub is not None:
            title_parts.append(self.url['subject'])
        title_parts.append('PSAT 기출문제')
        return ' '.join(title_parts)

    @property
    def pagination_url(self) -> reverse_lazy:
        return reverse_lazy(self.url_name, args=[self.year, self.ex, self.sub])

    @property
    def menu_url(self) -> dict:
        """ Return the navigation tab URLs for ProblemListView. """
        return {
            'eoneo': reverse_lazy(self.url_name, args=['전체', '전체', '언어']),
            'jaryo': reverse_lazy(self.url_name, args=['전체', '전체', '자료']),
            'sanghwang': reverse_lazy(self.url_name, args=['전체', '전체', '상황']),
        }

    def get_queryset(self) -> Problem:
        if self.request.htmx:
            problem_filter = Q()
            if self.year != '전체':
                problem_filter &= Q(exam__year=self.year)
            if self.ex != '전체':
                problem_filter &= Q(exam__ex=self.ex)
            if self.sub != '전체':
                problem_filter &= Q(exam__sub=self.sub)
            return Problem.objects.filter(problem_filter)
        else:
            return Problem.objects.all()


class LikeListView(BaseListView):
    view_type = 'like'
    title = 'PSAT 즐겨찾기'

    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.sub, self.is_liked)

    def get_queryset(self) -> Problem:
        return self.get_filtered_queryset('evaluation__is_liked', self.is_liked)


class RateListView(BaseListView):
    view_type = 'rate'
    title = 'PSAT 난이도'

    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.sub, self.star_count)

    def get_queryset(self) -> Problem:
        return self.get_filtered_queryset('evaluation__difficulty_rated', self.star_count)


class AnswerListView(BaseListView):
    view_type = 'answer'
    title = 'PSAT 정답확인'

    @property
    def pagination_url(self) -> reverse_lazy: return self.get_reverse_lazy(self.sub, self.is_correct)

    def get_queryset(self) -> Problem:
        return self.get_filtered_queryset('evaluation__is_correct', self.is_correct)


class ProblemSearchView(PSATListInfoMixIn, SearchView):
    model = ProblemData
    template_name = 'psat/problem_search.html'
    form_class = ProblemSearchForm
    paginate_by = 10
    first_display_all_list = False
    ordering = '-problem__exam__year'

    view_type = 'search'
    category = 0
    title = 'PSAT 검색'

    @property
    def pagination_url(self) -> reverse_lazy: return reverse_lazy('psat:search_content')

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.title,
            'pagination_url': self.pagination_url,
            'icon': menu_icon_set[self.view_type],
            'color': color_set[self.view_type],
        }

    def post(self, request, *args, **kwargs):
        try:
            request.session['_cleaned_data']
        except KeyError:
            super().get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data(object_list=None, **kwargs)
        page_obj = context['page_obj']
        paginator = context['paginator']
        page_range = paginator.get_elided_page_range(page_obj.number, on_ends=1)
        for obj in page_obj:
            get_evaluation_info(self.request.user, obj)

        context['url'] = self.url
        context['info'] = self.info
        context['page_range'] = page_range

        return context


class ProblemSearchContentView(ProblemSearchView):
    template_name = 'psat/problem_search.html#content'


problem = ProblemListView.as_view()
like = LikeListView.as_view()
rate = RateListView.as_view()
answer = AnswerListView.as_view()
search = ProblemSearchView.as_view()
search_content = ProblemSearchContentView.as_view()
