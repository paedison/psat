import json
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import retarget, reswap, push_url

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    psat_year = 2024
    psat_exam = '행시'

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_list = reverse_lazy('psat:predict-list')

    def get_psat(self):
        return get_object_or_404(models.PredictPsat, psat__year=self.psat_year, psat__exam=self.psat_exam)


def get_student_dict(user, exam_list):
    if user.is_authenticated:
        students = (
            models.PredictStudent.objects.filter(user=user, psat__in=exam_list)
            .select_related('psat', 'score', 'category').order_by('id')
        )
        return {student.psat: student for student in students}
    return {}


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam_list = models.Psat.objects.filter(year=2025)

    subjects = [
        ('헌법', 'subject_0'),
        ('언어논리', 'subject_1'),
        ('자료해석', 'subject_2'),
        ('상황판단', 'subject_3'),
        ('PSAT 평균', 'average'),
    ]

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_dict = get_student_dict(request.user, exam_list)
    for obj in page_obj:
        obj.student = student_dict.get(obj, None)
        # for idx in range(4):
        #     setattr(obj, f'score_{idx}', getattr(obj.student.score, f'subject_{idx}'))
        answer_student_counts = models.PredictAnswer.objects.filter(student=obj.student).count()
        obj.answer_all_confirmed = answer_student_counts == 145

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        subjects=subjects,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_psat/predict/predict_list.html', context)
