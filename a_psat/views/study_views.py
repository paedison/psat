from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, forms


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
    url_list = reverse_lazy('psat:study-list')

    url_study_student_register = reverse_lazy('psat:study-student-register')


def get_student_dict(user, curriculum_list) -> dict:
    if user.is_authenticated:
        students = (
            models.StudyStudent.objects.filter(user=user, curriculum__in=curriculum_list)
            .select_related('curriculum', 'user').prefetch_related('results').order_by('id')
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


def register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '새 커리큘럼 등록'
    form = forms.StudyStudentRegisterForm()
    context = update_context_data(config=config, title=title, form=form)

    if request.method == 'POST':
        form = forms.StudyStudentRegisterForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organization']
            semester = form.cleaned_data['semester']
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']

            curriculum = models.StudyCurriculum.objects.filter(
                year=timezone.now().year, organization__name=organization, semester=semester).first()
            print(curriculum)
            if curriculum:
                student, _ = models.StudyStudent.objects.get_or_create(
                    curriculum=curriculum, serial=serial, user=request.user)
                if student.name != name:
                    student.name = name
                    student.save()
                return redirect('psat:study-list')
        context = update_context_data(context, form=form)

    return render(request, 'a_psat/admin_form.html', context)
