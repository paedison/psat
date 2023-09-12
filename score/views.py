from django.core.paginator import Paginator
from django.db.models import Max
from django.shortcuts import render

from common.constants import color, icon
from common.constants.psat import TOTAL
from psat.models import Exam, Problem
from .forms import TemporaryAnswerForm
from .models import TemporaryAnswer, ConfirmedAnswer


class ScoreTemplate:
    """ Represent the appropriate templates. """
    list_base = 'score/score_list.html'  # score_list_view
    list_main = f'{list_base}#list_main'  # score_list_view
    list_content = f'{list_base}#list_content'  # score_list_view
    detail_base = 'score/score_detail.html'  # score_detail_view
    detail_content = f'{detail_base}#detail_content'  # score_detail_view w/ htmx
    score_form = f'{detail_base}#score_form'  # score_submit_form
    scored_problem = f'{detail_base}#scored_problem'  # score_submit_form
    score_confirm_modal = 'snippets/modal.html#score_confirm'  #
    score_confirmed_base = 'score/score_confirmed.html'  #
    score_confirmed_content = f'{score_confirmed_base}#confirmed_content'  # score_submit_form


class TargetAnswer:
    def __init__(self, request, problem=None, exam=None):
        self.request = request
        self.problem = problem
        self.exam = exam

    def get_exam_ids(self, boolean: bool) -> set[int]:
        return set(TemporaryAnswer.objects.filter(
            user=self.request.user, is_confirmed=boolean).order_by(
            'problem__id').values_list('problem__exam__id', flat=True))

    @property
    def temporary_exam_ids(self) -> set[int]: return self.get_exam_ids(False)
    @property
    def confirmed_exam_ids(self) -> set[int]: return self.get_exam_ids(True)

    @property
    def temporary_ans(self) -> TemporaryAnswer:
        """ Return the one TemporaryAnswer object. """
        if self.problem:
            return TemporaryAnswer.objects.filter(
                user=self.request.user, problem=self.problem,
                is_confirmed=False).first()

    @property
    def temporary_answers(self) -> TemporaryAnswer.objects:
        """ Return the TemporaryAnswer objects. """
        if self.exam:
            return TemporaryAnswer.objects.filter(
                user=self.request.user, problem__exam=self.exam,
                is_confirmed=False).order_by('problem__id')

    @property
    def temporary_answers_problem_ids(self) -> list:
        if self.temporary_answers:
            return self.temporary_answers.values_list('problem', flat=True)

    @property
    def confirmed_answers(self) -> TemporaryAnswer.objects:
        """ Return the TemporaryAnswer objects. """
        if self.exam is not None:
            confirmed_times = ConfirmedAnswer.objects.filter(
                user=self.request.user, problem__exam=self.exam
            ).aggregate(Max('confirmed_times'))['confirmed_times__max']
            return ConfirmedAnswer.objects.filter(
                user=self.request.user, problem__exam=self.exam,
                confirmed_times=confirmed_times).order_by('problem__id')


def score_list_view(request) -> render:
    # Get the template name
    if request.method == 'POST':
        template_name = ScoreTemplate.list_main
    else:
        if request.htmx:
            template_name = ScoreTemplate.list_content
        else:
            template_name = ScoreTemplate.list_base

    # Get the temporary and confirmed answers list
    target_answer = TargetAnswer(request)
    temporary_exam_ids = target_answer.temporary_exam_ids
    confirmed_exam_ids = target_answer.confirmed_exam_ids

    # Get paginator for total exam list
    exam_list = TOTAL['list']
    paginate_by = 10
    paginator = Paginator(exam_list, paginate_by)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=3, on_ends=1)

    # Return the current status of the target exam
    def get_status(target_exam):
        try:
            if target_exam.id in temporary_exam_ids:
                return False  # 작성 중
            elif target_exam.id in confirmed_exam_ids:
                return True  # 제출 완료
            else:
                return None  # 작성 전
        except AttributeError:
            return 'N/A'  # 해당 사항 없음(시험에서 제외된 과목)

    # Get additional information of page_obj
    exams = Exam.objects.all()
    for obj in page_obj:
        exam_eoneo = exams.filter(year=obj['year'], ex=obj['ex'], sub='언어').first()
        exam_jaryo = exams.filter(year=obj['year'], ex=obj['ex'], sub='자료').first()
        exam_sanghwang = exams.filter(year=obj['year'], ex=obj['ex'], sub='상황').first()
        obj['eoneo'] = {
            'exam_id': exam_eoneo.id if exam_eoneo else None,
            'status': get_status(exam_eoneo),
        }
        obj['jaryo'] = {
            'exam_id': exam_jaryo.id if exam_jaryo else None,
            'status': get_status(exam_jaryo),
        }
        obj['sanghwang'] = {
            'exam_id': exam_sanghwang.id if exam_sanghwang else None,
            'status': get_status(exam_sanghwang),
        }

    info = {
        'menu': 'score',
        'title': 'Score',
        'icon': '<i class="fa-solid fa-circle-check"></i>',
        'color': 'primary',

    }
    context = {
        'info': info,
        'page_obj': page_obj,
        'exams': exams,
        'page_range': page_range,
    }
    return render(request, template_name, context)


def score_detail_view(request, exam_id: int) -> render:
    # Get the template name
    if request.htmx:
        template_name = ScoreTemplate.detail_content
    else:
        template_name = ScoreTemplate.detail_base

    exam = Exam.objects.get(id=exam_id)
    target_answer = TargetAnswer(request, exam=exam)
    temporary_answers_problem_ids = target_answer.temporary_answers_problem_ids

    problems = exam.problems.all()
    for problem in problems:
        if temporary_answers_problem_ids:
            if problem.id in temporary_answers_problem_ids:
                target_answer2 = TargetAnswer(request, exam=exam, problem=problem)
                problem.submitted_answer = target_answer2.temporary_ans.answer

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
    return render(request, template_name, context)


def score_submit_form(request, problem_id: int) -> render:
    problem = Problem.objects.get(id=problem_id)
    target_answer = TargetAnswer(request, problem=problem)

    if request.method == 'GET':
        template_name = ScoreTemplate.score_form  # template_name
        context = {'problem': problem}
    else:
        form = TemporaryAnswerForm(request.POST)
        submitted_answer: int = int(request.POST.get('answer'))
        temporary_ans: TemporaryAnswer = target_answer.temporary_ans
        if temporary_ans is None:
            form.user = request.user.id
            if form.is_valid():
                template_name = ScoreTemplate.scored_problem  # template_name
                scored = form.save()
                context = {'scored': scored}
            else:
                template_name = ScoreTemplate.score_form  # template_name
                context = {'problem': problem}
        else:
            template_name = ScoreTemplate.scored_problem  # template_name
            temporary_ans.answer = submitted_answer
            temporary_ans.save()
            scored = temporary_ans
            context = {'scored': scored}
    return render(request, template_name, context)


def score_confirm(request, exam_id: int):
    # Get the template name
    if request.method == 'POST':
        template_name = ScoreTemplate.score_confirm_modal
    else:
        if request.htmx:
            template_name = ScoreTemplate.score_confirmed_content
        else:
            template_name = ScoreTemplate.score_confirmed_base

    exam = Exam.objects.get(id=exam_id)
    target_answer = TargetAnswer(request, exam=exam)

    if request.method == 'POST':
        temporary_answers = target_answer.temporary_answers
        if exam.problems.count() != temporary_answers.count():
            all_confirmed = False
        else:
            for obj in temporary_answers:
                obj.is_confirmed = True
                obj.save()
                ConfirmedAnswer.objects.get_or_create(
                    user=request.user, problem=obj.problem, answer=obj.answer)
            all_confirmed = True
        context = {
            'all_confirmed': all_confirmed,
            'exam_id': exam_id,
        }
        return render(request, template_name, context)
    else:
        confirmed_answers = target_answer.confirmed_answers
        info = {
            'menu': 'score',
            'title': exam.full_title,
            'exam_id': exam_id,
            'icon': icon.MENU_ICON_SET['answer'],
            'color': color.COLOR_SET['answer'],
        }
        context = {
            'info': info,
            'confirmed_answers': confirmed_answers,
        }
        return render(request, template_name, context)
