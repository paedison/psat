from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django_htmx.http import retarget

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .prime_police_views import get_detail_context
from .. import forms
from .. import models

BASE_INFO = {
    'info': {'menu': 'score', 'menu_self': 'prime'},
    'title': 'Score',
    'sub_title': '74기 대비 프라임 경위공채 전국모의고사',
    'icon_menu': icon_set_new.ICON_MENU['score'],
    'icon_subject': icon_set_new.ICON_SUBJECT,
}

EXAM_YEAR = 2025
EXAM_ROUND = 1
EXAM_INFO = {'year': EXAM_YEAR, 'round': EXAM_ROUND}
REGISTERED_STUDENT_INFO = {'student__year': EXAM_YEAR, 'student__round': EXAM_ROUND}
EXAM_URL_KWARGS = {'exam_year': EXAM_YEAR, 'exam_round': EXAM_ROUND}


def get_registered_student(request):
    return models.PrimePoliceRegisteredStudent.objects.filter(
        user=request.user, **REGISTERED_STUDENT_INFO).first()


@login_not_required
def index_view(request: HtmxHttpRequest):
    if request.user.is_authenticated:
        registered_student = get_registered_student(request=request)
        if registered_student:
            return redirect('score:temporary-result')
    context = update_context_data(**BASE_INFO)
    return render(request, 'a_score/prime_police/temporary/police_index.html', context)


def result_view(request: HtmxHttpRequest):
    registered_student = get_registered_student(request=request)
    if not registered_student:
        return redirect('score:temporary-index')
    context = get_detail_context(request=request, **EXAM_URL_KWARGS)
    context.update(BASE_INFO)
    return render(request, 'a_score/prime_police/temporary/police_result.html', context)


def student_register_view(request: HtmxHttpRequest):
    registered_student = get_registered_student(request=request)
    if registered_student:
        return redirect('score:temporary-result')

    exam = models.PrimePoliceExam.objects.get(**EXAM_INFO)
    context = update_context_data(**BASE_INFO, exam=exam)

    # student_create
    form_class = forms.PrimePoliceStudentForm
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            target_student = models.PrimePoliceStudent.objects.filter(
                **EXAM_INFO, serial=serial, name=name, password=password).first()
            if target_student:
                registered_student, _ = models.PrimePoliceRegisteredStudent.objects.get_or_create(
                    user=request.user, student=target_student)
                next_url = reverse('score:temporary-result')
                response = redirect(next_url)
                response.headers['HX-Replace-Url'] = next_url
                return response
            else:
                context = update_context_data(context, form=form, no_student=True)
                response = render(request, 'a_score/prime_police/temporary/create_info_student.html', context)
                return retarget(response, '#infoStudent')
        else:
            context = update_context_data(context, form=form)
            response = render(request, 'a_score/prime_police/temporary/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        context = update_context_data(context, form=form_class())
        return render(request, 'a_score/prime_police/temporary/police_student_register.html', context)
