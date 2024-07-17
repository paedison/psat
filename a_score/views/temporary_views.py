from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .prime_police_views import get_detail_context
from .. import forms
from .. import models

INFO = {'menu': 'score', 'view_type': 'primeScore'}

EXAM_YEAR = 2025
EXAM_ROUND = 1
EXAM_INFO = {'year': EXAM_YEAR, 'round': EXAM_ROUND}
EXAM_URL_KWARGS = {'exam_year': EXAM_YEAR, 'exam_round': EXAM_ROUND}
STUDENT = models.PrimePoliceStudent.objects.filter(**EXAM_INFO).first()


def index_view(request: HtmxHttpRequest):
    info = {'menu': 'score', 'view_type': 'primeScore'}
    registered_student = models.PrimePoliceRegisteredStudent.objects.filter(
        user=request.user).first()
    if registered_student:
        return redirect('score_new:temporary-result')

    context = update_context_data(
        info=info, title='Score',
        sub_title='프라임 경위공채 모의고사 성적표',
        current_time=timezone.now(),
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
    )
    return render(request, 'a_score/prime_police/temporary/police_index.html', context)


def result_view(request: HtmxHttpRequest):
    registered_student = models.PrimePoliceRegisteredStudent.objects.filter(
        user=request.user).first()
    if not registered_student:
        return redirect('score_new:temporary-index')

    context = get_detail_context(request=request, **EXAM_URL_KWARGS)

    return render(request, 'a_score/prime_police/temporary/police_result.html', context)


@login_required
def student_register_view(request: HtmxHttpRequest):
    info = {'menu': 'score', 'view_type': 'primeScore'}

    registered_student = models.PrimePoliceRegisteredStudent.objects.filter(
        user=request.user).first()
    if registered_student:
        return redirect('score_new:temporary-result')

    exam = models.PrimePoliceExam.objects.get(**EXAM_INFO)
    context = update_context_data(
        info=info, exam=exam, current_time=timezone.now(),
        title='Predict',
        sub_title='74기 대비 프라임 경위공채 전국모의고사',
        icon_menu=icon_set_new.ICON_MENU['score'],
    )

    # student_create
    form_class = forms.PrimePoliceStudentForm
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            target_student = models.PrimePoliceStudent.objects.filter(
                **EXAM_INFO, serial=serial, name=name).first()
            if target_student:
                registered_student, _ = models.PrimePoliceRegisteredStudent.objects.get_or_create(
                    user=request.user, student=target_student)
                return redirect('score_new:temporary-result')
            else:
                context = update_context_data(context, form=form, no_student=True)
                return render(request, 'a_score/prime_police/temporary/police_student_register.html', context)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_score/prime_police/temporary/police_student_register.html', context)
    else:
        context = update_context_data(context, form=form_class())
        return render(request, 'a_score/prime_police/temporary/police_student_register.html', context)
