from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils
from .score_info import ScorePsatExamVars


class ViewConfiguration:
    menu = menu_eng = 'prime'
    menu_kor = '프라임'
    submenu = submenu_eng = 'score'
    submenu_kor = '모의고사 성적 확인'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_psat_changelist')
    url_list = reverse_lazy('prime:score-list')


def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam_list = models.Psat.objects.filter(year=2024)

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    if request.user.is_authenticated:
        for obj in page_obj:
            obj.url_modal = reverse('prime:score-modal', args=[obj.id])
            student = models.ResultStudent.objects.filter(
                registries__user=request.user, psat__year=obj.year, psat__round=obj.round).order_by('id').last()
            if student:
                obj.student = student
                obj.url_detail = reverse('prime:score-detail', args=[obj.id])

    context = update_context_data(
        config=config, current_time=timezone.now(), icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj, page_range=page_range)
    return render(request, 'a_prime/score_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    psat = models.Psat.objects.get(pk=pk)
    config.submenu_kor = f'제{psat.round}회 ' + config.submenu_kor

    exam_vars = ScorePsatExamVars(psat)
    exam_vars.student = student = exam_vars.get_student(request)
    if not request.user.is_authenticated or not student:
        return redirect(exam_vars.url_list)

    qs_student_answer = models.ResultAnswer.objects.filter(
        problem__psat=psat, student=exam_vars.student).annotate(
        is_correct=Case(
            When(answer=F('problem__answer'), then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )

    data_answer_official, data_answer_student = utils.get_data_answer(exam_vars, qs_student_answer)

    stat_total = utils.get_dict_stat_data(exam_vars, student, 'total')
    stat_department = utils.get_dict_stat_data(exam_vars, student, 'department')

    frequency_score = utils.get_dict_frequency_score(exam_vars, student)

    context = update_context_data(
        config=config,
        info=exam_vars.info, current_time=timezone.now(),
        title='Score', sub_title=exam_vars.sub_title,
        icon_menu=exam_vars.icon_menu,
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        exam_vars=exam_vars, exam=exam_vars.exam,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_total=stat_total,
        stat_department=stat_department,

        # # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answer_official=data_answer_official,
        data_answer_student=data_answer_student,
    )
    return render(request, 'a_prime/score_detail.html', context)


def detail_print_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    pass


def modal_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = utils.get_exam_vars(**kwargs)
    exam = exam_vars.exam

    hx_modal = request.headers.get('View-Modal', '')
    is_no_open = hx_modal == 'no_open'
    is_student_register = hx_modal == 'student_register'

    if is_no_open:
        context = update_context_data(exam=exam)
        return render(request, 'a_prime/snippets/modal_no_open.html', context)

    if is_student_register:
        header = f'{exam_vars.exam_year}년 대비 제{exam_vars.exam_round}회 프라임 모의고사 수험 정보 입력'
        context = update_context_data(exam_vars=exam_vars, header=header, **exam_vars.exam_info)
        return render(request, 'a_prime/snippets/modal_student_register.html', context)


@require_POST
@login_required
def student_register_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = utils.get_exam_vars(**kwargs)
    context = update_context_data(exam_vars=exam_vars)
    form = exam_vars.student_form(data=request.POST, files=request.FILES)
    if form.is_valid():
        target_student = models.ResultStudent.objects.get(
            **exam_vars.exam_info, serial=form.cleaned_data['serial'],
            name=form.cleaned_data['name'], password=form.cleaned_data['password'])
        registered_student, _ = models.ResultRegistry.objects.get_or_create(
            user=request.user, student=target_student)
        context = update_context_data(context, form=form, user_verified=True)
    else:
        context = update_context_data(context, form=form)

    return render(request, 'a_prime/snippets/modal_student_register.html#student_info', context)
