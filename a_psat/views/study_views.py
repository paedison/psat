from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'study'
    submenu_kor = '스터디'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_list = reverse_lazy('psat:predict-list')


def get_student_dict(user, curriculum_list) -> dict:
    if user.is_authenticated:
        students = (
            models.StudyStudent.objects.filter(user=user, curriculum__in=curriculum_list)
            .select_related('curriculum', 'user', 'score', 'rank').order_by('id')
        )
        return {student.curriculum: student for student in students}
    return {}


@login_not_required
def list_view(request: HtmxHttpRequest):
    if not request.user.is_authenticated:
        return redirect('psat:study-register')

    config = ViewConfiguration()
    student = models.StudyStudent.objects.filter(user=request.user)
    curriculum_list = models.StudyCurriculum.objects.filter(students__in=student)

    page_number = request.GET.get('page', 1)
    paginator = Paginator(curriculum_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_dict = get_student_dict(request.user, curriculum_list)
    for obj in page_obj:
        obj.student = student_dict.get(obj, None)
        if obj.student:
            pass

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_psat/study_list.html', context)


def register_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    psat = utils.get_psat(pk)
    if not psat or not psat.predict_psat or not psat.predict_psat.is_active:
        return redirect('prime:predict-list')

    exam_vars = ExamVars(psat.predict_psat)
    form = exam_vars.student_form()
    context = update_context_data(exam_vars=exam_vars, exam=psat, form=form)

    if view_type == 'department':
        unit = request.GET.get('unit')
        categories = exam_vars.get_qs_category(unit)
        context = update_context_data(context, categories=categories)
        return render(request, 'a_psat/snippets/predict_department_list.html', context)

    if request.method == 'POST':
        form = exam_vars.student_form(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.psat = psat
            student.save()
            exam_vars.rank_total_model.objects.get_or_create(student=student)
            exam_vars.rank_category_model.objects.get_or_create(student=student)
            exam_vars.score_model.objects.get_or_create(student=student)
            context = update_context_data(context, user_verified=True)

    return render(request, 'a_psat/snippets/modal_predict_student_register.html#student_info', context)
