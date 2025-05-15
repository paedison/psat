from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from . import normal_utils
from .. import models


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임LEET'
    submenu = submenu_eng = 'fake'
    submenu_kor = '가상 결과'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:result-list')
    url_student_register = reverse_lazy('prime_leet:result-student-register')


def detail_view(request: HtmxHttpRequest, pk: int, student=None, is_for_print=False):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    leet = models.Leet.objects.filter(pk=pk).first()
    if not leet or not leet.is_active:
        context = update_context_data(context, message='성적 확인 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_prime_leet/redirect.html', context)

    if student is None:
        student = models.FakeStudent.objects.get_student(leet=leet)
    if not student:
        context = update_context_data(
            context, message='등록된 수험정보가 없습니다.', next_url=config.url_list)
        return render(request, 'a_psat/redirect.html', context)

    stat_data_total = normal_utils.get_dict_stat_data_for_fake(student)
    stat_data_1 = normal_utils.get_dict_stat_data_for_fake(student, 'aspiration_1')
    stat_data_2 = normal_utils.get_dict_stat_data_for_fake(student, 'aspiration_2')

    stat_chart = normal_utils.get_dict_stat_chart(student, stat_data_total)
    score_frequency_dict = normal_utils.get_score_frequency_dict(leet, 'fake')
    stat_frequency_dict = normal_utils.get_stat_frequency_dict(student, score_frequency_dict)

    qs_problem = models.Problem.objects.filter(leet=leet)
    data_answers = normal_utils.get_data_answers_for_fake(qs_problem)

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
