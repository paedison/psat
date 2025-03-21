from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import result_utils
from .. import models, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임LEET'
    submenu = submenu_eng = 'result'
    submenu_kor = '성적 확인'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:result-list')
    url_student_register = reverse_lazy('prime_leet:result-student-register')


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    qs_registry = models.ResultRegistry.objects.with_select_related().filter(user=request.user)
    context = update_context_data(current_time=timezone.now(), config=config, registries=qs_registry)
    return render(request, 'a_prime_leet/result_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int, student=None, is_for_print=False):
    config = ViewConfiguration()
    context = update_context_data(current_time=timezone.now(), config=config)

    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not leet.is_active:
        context = update_context_data(context, message='성적 확인 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)

    if student is None:
        student = result_utils.get_student(leet, request.user)
    if not student:
        context = update_context_data(
            context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)
    context = update_context_data(context, leet=leet, student=student)

    sub_list = result_utils.get_sub_list()
    stat_data_total = result_utils.get_dict_stat_data(student)
    stat_data_1 = result_utils.get_dict_stat_data(student, 'aspiration_1')
    stat_data_2 = result_utils.get_dict_stat_data(student, 'aspiration_2')

    frequency_score = result_utils.get_dict_frequency_score(student)
    qs_answer = models.ResultAnswer.objects.prime_leet_qs_answer_by_student(student)
    data_answers = result_utils.get_data_answers(qs_answer)

    context = update_context_data(
        context, sub_title=f'{leet.name} 성적표', sub_list=sub_list,
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        answer_tab=result_utils.get_answer_tab(),
        score_tab=result_utils.get_score_tab(),

        # sheet_score: 성적 확인
        stat_data_total=stat_data_total,
        stat_data_1=stat_data_1,
        stat_data_2=stat_data_2,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answers=data_answers,
    )
    if is_for_print:
        return render(request, 'a_prime_leet/result_print.html', context)
    return render(request, 'a_prime_leet/result_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int):
    return detail_view(request, pk, is_for_print=True)


def student_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '수험정보 등록'
    form = forms.ResultStudentForm()
    context = update_context_data(config=config, title=title, form=form)

    if request.method == 'POST':
        form = forms.ResultStudentForm(request.POST)
        if form.is_valid():
            leet = form.cleaned_data['leet']
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']

            existing_registry = models.ResultRegistry.objects.filter(user=request.user, student__leet=leet)
            if not existing_registry.exists():
                student = models.ResultStudent.objects.filter(
                    leet=leet, serial=serial, name=name, password=password).first()
                if student:
                    registry = models.ResultRegistry.objects.create(user=request.user, student=student)
                    return redirect(registry.student.leet.get_result_detail_url())
                form.add_error(None, '존재하지 않는 수험정보입니다.')
            else:
                form.add_error(None, '해당 시험으로 등록된 수험정보가 존재합니다.')
            form.add_error(None, '시험명 및 수험정보를 다시 확인해주세요.')
        context = update_context_data(context, form=form)

    return render(request, 'a_prime_leet/admin_form.html', context)


def modal_view(request: HtmxHttpRequest, pk: int):
    leet = models.Leet.objects.get(pk=pk)
    hx_modal = request.headers.get('View-Modal', '')
    is_no_open = hx_modal == 'no_open'
    is_student_register = hx_modal == 'student_register'

    context = update_context_data(exam=leet)
    if is_no_open:
        return render(request, 'a_prime_leet/snippets/modal_no_open.html', context)

    if is_student_register:
        context = update_context_data(
            context,
            header=f'{leet.name} 수험 정보 입력',
        )
        return render(request, 'a_prime_leet/snippets/modal_student_register.html', context)
