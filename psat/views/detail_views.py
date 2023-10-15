from django.urls import reverse_lazy
from vanilla import DetailView, TemplateView

from common import constants
from .list_views import get_evaluation_info
from ..models import Problem, Evaluation, ProblemMemo, ProblemTag

menu_icon_set = constants.icon.MENU_ICON_SET


class PSATDetailInfoMixIn:
    """
    Represent PSAT detail information mixin.
    view_type(str): One of [ problem, like, rate, answer ]
    """
    kwargs: dict
    view_type: str
    title: str
    request: any
    prob_data: Problem.objects

    icon_container = 'psat/snippets/icon_container.html'
    detail_template = 'psat/problem_detail.html'

    @property
    def problem_id(self) -> int: return int(self.kwargs.get('problem_id'))
    @property
    def problem(self) -> Problem: return Problem.objects.get(id=self.problem_id)
    @property
    def object(self) -> Problem: return self.problem
    @property
    def icon_id(self) -> str: return self.request.GET.get('icon_id')
    @property
    def icon_template(self) -> str: return f'{self.icon_container}#{self.view_type}'
    @property
    def prob_list(self) -> list: return self.prob_data.values_list('id', flat=True)
    @property
    def list_data(self) -> list: return self.get_detail_list(self.prob_data)
    @property
    def prev_prob(self) -> Problem: return self.get_probs(self.prob_data, self.prob_list)[0]
    @property
    def next_prob(self) -> Problem: return self.get_probs(self.prob_data, self.prob_list)[1]

    @property
    def num_range(self):
        if self.problem.ex == '민경' or '칠급':
            return range(1, 26)
        else:
            return range(1, 41)

    @property
    def evaluation(self) -> Evaluation:
        return Evaluation.objects.get_or_create(
            user=self.request.user, problem=self.problem)[0]

    def get_detail_list(self, prob_data: any) -> list:
        organized_dict: dict = self.get_organized_dict(prob_data)
        return get_organized_list(organized_dict)

    def get_organized_dict(self, prob_data: any) -> dict:
        """ Return a dictionary sorted by exam. """
        organized_dict = {}
        for prob in prob_data:
            key = prob.exam.id
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam2, subject = prob.exam.year, prob.exam.exam2, prob.exam.subject
            list_item = {
                'exam_name': f"{year}년 '{exam2}' {subject}",
                'problem_number': prob.number,
                'problem_id': prob.id,
                'problem_url': self.get_reverse_lazy(prob.id)
            }
            organized_dict[key].append(list_item)
        return organized_dict

    def get_probs(self, prob_data=None, prob_list=None) -> [Problem, Problem]:
        prev_prob = next_prob = None
        page_list = list(prob_list)
        last_id = len(page_list) - 1
        q = page_list.index(self.problem_id)
        if q != 0:
            prev_prob = prob_data.filter(id=page_list[q - 1]).first()
        if q != last_id:
            next_prob = prob_data.filter(id=page_list[q + 1]).first()
        return prev_prob, next_prob

    @property
    def my_tag(self) -> ProblemTag | None:
        if self.request.user.is_authenticated:
            return ProblemTag.objects.filter(user=self.request.user,
                                             problem=self.problem).first()
        return None

    @property
    def problem_memo(self) -> ProblemMemo | None:
        if self.request.user.is_authenticated:
            return ProblemMemo.objects.filter(user=self.request.user,
                                              problem=self.problem).first()
        return None

    def get_reverse_lazy(self, problem_id) -> reverse_lazy:
        return reverse_lazy(f'psat:{self.view_type}_detail', args=[problem_id])

    @property
    def info(self) -> dict:
        return {
            'menu': self.view_type,
            'view_type': self.view_type,
            'type': f'{self.view_type}Detail',
            'title': self.title,
            'current_url': self.get_reverse_lazy(self.problem_id),
            'icon': menu_icon_set[self.view_type],
            'problem_id': self.problem_id,
        }


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


class BaseDetailView(PSATDetailInfoMixIn, DetailView):
    """Represent PSAT base detail view."""
    model = Problem
    context_object_name = 'problem'
    lookup_field = 'id'
    lookup_url_kwarg = 'problem_id'

    @property
    def title(self) -> str: return self.object.full_title
    def get_object(self) -> Problem: return self.problem

    def get_template_names(self) -> str:
        base_template = self.detail_template
        main_template = f'{base_template}#detail_main'
        if self.request.method == 'GET':
            return main_template if self.request.htmx else base_template
        else:
            return main_template

        # return self.detail_template if self.request.method == 'GET' else self.icon_template

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.evaluation.update_open()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['num_range'] = self.num_range
        context['problem_memo'] = self.problem_memo
        context['my_tag'] = self.my_tag
        context['anchor_id'] = self.problem_id - int(self.object.number)
        context['problem'] = get_evaluation_info(self.request.user, self.object)
        if self.request.method == 'GET':
            context['prev_prob'] = self.prev_prob
            context['next_prob'] = self.next_prob
            context['list_data'] = self.list_data
        return context


class ProblemDetailView(BaseDetailView):
    view_type = 'problem'
    @property
    def prob_data(self): return Problem.objects.filter(exam=self.problem.exam)


class LikeDetailView(BaseDetailView):
    view_type = 'like'

    @property
    def prob_data(self):
        return Problem.objects.filter(
            evaluation__user=self.request.user, evaluation__is_liked__gte=1)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_like()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RateDetailView(BaseDetailView):
    view_type = 'rate'
    @property
    def difficulty(self) -> int: return int(self.request.POST.get('difficulty'))

    @property
    def prob_data(self):
        return Problem.objects.filter(
            evaluation__user=self.request.user, evaluation__difficulty_rated__gte=0)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_rate(self.difficulty)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class AnswerDetailView(BaseDetailView):
    view_type = 'answer'

    @property
    def answer(self) -> int: return int(self.request.POST.get('answer'))

    @property
    def prob_data(self) -> object:
        return Problem.objects.filter(
            evaluation__user=self.request.user, evaluation__is_correct__gte=0)

    def post(self, request, *args, **kwargs):
        self.evaluation.update_answer(self.answer)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RateDetailModalView(PSATDetailInfoMixIn, TemplateView):
    template_name = 'snippets/modal.html#rate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem_id'] = self.problem_id
        context['icon_id'] = self.icon_id
        return context


class AnswerDetailModalView(PSATDetailInfoMixIn, TemplateView):
    template_name = 'snippets/modal.html#answer'

    @property
    def answer(self) -> int | None:
        answer_ = self.request.POST.get('answer')
        answer_ = int(answer_) if answer_ else None
        return answer_

    @property
    def is_correct(self) -> bool | None:
        return None if self.answer is None else (self.answer == self.evaluation.correct_answer)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer'] = self.answer
        context['is_correct'] = self.is_correct
        context['problem_id'] = self.problem_id
        return context


problem = ProblemDetailView.as_view()
like = LikeDetailView.as_view()
rate = RateDetailView.as_view()
answer = AnswerDetailView.as_view()
rate_modal = RateDetailModalView.as_view()
answer_modal = AnswerDetailModalView.as_view()
