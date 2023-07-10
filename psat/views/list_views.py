# Django Core Import

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from common.constants import icon, color, psat
from log.views import CreateLogMixIn
from ..models import Problem, Evaluation


def index(request):
    if request:
        return redirect('psat:base')


class PsatListInfoMixIn:
    """
    Represent PSAT list information mixin.
    category(str): One of [ problem, like, rate, answer ]
    """
    kwargs: dict
    app_name = 'psat'
    category: str
    title_dict = {
        'problem': '',
        'like': 'PSAT 즐겨찾기',
        'rate': 'PSAT 난이도',
        'answer': 'PSAT 정답확인',
    }

    @property
    def url(self) -> dict:
        """ Return URL dictionary containing year, ex, exam2, sub, subject, sub_code. """
        year = self.kwargs.get('year', '전체')
        if year != '전체':
            year = int(year)
        ex = self.kwargs.get('ex', '전체')
        exam2 = next((i['exam2'] for i in psat.TOTAL['exam_list'] if i['ex'] == ex), None)
        sub = self.kwargs.get('sub', '전체')
        subject = next((i['subject'] for i in psat.TOTAL['subject_list'] if i['sub'] == sub), None)
        sub_code = next((i['sub_code'] for i in psat.TOTAL['subject_list'] if i['sub'] == sub), '')
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
        }

    @property
    def title(self) -> str:
        """ Return title of the list. """
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        exam2, subject = self.url['exam2'], self.url['subject']
        title = self.title_dict[self.category]
        title_parts = []
        if year != '전체':
            title_parts.append(f"{year}년")
        if ex != '전체':
            title_parts.append(exam2)
        if sub != '전체':
            title_parts.append(subject)
        title_parts.append('PSAT 기출문제')
        if self.category == 'problem':
            title = ' '.join(title_parts)
        return title

    @property
    def pagination_url(self) -> reverse_lazy:
        """ Return URL of reverse_lazy style. """
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        opt = self.option[self.category]
        if self.category == 'problem':
            return reverse_lazy(f'psat:{self.category}_list', args=[year, ex, sub])
        else:
            sub = sub if sub != '전체' else None
            args = [opt, sub]
            args = [value for value in args if value is not None]
            _opt = '_opt' if opt else ''
            _sub = '_sub' if sub else ''
            if args:
                return reverse_lazy(f'psat:{self.category}_list{_opt}{_sub}', args=args)
            else:
                return reverse_lazy(f'psat:{self.category}_list')

    @property
    def info(self) -> dict:
        """ Return information dictionary of the list. """
        return {
            'app_name': self.app_name,
            'menu': '',
            'category': self.category,
            'type': f'{self.category}List',
            'title': self.title,
            'sub': self.url['sub'],
            'sub_code': self.url['sub_code'],
            'pagination_url': self.pagination_url,
            'target_id': f'{self.category}ListContent{self.url["sub_code"]}',
            'icon': icon.ICON_LIST[self.category],
            'color': color.COLOR_LIST[self.category],
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
        if user.is_authenticated:
            try:
                source = Evaluation.objects.get(user=user, problem_id=obj.prob_id())
                obj.like_icon = source.like_icon()
                obj.rate_icon = source.rate_icon()
                obj.answer_icon = source.answer_icon()

                obj.opened_at = source.opened_at
                obj.opened_times = source.opened_times

                obj.liked_at = source.liked_at
                obj.is_liked = source.is_liked
                obj.like_icon = source.like_icon()

                obj.rated_at = source.rated_at
                obj.difficulty_rated = source.difficulty_rated
                obj.rate_icon = source.rate_icon()

                obj.answered_at = source.answered_at
                obj.submitted_answered = source.submitted_answer
                obj.is_correct = source.is_correct
                obj.answer_icon = source.answer_icon()

            except Evaluation.DoesNotExist:
                obj.opened_at = None
                obj.opened_times = 0

                obj.liked_at = None
                obj.is_liked = None
                obj.like_icon = icon.EMPTY_HEART_ICON

                obj.rated_at = None
                obj.difficulty_rated = None
                obj.rate_icon = icon.STAR0_ICON

                obj.answered_at = None
                obj.submitted_answered = None
                obj.is_correct = None
                obj.answer_icon = ''
        return obj


class QuerysetFieldMixIn:
    """ Represent queryset field. """
    category: str
    field_dict = {
        'problem': ['', ''],
        'like': ['evaluation__is_liked__gte', 'evaluation__is_liked', '-evaluation__liked_at'],
        'rate': ['evaluation__difficulty_rated__gte', 'evaluation__difficulty_rated', '-evaluation__rated_at'],
        'answer': ['evaluation__is_correct__gte', 'evaluation__is_correct', '-evaluation__rated_at'],
    }

    @property
    def queryset_field(self) -> list:
        """ Return queryset field for 'get_queryset'. """
        return self.field_dict[self.category]


class BaseListView(
    PsatListInfoMixIn,
    EvaluationInfoMixIn,
    QuerysetFieldMixIn,
    CreateLogMixIn,
    generic.ListView,
):
    """ Represent PSAT base list view. """
    model = Problem
    template_name = 'psat/problem_list.html'
    content_template = 'psat/problem_list_content.html'
    context_object_name = 'problem'
    paginate_by = 10
    category: str

    @property
    def object_list(self) -> object:
        return self.get_queryset()

    def get(self, request, *args, **kwargs) -> render:
        context = self.get_context_data(**kwargs)
        html = render(request, self.content_template, context)
        self.create_log_for_list(page_obj=context['page_obj'])
        return html

    def post(self, request, *args, **kwargs) -> HttpResponse:
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.content_template, context).content.decode('utf-8')
        self.create_log_for_list(page_obj=context['page_obj'])
        return HttpResponse(html)

    def get_queryset(self) -> object:
        field = self.queryset_field
        opt = self.option[self.category]
        year, ex, sub = self.url['year'], self.url['ex'], self.url['sub']
        problem_filter = Q()
        if self.category == 'problem':
            if year != '전체':
                problem_filter &= Q(exam__year=year)
            if ex != '전체':
                problem_filter &= Q(exam__ex=ex)
            if sub != '전체':
                problem_filter &= Q(exam__sub=sub)
        else:
            problem_filter = Q(evaluation__user=self.request.user)
            if sub != '전체':
                problem_filter &= Q(exam__sub=sub)
            lookup_expr = field[0] if opt is None else field[1]
            value = 0 if opt is None else opt
            problem_filter &= Q(**{lookup_expr: value})
        return Problem.objects.filter(problem_filter)

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        """Get the context for this view."""
        queryset = self.object_list
        page_size = self.get_paginate_by(queryset)
        paginator, page_obj, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
        for obj in page_obj:
            self.get_evaluation_info(obj)
        return {
            'view': self,
            'url': self.url,
            'info': self.info,
            'page_obj': page_obj,
            'page_range': paginator.get_elided_page_range(page_obj.number, on_ends=1),
        }


class ProblemListView(BaseListView):
    category = 'problem'


class LikeListView(BaseListView):
    category = 'like'


class RateListView(BaseListView):
    category = 'rate'


class AnswerListView(BaseListView):
    category = 'answer'


class ListMainView(PsatListInfoMixIn, generic.View):
    """ Represent PSAT list main view. """
    template_name = 'psat/problem_list.html'
    main_list_view = None

    @property
    def title(self) -> str:
        """ Return menu name of the list. """
        title_dict = self.title_dict.copy()
        title_dict['problem'] = 'PSAT 기출문제'
        return title_dict[self.category]

    @property
    def info(self) -> dict:
        """ Return information dictionary of the main list. """
        return {
            'app_name': self.app_name,
            'menu': self.category,
            'category': self.category,
            'type': f'{self.category}List',
            'title': self.title,
            'target_id': f'{self.category}List',
            'icon': icon.ICON_LIST[self.category],
            'color': color.COLOR_LIST[self.category],
        }

    def get(self, request) -> render:
        list_view = self.main_list_view.as_view()
        all_ = list_view(request).content.decode('utf-8')
        eoneo = list_view(request, sub='언어').content.decode('utf-8')
        jaryo = list_view(request, sub='자료').content.decode('utf-8')
        sanghwang = list_view(request, sub='상황').content.decode('utf-8')
        context = {
            'info': self.info,
            'total': psat.TOTAL,
            'all': all_,
            'eoneo': eoneo,
            'jaryo': jaryo,
            'sanghwang': sanghwang,
        }
        return render(request, self.template_name, context)


class ProblemListMainView(ListMainView):
    main_list_view = ProblemListView
    category = 'problem'


class LikeListMainView(ListMainView):
    main_list_view = LikeListView
    category = 'like'


class RateListMainView(ListMainView):
    main_list_view = RateListView
    category = 'rate'


class AnswerListMainView(ListMainView):
    main_list_view = AnswerListView
    category = 'answer'
