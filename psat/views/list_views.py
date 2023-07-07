# Django Core Import
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView

# Custom App Import
from common.constants.icon import *
from common.constants.psat import *
from log.views import create_log
from psat.models import Exam, Problem
from psat.views.common_views import get_evaluation_info

exam = Exam.objects
problem = Problem.objects

field_dict = {
    'problem': [],
    'like': [
        'evaluation__is_liked__gte',
        'evaluation__is_liked',
    ],
    'rate': [
        'evaluation__difficulty_rated__gte',
        'evaluation__difficulty_rated'
    ],
    'answer': [
        'evaluation__is_correct__gte',
        'evaluation__is_correct',
    ],
}

title_dict = {
    'problem': '',
    'like': 'PSAT 즐겨찾기',
    'rate': 'PSAT 난이도',
    'answer': 'PSAT 정답확인',
}


def index(request):
    return redirect('psat:base')


def get_url_info(**kwargs):
    year = kwargs.get('year', '전체')
    if year != '전체':
        year = int(year)
    ex = kwargs.get('ex', '전체')
    exam2 = next((instance['exam2'] for instance in TOTAL['exam_list'] if instance['ex'] == ex), None)
    sub = kwargs.get('sub', '전체')
    subject = next((instance['subject'] for instance in TOTAL['subject_list'] if instance['sub'] == sub), None)
    sub_code = next((instance['sub_code'] for instance in TOTAL['subject_list'] if instance['sub'] == sub), '')
    url = {
        'year': year,
        'ex': ex,
        'exam2': exam2,
        'sub': sub,
        'subject': subject,
        'sub_code': sub_code,
    }
    return url


def get_view_option(**kwargs):
    is_liked = kwargs.get('is_liked')
    star_count = kwargs.get('star_count')
    is_correct = kwargs.get('is_correct')
    option = {
        'problem': None,
        'like': is_liked,
        'rate': star_count,
        'answer': is_correct,
    }
    return option


def get_info_title(view_category, url):
    title = title_dict[view_category]
    title_parts = []
    if url['year'] != '전체':
        title_parts.append(f"{url['year']}년")
    if url['ex'] != '전체':
        title_parts.append(url['exam2'])
    if url['sub'] != '전체':
        title_parts.append(url['subject'])
    title_parts.append('PSAT 기출문제')
    if view_category == 'problem':
        title = ' '.join(title_parts)
    return title


def get_pagination_url(view_category, url, option):
    year, ex, sub = url['year'], url['ex'], url['sub']
    if view_category == 'problem':
        pagination_url = reverse_lazy(f'psat:{view_category}_list', args=[year, ex, sub])
    else:
        sub = sub if sub != '전체' else None
        args = [option[view_category], sub]
        args = [value for value in args if value is not None]
        _opt = '_opt' if option[view_category] else ''
        _sub = '_sub' if sub else ''
        if args:
            pagination_url = reverse_lazy(f'psat:{view_category}_list{_opt}{_sub}', args=args)
        else:
            pagination_url = reverse_lazy(f'psat:{view_category}_list')
    return pagination_url


def get_class_view_info(view_category, url, option):
    title = get_info_title(view_category, url)
    pagination_url = get_pagination_url(view_category, url, option)
    return {
        'category': view_category,
        'type': f'{view_category}List',
        'sub': url['sub'],
        'sub_code': url['sub_code'],
        'title': title,
        'pagination_url': pagination_url,
        'target_id': f'{view_category}ListContent{url["sub_code"]}',
        'icon': ICON_LIST[view_category],
        'color': COLOR_LIST[view_category],
        'is_liked': option['like'],
        'star_count': option['rate'],
        'is_correct': option['answer'],
    }


def get_main_view_info(view_category):
    main_title_dict = title_dict.copy()
    main_title_dict['problem'] = 'PSAT 기출문제'
    title = main_title_dict[view_category]
    main_view_info = {
        'category': view_category,
        'type': f'{view_category}List',
        'title': title,
        'target_id': f'{view_category}List',
        'icon': ICON_LIST[view_category],
        'color': COLOR_LIST[view_category],
    }
    return main_view_info


def get_list_queryset(view_category, request, url, option):
    user = request.user
    field = field_dict[view_category]
    opt = option[view_category]

    year, ex, sub = url['year'], url['ex'], url['sub']
    problem_filter = Q()
    if view_category == 'problem':
        if year != '전체':
            problem_filter &= Q(exam__year=year)
        if ex != '전체':
            problem_filter &= Q(exam__ex=ex)
        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)
    else:
        problem_filter = Q(evaluation__user=user)
        if sub != '전체':
            problem_filter &= Q(exam__sub=sub)
        lookup_expr = field[0] if opt is None else field[1]
        value = 0 if opt is None else opt
        problem_filter &= Q(**{lookup_expr: value})
    return problem.filter(problem_filter)


class BaseListView(ListView):
    model = Problem
    template_name = 'psat/problem_list.html'
    content_template = 'psat/problem_list_content.html'
    context_object_name = 'problem'
    paginate_by = 10
    info = url = option = {}
    object_list = None

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        html = render(request, self.content_template, context)
        create_log(self.request, self.info)
        return html

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.content_template, context).content.decode('utf-8')
        create_log(self.request, self.info)
        return HttpResponse(html)

    def update_context(self, context):
        page_obj = context['page_obj']
        paginator = context['paginator']
        for obj in page_obj:
            get_evaluation_info(self.request, obj)
        context['page_range'] = paginator.get_elided_page_range(page_obj.number, on_ends=1)
        context['info'] = self.info
        context['info']['page'] = page_obj.number


class ProblemListView(BaseListView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.url = get_url_info(**kwargs)
        self.option = get_view_option(**kwargs)
        self.info = get_class_view_info('problem', self.url, self.option)

    def get_queryset(self):
        return get_list_queryset('problem', self.request, self.url, self.option)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.url
        self.update_context(context)
        return context


class LikeListView(BaseListView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.url = get_url_info(**kwargs)
        self.option = get_view_option(**kwargs)
        self.info = get_class_view_info('like', self.url, self.option)

    def get_queryset(self):
        return get_list_queryset('like', self.request, self.url, self.option)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        self.update_context(context)
        return context


class RateListView(BaseListView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.url = get_url_info(**kwargs)
        self.option = get_view_option(**kwargs)
        self.info = get_class_view_info('rate', self.url, self.option)

    def get_queryset(self):
        return get_list_queryset('rate', self.request, self.url, self.option)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        self.update_context(context)
        return context


class AnswerListView(BaseListView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.url = get_url_info(**kwargs)
        self.option = get_view_option(**kwargs)
        self.info = get_class_view_info('answer', self.url, self.option)

    def get_queryset(self):
        return get_list_queryset('answer', self.request, self.url, self.option)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        self.update_context(context)
        return context


class MainView(View):
    template_name = 'psat/problem_list.html'
    main_list_view = None
    info = {}

    def get(self, request):
        list_view = self.main_list_view.as_view()
        subject_all = list_view(request).content.decode('utf-8')
        subject_eoneo = list_view(request, sub='언어').content.decode('utf-8')
        subject_jaryo = list_view(request, sub='자료').content.decode('utf-8')
        subject_sanghwang = list_view(request, sub='상황').content.decode('utf-8')
        context = {
            'info': self.info,
            'total': TOTAL,
            'subject_all': subject_all,
            'subject_eoneo': subject_eoneo,
            'subject_jaryo': subject_jaryo,
            'subject_sanghwang': subject_sanghwang,
        }
        return render(request, self.template_name, context)


class MainProblemView(MainView):
    main_list_view = ProblemListView
    info = get_main_view_info('problem')


class MainLikeView(MainView):
    main_list_view = LikeListView
    info = get_main_view_info('like')


class MainRateView(MainView):
    main_list_view = RateListView
    info = get_main_view_info('rate')


class MainAnswerView(MainView):
    main_list_view = AnswerListView
    info = get_main_view_info('answer')
