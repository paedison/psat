from django.core.paginator import Paginator
from django.db.models import Max
from django.shortcuts import render

from common.constants import color, icon
from common.constants.psat import TOTAL
from common.models import User
from psat.models import Exam, Problem
from .forms import TemporaryAnswerForm
from .models import TemporaryAnswer, ConfirmedAnswer


def get_template() -> dict:
    """ Return the appropriate templates. """
    list_base = 'score/score_list.html'  # score_list_view
    list_main = f'{list_base}#list_main'  # score_list_view
    list_content = f'{list_base}#list_content'  # score_list_view
    detail_base = 'score/score_detail.html'  # score_detail_view
    detail_content = f'{detail_base}#detail_content'  # score_detail_view w/ htmx
    score_form = f'{detail_base}#score_form'  # score_submit_form
    scored_problem = f'{detail_base}#scored_problem'  # score_submit_form
    score_confirm_modal = 'snippets/modal.html#score_confirm'  #
    score_confirmed = 'score/score_confirmed.html'  #
    score_confirmed_content = f'{score_confirmed}#confirmed_content'  # score_submit_form
    return {
        'list_base': list_base,
        'list_main': list_main,
        'list_content': list_content,
        'detail_base': detail_base,
        'detail_content': detail_content,
        'score_form': score_form,
        'scored_problem': scored_problem,
        'score_confirm_modal': score_confirm_modal,
        'score_confirmed': score_confirmed,
        'score_confirmed_content': score_confirmed_content,
    }


def get_temporary_obj(user: User, problem: Problem) -> TemporaryAnswer:
    """ Return the one TemporaryAnswer object. """
    return TemporaryAnswer.objects.filter(
        user=user, problem=problem, is_confirmed=False).first()


def get_temporary_objects(user: User, exam: Exam) -> TemporaryAnswer.objects:
    """ Return the TemporaryAnswer objects. """
    return TemporaryAnswer.objects.filter(
        user=user, problem__exam=exam, is_confirmed=False).order_by('problem__id')


def get_confirmed_objects(user: User, exam: Exam) -> TemporaryAnswer.objects:
    """ Return the TemporaryAnswer objects. """
    confirmed_times = ConfirmedAnswer.objects.filter(
        user=user, problem__exam=exam).aggregate(Max('confirmed_times'))['confirmed_times__max']
    return ConfirmedAnswer.objects.filter(
        user=user, problem__exam=exam, confirmed_times=confirmed_times).order_by('problem__id')


def get_confirmed_times(user: User, exam: Exam) -> int:
    """ Return the TemporaryAnswer objects. """
    return ConfirmedAnswer.objects.filter(
        user=user, problem__exam=exam).aggregate(Max('confirmed_times'))['confirmed_times__max']


def score_list_view(request) -> render:
    # Get the template name
    if request.method == 'GET':
        if request.htmx:
            template_name = get_template()['list_content']
        else:
            template_name = get_template()['list_base']
    else:
        template_name = get_template()['list_main']

    # Get the temporary and confirmed answers list
    temporary_exams_ids = TemporaryAnswer.objects.filter(
        user=request.user, is_confirmed=False).order_by(
        'problem__id').values_list('problem__exam__id', flat=True).distinct()
    confirmed_exams_ids = TemporaryAnswer.objects.filter(
        user=request.user, is_confirmed=True).order_by(
        'problem__id').values_list('problem__exam__id', flat=True).distinct()

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
    return render(request, template_name, context)


def score_detail_view(request, exam_id: int) -> render:
    # Get the template name
    if request.htmx:
        template_name = get_template()['detail_content']
    else:
        template_name = get_template()['detail_base']

    exam = Exam.objects.get(id=exam_id)
    problems = exam.problems.all()
    temporary_objects_ids = get_temporary_objects(
        request.user, exam).values_list('problem', flat=True)

    for prob in problems:
        if prob.id in temporary_objects_ids:
            prob.submitted_answer = get_temporary_obj(request.user, prob).answer

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
    answer_form_template = get_template()['score_form']
    answered_problem_template = get_template()['scored_problem']

    problem = Problem.objects.get(id=problem_id)

    if request.method == 'GET':
        context = {'problem': problem}
        template_name = answer_form_template
    else:
        form = TemporaryAnswerForm(request.POST)
        submitted_answer: int = int(request.POST.get('answer'))
        temporary_obj: TemporaryAnswer = get_temporary_obj(request.user, problem)
        if temporary_obj is None:
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
            temporary_obj.answer = submitted_answer
            temporary_obj.save()
            answered = temporary_obj
            context = {'answered': answered}
            template_name = answered_problem_template
    return render(request, template_name, context)


def score_confirm(request, exam_id: int):
    exam = Exam.objects.get(id=exam_id)
    if request.method == 'POST':
        template_name = get_template()['score_confirm_modal']
        temporary_objects: TemporaryAnswer.objects = get_temporary_objects(request.user, exam)
        if exam.problems.count() != temporary_objects.count():
            all_confirmed = False
        else:
            for obj in temporary_objects:
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
        # Get the template name
        if request.htmx:
            template_name = get_template()['score_confirmed_content']
        else:
            template_name = get_template()['score_confirmed']

        exam = Exam.objects.get(id=exam_id)
        confirmed_objects = get_confirmed_objects(request.user, exam)

        info = {
            'menu': 'score',
            'title': exam.full_title,
            'exam_id': exam_id,
            'icon': icon.MENU_ICON_SET['answer'],
            'color': color.COLOR_SET['answer'],
        }
        context = {
            'info': info,
            'confirmed_objects': confirmed_objects,
        }
        return render(request, template_name, context)
