# Django Core Import
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy

# Third Party Library Import
from searchview import views as search_view
from vanilla import ListView

# Custom App Import
from common.constants import icon, color, psat
from ..forms import ProblemSearchForm
from ..models import Problem, Evaluation, ProblemData


def index(request):
    if request:
        return redirect('psat:base')


def get_evaluation_info(user, obj) -> object:
    problem_id = obj.prob_id()
    like_none_icon = icon.PSAT_ICON_SET['likeNone']
    star_none_icon = icon.PSAT_ICON_SET['starNone']

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
    object: any
    object_list: any

    title_dict = {
        'problem': '',
        'like': 'PSAT 즐겨찾기',
        'rate': 'PSAT 난이도',
        'answer': 'PSAT 정답확인',
        'search': 'PSAT 검색'
    }
    list_template = 'psat/problem_list.html'
    list_content_template = 'psat/problem_list_content.html'

    @property
    def url(self) -> dict:
        year = self.kwargs.get('year')
        year = year if year == '전체' or year is None else int(year)
        ex = self.kwargs.get('ex')
        exam2 = next((i['exam2'] for i in psat.TOTAL['exam_list']
                      if i['ex'] == ex), None)
        sub = self.kwargs.get('sub')
        subject = next((i['subject'] for i in psat.TOTAL['subject_list']
                        if i['sub'] == sub), None)
        sub_code = next((i['sub_code'] for i in psat.TOTAL['subject_list']
                         if i['sub'] == sub), None)
        return {
            'year': year,
            'ex': ex,
            'exam2': exam2,
            'sub': sub,
            'subject': subject,
            'sub_code': sub_code,
        }

    @property
    def option(self) -> dict:
        return {
            'problem': None,
            'like': self.kwargs.get('is_liked'),
            'rate': self.kwargs.get('star_count'),
            'answer': self.kwargs.get('is_correct'),
            'search': None,
        }

    @property
    def title(self) -> str:
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        exam2, subject = self.url['exam2'], self.url['subject']
        title = self.title_dict[self.view_type]
        title_parts = []

        if year != '전체' and year is not None:
            title_parts.append(f"{year}년")
        if ex != '전체' and ex is not None:
            title_parts.append(exam2)
        if sub != '전체' and sub is not None:
            title_parts.append(subject)
        title_parts.append('PSAT 기출문제')
        if self.view_type == 'problem' and title_parts is not None:
            title = ' '.join(title_parts)

        return title

    @property
    def pagination_url(self) -> reverse_lazy:
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        opt = self.option[self.view_type]
        url_pattern = f'psat:{self.view_type}_list'
        if self.view_type == 'problem':
            if sub is None:
                return None
            return reverse_lazy(f'psat:{self.view_type}_list', args=[year, ex, sub])
        else:
            sub = sub if sub != '전체' else None
            args = [opt, sub]
            args = [value for value in args if value is not None]
            _opt = '_opt' if opt else ''
            _sub = '_sub' if sub else ''
            if args:
                return reverse_lazy(f'{url_pattern}{_opt}{_sub}', args=args)
            else:
                return reverse_lazy(url_pattern)

    @property
    def category(self) -> int: return self.url['sub_code']

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'category': self.category,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.title,
            'sub': self.url['sub'],
            'sub_code': self.url['sub_code'],
            'pagination_url': self.pagination_url,
            'target_id': f'{self.view_type}ListContent{self.url["sub_code"]}',
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
            'is_liked': self.option['like'],
            'star_count': self.option['rate'],
            'is_correct': self.option['answer'],
        }


class BaseListView(PSATListInfoMixIn, ListView):
    """ Represent PSAT base list view. """
    model = Problem
    context_object_name = 'problem'
    paginate_by = 10
    view_type: str

    def get_elided_page_range(self, page_number):
        paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
        elided_page_range = paginator.get_elided_page_range(
            number=page_number, on_each_side=3, on_ends=1)
        return elided_page_range

    def get(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset(), self.paginate_by)
        self.object_list = page.object_list
        for obj in page:
            get_evaluation_info(self.request.user, obj)

        page_number = self.request.GET.get('page', 1)
        page_range = self.get_elided_page_range(page_number)

        context = self.get_context_data(
            url=self.url,
            info=self.info,
            page_obj=page,
            is_paginated=page.has_other_pages(),
            paginator=page.paginator,
            page_range=page_range,
        )

        return self.render_to_response(context)

    def get_template_names(self):
        if self.url['sub'] is None:
            return self.list_template
        else:
            return self.list_content_template

    def get_queryset(self) -> Problem.objects:
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        field = value = None
        problem_filter = Q()

        if self.view_type == 'problem':
            if year != '전체':
                problem_filter &= Q(exam__year=year)
            if ex != '전체':
                problem_filter &= Q(exam__ex=ex)
            if sub != '전체':
                problem_filter &= Q(exam__sub=sub)
        else:
            problem_filter = Q(evaluation__user=self.request.user)
            if sub != '전체' and sub is not None:
                problem_filter &= Q(exam__sub=sub)
            if self.view_type == 'like':
                field = 'evaluation__is_liked'
                value = self.kwargs.get('is_liked')
            elif self.view_type == 'rate':
                field = 'evaluation__difficulty_rated'
                value = self.kwargs.get('star_count')
            elif self.view_type == 'answer':
                field = 'evaluation__is_correct'
                value = self.kwargs.get('is_correct')

            if value is None:
                problem_filter &= Q(**{field+'__isnull': False})
            else:
                problem_filter &= Q(**{field: value})
        return Problem.objects.filter(problem_filter)


class ProblemListView(BaseListView):
    view_type = 'problem'


class LikeListView(BaseListView):
    view_type = 'like'


class RateListView(BaseListView):
    view_type = 'rate'


class AnswerListView(BaseListView):
    view_type = 'answer'


class ProblemSearchView(PSATListInfoMixIn, search_view.SearchView):
    model = ProblemData
    template_name = 'psat/problem_search.html'
    form_class = ProblemSearchForm
    paginate_by = 10
    first_display_all_list = False
    ordering = '-problem__exam__year'
    view_type = 'search'
    category = 0

    @property
    def log_title(self) -> str: return self.title_dict[self.view_type]

    @property
    def pagination_url(self) -> reverse_lazy:
        return reverse_lazy('psat:search_content')

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.log_title,
            'pagination_url': self.pagination_url,
            'target_id': f'{self.view_type}ListContent',
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
        }

    def post(self, request, *args, **kwargs):
        try:
            request.session['_cleaned_data']
        except KeyError:
            super().get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data()
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
    template_name = 'psat/problem_search.html#search_content'


problem_list_view = ProblemListView.as_view()
like_list_view = LikeListView.as_view()
rate_list_view = RateListView.as_view()
answer_list_view = AnswerListView.as_view()
problem_search_view = ProblemSearchView.as_view()
problem_search_content_view = ProblemSearchContentView.as_view()
