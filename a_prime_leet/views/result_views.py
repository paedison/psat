from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import normal_utils
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
    qs_registry = []
    if request.user.is_authenticated:
        qs_registry = models.ResultRegistry.objects.get_qs_registry_by_user(request.user)
    context = update_context_data(current_time=timezone.now(), config=config, registries=qs_registry)
    return render(request, 'a_prime_leet/result_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int, student=None, is_for_print=False):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not leet.is_active:
        context = update_context_data(context, message='성적 확인 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)

    if student is None:
        student = models.ResultStudent.objects.get_student(leet=leet, registries__user=request.user)
    if not student:
        context = update_context_data(
            context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    stat_data_total = normal_utils.get_dict_stat_data_for_result(student)
    stat_data_1 = normal_utils.get_dict_stat_data_for_result(student, 'aspiration_1')
    stat_data_2 = normal_utils.get_dict_stat_data_for_result(student, 'aspiration_2')

    fake_student = models.FakeStudent.objects.filter(leet=leet, serial=student.serial).first()
    if fake_student:
        fake_stat_data_total = normal_utils.get_dict_stat_data_for_fake(fake_student)
        fake_stat_data_1 = normal_utils.get_dict_stat_data_for_fake(fake_student, 'aspiration_1')
        fake_stat_data_2 = normal_utils.get_dict_stat_data_for_fake(fake_student, 'aspiration_2')

        stat_chart = normal_utils.get_dict_stat_chart(fake_student, fake_stat_data_total)
        score_frequency_dict = normal_utils.get_score_frequency_dict(leet, 'fake')
        stat_frequency_dict = normal_utils.get_stat_frequency_dict(fake_student, score_frequency_dict)
    else:
        fake_stat_data_total,fake_stat_data_1, fake_stat_data_2 = [], [], []
        stat_chart = normal_utils.get_dict_stat_chart(student, stat_data_total)
        score_frequency_dict = normal_utils.get_score_frequency_dict(leet)
        stat_frequency_dict = normal_utils.get_stat_frequency_dict(student, score_frequency_dict)

    qs_student_answer = models.ResultAnswer.objects.get_qs_answer_by_student(student)
    data_answers = normal_utils.get_data_answers_for_result(qs_student_answer)

    context = update_context_data(
        context, leet=leet, head_title=f'{leet.name} 성적표',
        icon_menu=icon_set_new.ICON_MENU, icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        score_tab=normal_utils.get_score_tab(),
        answer_tab=normal_utils.get_answer_tab(leet),

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_data_total=stat_data_total,
        stat_data_1=stat_data_1,
        stat_data_2=stat_data_2,

        # sheet_score: 누적 성적 확인
        fake_stat_data_total=fake_stat_data_total,
        fake_stat_data_1=fake_stat_data_1,
        fake_stat_data_2=fake_stat_data_2,

        # sheet_answer: 답안 확인
        data_answers=data_answers,

        # chart: 성적 분포 차트
        stat_chart=stat_chart,
        stat_frequency_dict=stat_frequency_dict,
        all_confirmed=True,
    )
    if is_for_print:
        return render(request, 'a_prime_leet/result_print.html', context)
    return render(request, 'a_prime_leet/result_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int, student=None):
    return detail_view(request, pk, student, True)


def student_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '성적 확인'
    form = forms.ResultStudentForm()
    context = update_context_data(config=config, title=title, form=form)

    if request.method == 'POST':
        form = forms.ResultStudentForm(request.POST)
        if form.is_valid():
            leet = form.cleaned_data['leet']
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['student_name']
            password = form.cleaned_data['student_password']

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
