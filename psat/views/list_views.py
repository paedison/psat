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
from psat.models import Exam, Problem
from psat.views.common_views import get_evaluation_info

exam = Exam.objects
problem = Problem.objects


def index(request):
    return redirect('psat:base')


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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_list_view = ProblemListView

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'problem',
            'type': 'problemList',
            'title': 'PSAT 기출문제',
            'target_id': 'problemList',
            'icon': MENU_PROBLEM_ICON,
            'color': 'primary',
        }


class MainLikeView(MainView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_list_view = LikeListView

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'like',
            'type': 'likeList',
            'title': 'PSAT 즐겨찾기',
            'target_id': 'likeList',
            'icon': MENU_LIKE_ICON,
            'color': 'danger',
        }


class MainRateView(MainView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_list_view = RateListView

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'rate',
            'type': 'rateList',
            'title': 'PSAT 난이도',
            'target_id': 'rateList',
            'icon': MENU_RATE_ICON,
            'color': 'warning',
        }


class MainAnswerView(MainView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_list_view = AnswerListView

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.info = {
            'category': 'answer',
            'type': 'answerList',
            'title': 'PSAT 정답확인',
            'target_id': 'answerList',
            'icon': MENU_ANSWER_ICON,
            'color': 'success',
        }


class BaseListView(ListView):
    model = Problem
    template_name = 'psat/problem_list.html'
    content_template = 'psat/problem_list_content.html'
    context_object_name = 'problem'
    paginate_by = 10
    info = {}

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        from log.views import create_request_log
        extra = f"({self.sub})"
        create_request_log(self.request, self.info, extra)

        # return self.render_to_response(context)
        html = render(request, self.content_template, context)
        return html

    def post(self, request, *args, **kwargs):
        page = self.kwargs['page'] = request.POST.get('page', '1')
        context = self.get_context_data(**kwargs)
        html = render(request, self.content_template, context).content.decode('utf-8')

        from log.views import create_request_log
        extra = f"({self.sub} p.{page})"
        create_request_log(self.request, self.info, extra)

        return HttpResponse(html)

    def update_context(self, context):
        page_obj = context['page_obj']
        paginator = context['paginator']
        for obj in page_obj:
            obj = get_evaluation_info(self.request, obj)
        context['page_range'] = paginator.get_elided_page_range(page_obj.number, on_ends=1)
        context['info'] = self.info


class ProblemListView(BaseListView):
    year = ex = exam2 = sub = subject = '전체'
    sub_code = None
    main_title = exam_data = problem_data = year_list = exam_list = subject_list = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.year = kwargs.get('year', '전체')
        if self.year != '전체':
            self.year = int(self.year)
        self.ex = kwargs.get('ex', '전체')
        self.exam2 = next((instance['exam2'] for instance in TOTAL['exam_list'] if instance['ex'] == self.ex), None)
        self.sub = kwargs.get('sub', '전체')
        self.subject = next((instance['subject'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), None)
        self.sub_code = next((instance['sub_code'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), '')

        self.main_title = self.get_main_title()
        self.exam_data = self.get_exam_data()
        self.problem_data = self.get_problem_data()
        self.year_list, self.exam_list, self.subject_list = self.get_year_exam_subject_list()
        pagination_url = reverse_lazy('psat:problem_list', args=[self.year, self.ex, self.sub])

        self.info ={
            'category': 'problem',
            'type': 'problemList',
            'sub': self.sub,
            'title': self.main_title,
            'pagination_url': pagination_url,
            'target_id': f'problemListContent{self.sub_code}',
            'icon': MENU_PROBLEM_ICON,
            'color': 'primary',
        }

    def get_main_title(self):
        main_title = ''
        if self.year != '전체':
            main_title += f"{self.year}년 "
        if self.ex != '전체':
            main_title += f"'{self.exam2}' "
        if self.sub != '전체':
            main_title += f"{self.subject} "
        main_title += 'PSAT 기출문제'
        return main_title

    def get_exam_data(self):
        exam_filter = Q()
        if self.year != '전체':
            exam_filter &= Q(year=self.year)
        if self.ex != '전체':
            exam_filter &= Q(ex=self.ex)
        if self.sub != '전체':
            exam_filter &= Q(sub=self.sub)
        return exam.filter(exam_filter)

    def get_problem_data(self):
        problem_filter = Q()
        if self.year != '전체':
            problem_filter &= Q(exam__year=self.year)
        if self.ex != '전체':
            problem_filter &= Q(exam__ex=self.ex)
        if self.sub != '전체':
            problem_filter &= Q(exam__sub=self.sub)
        return problem.filter(problem_filter)

    def get_year_exam_subject_list(self):
        year_list = self.exam_data.values_list('year', flat=True).distinct()
        exam_list = self.exam_data.values('ex', 'exam2').distinct()
        subject_list = self.exam_data.values('sub', 'subject').distinct()
        return year_list, exam_list, subject_list

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=self.problem_data, **kwargs)
        url = {
            'year': self.year,
            'ex': self.ex,
            'exam2': self.exam2,
            'sub': self.sub,
            'subject': self.subject,
            'year_list': self.year_list,
            'exam_list': self.exam_list,
            'subject_list': self.subject_list,
        }
        context['url'] = url
        self.update_context(context)

        return context


class LikeListView(BaseListView):
    is_liked = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.sub = kwargs.get('sub', '전체')
        self.subject = next((instance['subject'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), None)
        self.sub_code = next((instance['sub_code'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), '')

        self.is_liked = kwargs.get('is_liked')
        if self.is_liked is None:
            pagination_url = reverse_lazy('psat:like_list')
        else:
            pagination_url = reverse_lazy('psat:like_list_opt', args=[self.is_liked])

        self.info = {
            'category': 'like',
            'type': 'likeList',
            'sub': self.sub,
            'sub_code': self.sub_code,
            'title': 'PSAT 즐겨찾기',
            'pagination_url': pagination_url,
            'target_id': f'likeListContent{self.sub_code}',
            'icon': MENU_LIKE_ICON,
            'color': 'danger',
            'is_liked': self.is_liked,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        if self.sub == '전체':
            queryset = problem.filter(evaluation__user=user, evaluation__is_liked__gte=0)
            if self.is_liked is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__is_liked=self.is_liked)
        else:
            queryset = problem.filter(evaluation__user=user, evaluation__is_liked__gte=0, exam__sub=self.sub)
            if self.is_liked is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__is_liked=self.is_liked, exam__sub=self.sub)
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context


class RateListView(BaseListView):
    star_count = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.sub = kwargs.get('sub', '전체')
        self.subject = next((instance['subject'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), None)
        self.sub_code = next((instance['sub_code'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), '')

        self.star_count = kwargs.get('star_count')
        if self.star_count is None:
            pagination_url = reverse_lazy('psat:rate_list')
        else:
            pagination_url = reverse_lazy('psat:rate_list_opt', args=[self.star_count])

        self.info = {
            'category': 'rate',
            'type': 'rateList',
            'sub': self.sub,
            'title': 'PSAT 난이도',
            'pagination_url': pagination_url,
            'target_id': f'rateListContent{self.sub_code}',
            'icon': MENU_RATE_ICON,
            'color': 'warning',
            'star_count': self.star_count,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        if self.sub == '전체':
            queryset = problem.filter(evaluation__user=user, evaluation__difficulty_rated__gte=1)
            if self.star_count is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__difficulty_rated=self.star_count)
        else:
            queryset = problem.filter(evaluation__user=user, evaluation__difficulty_rated__gte=1, exam__sub=self.sub)
            if self.star_count is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__difficulty_rated=self.star_count, exam__sub=self.sub)
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context


class AnswerListView(BaseListView):
    is_correct = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.sub = kwargs.get('sub', '전체')
        self.subject = next((instance['subject'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), None)
        self.sub_code = next((instance['sub_code'] for instance in TOTAL['subject_list'] if instance['sub'] == self.sub), '')

        self.is_correct = kwargs.get('is_correct')
        if self.is_correct is None:
            pagination_url = reverse_lazy('psat:answer_list')
        else:
            pagination_url = reverse_lazy('psat:answer_list_opt', args=[self.is_correct])

        self.info = {
            'category': 'answer',
            'type': 'answerList',
            'sub': self.sub,
            'title': 'PSAT 정답확인',
            'pagination_url': pagination_url,
            'target_id': f'answerListContent{self.sub_code}',
            'icon': MENU_ANSWER_ICON,
            'color': 'success',
            'is_correct': self.is_correct,
        }

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        if self.sub == '전체':
            queryset = problem.filter(evaluation__user=user, evaluation__is_correct__gte=0)
            if self.is_correct is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__is_correct=self.is_correct)
        else:
            queryset = problem.filter(evaluation__user=user, evaluation__is_correct__gte=0, exam__sub=self.sub)
            if self.is_correct is not None:
                queryset = problem.filter(evaluation__user=user, evaluation__is_correct=self.is_correct, exam__sub=self.sub)
        context = super().get_context_data(object_list=queryset, **kwargs)
        self.update_context(context)

        return context
