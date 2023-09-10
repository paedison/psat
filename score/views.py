from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from vanilla import ListView, CreateView

from common.constants import psat, color, icon
from psat.models import Exam, Problem
from score.forms import TemporaryAnswerForm
from score.models import TemporaryAnswer


class TemporaryAnswerListView(ListView):
    category = 0
    view_type = 'answer'
    list_template = 'score/answer_list.html'
    list_content_template = 'score/answer_list_content.html'
    subject_list = {'전체': 0, '언어': 1, '자료': 2, '상황': 3}

    model = TemporaryAnswer
    paginate_by = 10

    @property
    def sub(self) -> str: return self.kwargs.get('sub')

    @property
    def sub_code(self) -> int:
        print(self.sub)
        if self.sub:
            return self.subject_list[self.sub]
        return None

    @property
    def menu_url(self) -> dict:
        return {
            'total': reverse_lazy('score:list_content', args=['전체']),
            'eoneo': reverse_lazy('score:list_content', args=['언어']),
            'jaryo': reverse_lazy('score:list_content', args=['자료']),
            'sanghwang': reverse_lazy('score:list_content', args=['상황']),
        }

    @property
    def pagination_url(self) -> reverse_lazy:
        if self.sub is None:
            return None
        return reverse_lazy(f'score:list_content', args=[self.sub])

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.sub == '전체':
            return queryset
        else:
            return queryset.filter(problem__exam__sub=self.sub)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = {
            'menu': 'score',
            'menu_url': self.menu_url,
            'category': self.category,
            'view_type': self.view_type,
            'type': f'{self.view_type}List',
            'title': 'Answer List',
            'sub': self.sub,
            'sub_code': self.sub_code,
            'pagination_url': self.pagination_url,
            'icon': '<i class="fa-solid fa-circle-check"></i>',
            'color': 'primary',
        }

    def get_template_names(self):
        if self.sub is None:
            return self.list_template
        else:
            return self.list_content_template


class TemporaryAnswerCreateView(CreateView):
    model = TemporaryAnswer
    form_class = TemporaryAnswerForm
    template_name = 'score/answer_form.html'
    context_object_name = 'problems'

    @property
    def year(self) -> int: return int(self.kwargs.get('year'))
    @property
    def ex(self) -> str: return self.kwargs.get('ex')
    @property
    def sub(self) -> str: return self.kwargs.get('sub')
    @property
    def exam(self) -> Exam: return Exam.objects.get(year=self.year, ex=self.ex, sub=self.sub)
    @property
    def problems(self) -> Problem: return Problem.objects.filter(exam=self.exam)
    @property
    def object_list(self) -> Problem: return self.problems

    @property
    def info(self) -> dict:
        return {
            'menu': 'score',
            'title': self.exam.full_title,
            'sub': self.sub,
            # 'sub_code': self.sub_code,
            # 'pagination_url': self.pagination_url,
            'icon': icon.MENU_ICON_SET['answer'],
            'color': color.COLOR_SET['answer'],
            # 'is_liked': self.is_liked,
            # 'star_count': self.star_count,
            # 'is_correct': self.is_correct,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


def temporary_answer_create(request, problem_id):
    basic_template = 'score/answer_form.html'
    answer_form_template = f'{basic_template}#answer_form'
    answered_template = f'{basic_template}#answered_problem'

    problem = Problem.objects.get(id=problem_id)

    if request.method == 'GET':
        return render(request, answer_form_template, {'problem': problem})
    elif request.method == 'POST':
        form = TemporaryAnswerForm(request.POST)
        answer = int(request.POST.get('answer'))

        temporary_answer = TemporaryAnswer.objects.filter(
            user=request.user, problem=problem, is_confirmed=False).first()
        if temporary_answer is None:
            form.user = request.user.id
            # form.problem_id = problem_id
            if form.is_valid():
                answered = form.save()
            else:
                print(form.errors)
                return render(request, answer_form_template, {'problem': problem})
        else:
            temporary_answer.answer = answer
            temporary_answer.save()
            answered = temporary_answer
        return render(request, answered_template, {'answered': answered})
