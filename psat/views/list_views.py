# Django Core Import
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

# Third Party Library Import
from searchview import views as search_view
from vanilla import ListView

# Custom App Import
from common.constants import icon, color, psat
from log.views import CreateLogMixIn
from ..forms import ProblemSearchForm
from ..models import Problem, Evaluation, ProblemData


def index(request):
    if request:
        return redirect('psat:base')


class PsatListInfoMixIn:
    """
    Represent PSAT list information mixin.
    view_type(str): One of [ problem, like, rate, answer ]
    """
    kwargs: dict
    app_name = 'psat'
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

    @property
    def url(self) -> dict:
        """
        Return URL dictionary containing year, ex, exam2, sub, subject, sub_code.
        """
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
        """ Return option dictionary. """
        return {
            'problem': None,
            'like': self.kwargs.get('is_liked'),
            'rate': self.kwargs.get('star_count'),
            'answer': self.kwargs.get('is_correct'),
            'search': None,
        }

    @property
    def title(self) -> str:
        """ Return title of the list. """
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
        """ Return URL of reverse_lazy style. """
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        opt = self.option[self.view_type]
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
                return reverse_lazy(f'psat:{self.view_type}_list{_opt}{_sub}', args=args)
            else:
                return reverse_lazy(f'psat:{self.view_type}_list')

    @property
    def category(self): return self.url['sub_code']

    @property
    def info(self) -> dict:
        """ Return information dictionary of the list. """
        return {
            'app_name': self.app_name,
            'menu': '',
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


class EvaluationInfoMixIn:
    """ Represent Evaluation model information mixin. """
    request: WSGIRequest

    def get_evaluation_info(self, obj) -> object:
        """ Get Evaluation information. """
        user = self.request.user
        problem_id = obj.prob_id()
        source = None
        if user.is_authenticated:
            source = Evaluation.objects.filter(user=user, problem_id=problem_id).first()

        obj.opened_at = source.opened_at if source else None
        obj.opened_times = source.opened_times if source else 0

        obj.liked_at = source.liked_at if source else None
        obj.is_liked = source.is_liked if source else None
        obj.like_icon = source.like_icon() if source else icon.PSAT_ICON_SET['likeNone']

        obj.rated_at = source.rated_at if source else None
        obj.difficulty_rated = source.difficulty_rated if source else None
        obj.rate_icon = source.rate_icon() if source else icon.PSAT_ICON_SET['starNone']

        obj.answered_at = source.answered_at if source else None
        obj.submitted_answered = source.submitted_answer if source else None
        obj.is_correct = source.is_correct if source else None
        obj.answer_icon = source.answer_icon() if source else ''

        return obj


class QuerysetFieldMixIn:
    """ Represent queryset field. """
    view_type: str
    field_dict = {
        'problem': ['', ''],
        'like': ['evaluation__is_liked__gte', 'evaluation__is_liked',
                 '-evaluation__liked_at'],
        'rate': ['evaluation__difficulty_rated__gte', 'evaluation__difficulty_rated',
                 '-evaluation__rated_at'],
        'answer': ['evaluation__is_correct__gte', 'evaluation__is_correct',
                   '-evaluation__rated_at'],
        'search': ['', ''],
    }

    @property
    def queryset_field(self) -> list:
        """ Return queryset field for 'get_queryset'. """
        return self.field_dict[self.view_type]


class BaseListView(PsatListInfoMixIn, EvaluationInfoMixIn, ListView):
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
            self.get_evaluation_info(obj)

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
            return 'psat/problem_list.html'
        else:
            return 'psat/problem_list_content.html'


class ProblemListView(BaseListView):
    view_type = 'problem'

    def get_queryset(self) -> object:
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        problem_filter = Q()

        if year != '전체':
            problem_filter &= Q(exam__year=year)
        if ex != '전체':
            problem_filter &= Q(exam__ex=ex)
        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)

        return Problem.objects.filter(problem_filter)


class LikeListView(BaseListView):
    view_type = 'like'

    def get_queryset(self) -> object:
        is_liked = self.kwargs.get('is_liked')
        sub = self.url['sub']
        problem_filter = Q(evaluation__user=self.request.user)

        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)
        if is_liked is None:
            problem_filter &= Q(evaluation__is_liked__gte=0)
        else:
            problem_filter &= Q(evaluation__is_liked=is_liked)

        return Problem.objects.filter(problem_filter)


class RateListView(BaseListView):
    view_type = 'rate'

    def get_queryset(self) -> object:
        star_count = self.kwargs.get('star_count')
        sub = self.url['sub']
        problem_filter = Q(evaluation__user=self.request.user)

        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)
        if star_count is None:
            problem_filter &= Q(evaluation__difficulty_rated__gte=0)
        else:
            problem_filter &= Q(evaluation__difficulty_rated=star_count)

        return Problem.objects.filter(problem_filter)


class AnswerListView(BaseListView):
    view_type = 'answer'

    def get_queryset(self) -> object:
        is_correct = self.kwargs.get('is_correct')
        sub = self.url['sub']
        problem_filter = Q(evaluation__user=self.request.user)

        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)
        if is_correct is None:
            problem_filter &= Q(evaluation__is_correct__gte=0)
        else:
            problem_filter &= Q(evaluation__is_correct=is_correct)

        return Problem.objects.filter(problem_filter)


class ProblemSearchListView(CreateLogMixIn, PsatListInfoMixIn, EvaluationInfoMixIn,
                            search_view.SearchView):
    model = ProblemData
    template_name = 'psat/problem_list_content.html'
    form_class = ProblemSearchForm
    paginate_by = 10
    first_display_all_list = False
    ordering = '-problem__exam__year'
    view_type = 'search'

    @property
    def log_title(self) -> str:
        """ Return menu name of the list. """
        return self.title_dict[self.view_type]

    @property
    def pagination_url(self) -> reverse_lazy:
        return reverse_lazy('psat:search')

    @property
    def info(self) -> dict:
        """ Return information dictionary of the main list. """
        return {
            'app_name': self.app_name,
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': self.log_title,
            'pagination_url': self.pagination_url,
            'target_id': f'{self.view_type}ListContent',
            'icon': icon.MENU_ICON_SET[self.view_type],
            'color': color.COLOR_SET[self.view_type],
        }

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context)
        self.create_log_for_list(page_obj=context['page_obj'])
        return html

    def post(self, request, *args, **kwargs) -> HttpResponse:
        super().post(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context).content.decode('utf-8')
        self.create_log_for_list(page_obj=context['page_obj'])
        return HttpResponse(html)

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data()
        page_obj = context['page_obj']
        paginator = context['paginator']
        page_range = paginator.get_elided_page_range(page_obj.number, on_ends=1)
        for obj in page_obj:
            self.get_evaluation_info(obj)
        context['url'] = self.url
        context['info'] = self.info
        context['page_range'] = page_range
        return context
