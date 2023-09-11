from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from common.constants import color, icon
from common.constants.psat import TOTAL
from common.models import User
from psat.models import Exam, Problem
from .forms import TemporaryAnswerForm
from .models import TemporaryAnswer


def get_template() -> dict:
    """ Return the appropriate templates. """
    list_base = 'score/answer_list.html'  # score_list_view
    list_main = f'{list_base}#list_main'  # score_list_view
    list_content = f'{list_base}#list_content'  # score_list_view
    detail_base = 'score/answer_detail.html'  # score_detail_view
    detail_content = f'{detail_base}#detail_content'  # score_detail_view w/ htmx
    answer_form = f'{detail_base}#answer_form'  # score_submit_form
    answered_problem = f'{detail_base}#answered_problem'  # score_submit_form
    return {
        'list_base': list_base,
        'list_main': list_main,
        'list_content': list_content,
        'detail_base': detail_base,
        'detail_content': detail_content,
        'answer_form': answer_form,
        'answered_problem': answered_problem,
    }


def get_answer_obj(user: User, problem: Problem) -> TemporaryAnswer:
    """ Return the one TemporaryAnswer object. """
    return TemporaryAnswer.objects.filter(
        user=user, problem=problem, is_confirmed=False).first()


def get_answer_objects(user: User, exam: Exam) -> TemporaryAnswer.objects:
    """ Return the TemporaryAnswer objects. """
    return TemporaryAnswer.objects.filter(
        user=user, problem__exam=exam, is_confirmed=False)


def score_list_view(request) -> render:
    # Get the template name
    if request.method == 'GET':
        if request.htmx:
            list_template = get_template()['list_content']
        else:
            list_template = get_template()['list_base']
    else:
        list_template = get_template()['list_main']

    # Get the temporary and confirmed answers list
    temporary_exams_ids = TemporaryAnswer.objects.filter(
        user=request.user, is_confirmed=False).values_list(
        'problem__exam__id', flat=True).distinct()
    confirmed_exams_ids = TemporaryAnswer.objects.filter(
        user=request.user, is_confirmed=True).values_list(
        'problem__exam__id', flat=True).distinct()

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
            if target_exam.id in temporary_exams_ids:
                return False  # 작성 전
            elif target_exam.id in confirmed_exams_ids:
                return True  # 작성 중
            else:
                return None  # 제출 완료
        except AttributeError:
            return 'N/A'

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
    return render(request, list_template, context)


def score_detail_view(request, exam_id: int) -> render:
    if request.htmx:
        detail_base_template = get_template()['detail_content']
    else:
        detail_base_template = get_template()['detail_base']
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
    return render(request, detail_base_template, context)


def score_submit_form(request, problem_id: int) -> render:
    answer_form_template = get_template()['answer_form']
    answered_problem_template = get_template()['answered_problem']

    problem = Problem.objects.get(id=problem_id)

    if request.method == 'GET':
        context = {'problem': problem}
        template_name = answer_form_template
    else:
        form = TemporaryAnswerForm(request.POST)
        submitted_answer: int = int(request.POST.get('answer'))
        answer_obj: TemporaryAnswer = get_answer_obj(request.user, problem)
        if answer_obj is None:
            form.user = request.user.id
            if form.is_valid():
                answered = form.save()
                context = {'answered': answered}
                template_name = answered_problem_template
            else:
                print(form.errors)
                context = {'problem': problem}
                template_name = answer_form_template
        else:
            answer_obj.answer = submitted_answer
            answer_obj.save()
            answered = answer_obj
            context = {'answered': answered}
            template_name = answered_problem_template
    return render(request, template_name, context)


def score_confirm(request, exam_id: int):
    exam = Exam.objects.get(id=exam_id)
    answer_objects = get_answer_objects(request.user, exam)
    if exam.problems.count() != answer_objects.count():
        return HttpResponse('모든 문제의 정답을 제출해주세요.')
    for obj in answer_objects:
        obj.is_confirmed = True
        obj.save()
    return HttpResponse('정답이 정상적으로 제출되었습니다.')
