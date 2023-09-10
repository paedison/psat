from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from vanilla import ListView, CreateView

from common.constants import color, icon
from common.models import User
from psat.models import Exam, Problem
from .forms import TemporaryAnswerForm
from .models import TemporaryAnswer


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
            'year': self.year,
            'ex': self.ex,
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


def get_template() -> (str, str, str):
    basic = 'score/answer_form.html'
    answer_form = f'{basic}#answer_form'
    answered = f'{basic}#answered_problem'
    return basic, answer_form, answered


def get_answer_obj(user: User, problem: Problem) -> TemporaryAnswer:
    return TemporaryAnswer.objects.filter(
        user=user, problem=problem, is_confirmed=False).first()


def get_answer_objects(user: User, exam: Exam) -> TemporaryAnswer.objects:
    return TemporaryAnswer.objects.filter(
        user=user, problem__exam=exam, is_confirmed=False)


def answer_detail(request, exam_id: int) -> render:
    basic_template = get_template()[0]
    exam = Exam.objects.get(id=exam_id)
    problems = exam.problems.all()
    answer_objects_ids = get_answer_objects(request.user, exam).order_by(
        'problem').values_list('problem', flat=True)

    for prob in problems:
        if prob.id in answer_objects_ids:
            prob.submitted_answer = get_answer_obj(request.user, prob).answer

    info = {
        'menu': 'score',
        'title': exam.full_title,
        'exam_id': exam_id,
        'icon': icon.MENU_ICON_SET['answer'],
        'color': color.COLOR_SET['answer'],
    }
    context = {
        'info': info,
        'problems': problems,
    }
    return render(request, basic_template, context)


def answer_submit(request, problem_id: int) -> render:
    answer_form_template = get_template()[1]
    answered_template = get_template()[2]
    problem = Problem.objects.get(id=problem_id)

    if request.method == 'GET':
        return render(request, answer_form_template, {'problem': problem})
    elif request.method == 'POST':
        form = TemporaryAnswerForm(request.POST)
        submitted_answer: int = int(request.POST.get('answer'))
        answer_obj: TemporaryAnswer = get_answer_obj(request.user, problem)
        if answer_obj is None:
            form.user = request.user.id
            if form.is_valid():
                answered = form.save()
            else:
                print(form.errors)
                return render(request, answer_form_template, {'problem': problem})
        else:
            answer_obj.answer = submitted_answer
            answer_obj.save()
            answered = answer_obj
        return render(request, answered_template, {'answered': answered})


def answer_confirm(request, exam_id: int):
    exam = Exam.objects.get(id=exam_id)
    answer_objects = get_answer_objects(request.user, exam)
    if exam.problems.count() != answer_objects.count():
        return HttpResponse('모든 문제의 정답을 제출해주세요.')
    for obj in answer_objects:
        obj.is_confirmed = True
        obj.save()
    return HttpResponse('정답이 정상적으로 제출되었습니다.')
