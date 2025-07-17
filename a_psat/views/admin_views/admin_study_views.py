from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from a_psat import models, forms
from a_psat.utils.study_utils import *
from a_psat.utils.variables import RequestContext
from a_psat.views.normal_views.study_views import study_detail_view as normal_study_detail_view
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    menu = menu_eng = 'psat_admin'
    menu_kor = 'PSAT 관리자'
    submenu = submenu_eng = 'study'
    submenu_kor = '스터디'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-study-list')
    url_study_category_upload = reverse_lazy('psat:admin-study-category-upload')
    url_study_category_create = reverse_lazy('psat:admin-study-category-create')

    url_study_curriculum_upload = reverse_lazy('psat:admin-study-curriculum-upload')
    url_study_answer_upload = reverse_lazy('psat:admin-study-answer-upload')
    url_study_organization_create = reverse_lazy('psat:admin-study-organization-create')
    url_study_curriculum_create = reverse_lazy('psat:admin-study-curriculum-create')
    url_study_student_create = reverse_lazy('psat:admin-study-student-create')


@admin_required
def study_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    request_context = RequestContext(_request=request)
    list_context = AdminListContext(_request=request)
    context = update_context_data(config=config, sub_title=request_context.get_sub_title())
    template_name = 'a_psat/admin_study_list.html'

    if request_context.view_type == 'study_category_list':
        context = update_context_data(context, category_context=list_context.get_list_context(True))
        return render(request, f'{template_name}#study_category_list', context)
    elif request_context.view_type == 'study_curriculum_list':
        context = update_context_data(context, curriculum_context=list_context.get_list_context(False))
        return render(request, f'{template_name}#study_curriculum_list', context)

    context = update_context_data(
        context,
        category_context=list_context.get_list_context(True),
        curriculum_context=list_context.get_list_context(False),
    )
    return render(request, 'a_psat/admin_study_list.html', context)


@admin_required
def study_detail_view(request: HtmxHttpRequest, study_type: str, pk: int):
    config = ViewConfiguration()
    config.study_type = study_type

    if study_type == 'category':
        curriculum = None
        category = get_object_or_404(models.StudyCategory, pk=pk)
        config.url_study_update = reverse_lazy('psat:admin-study-category-update', args=[category.pk])
        config.url_export_statistics_excel = category.get_admin_study_statistics_excel_url()
        config.url_export_catalog_excel = category.get_admin_study_catalog_excel_url()
        config.url_export_answers_excel = category.get_admin_study_answer_excel_url()
        page_title = category.full_reference
    else:
        curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)
        category = curriculum.category
        config.url_study_update = reverse_lazy('psat:admin-study-curriculum-update', args=[curriculum.pk])
        config.url_export_statistics_excel = curriculum.get_admin_study_statistics_excel_url()
        config.url_export_catalog_excel = curriculum.get_admin_study_catalog_excel_url()
        config.url_export_answers_excel = curriculum.get_admin_study_answer_excel_url()
        page_title = curriculum.full_reference

    detail_context = AdminDetailContext(request=request, category=category, curriculum=curriculum)

    context = update_context_data(
        config=config, category=category, curriculum=curriculum, study_rounds=detail_context.study_rounds,
        page_title=page_title, icon_image=icon_set_new.ICON_IMAGE, icon_search=icon_set_new.ICON_SEARCH,
    )

    view_type = request.headers.get('View-Type', '')
    if view_type == 'lecture_list':
        context = update_context_data(context, lecture_context=detail_context.lecture_context)
        return render(request, 'a_psat/snippets/study_detail_lecture.html', context)
    if view_type == 'statistics_list':
        context = update_context_data(
            context, category_stat=detail_context.category_stat, statistics_context=detail_context.statistics_context)
        return render(request, 'a_psat/snippets/admin_detail_study_statistics.html', context)
    if view_type == 'catalog_list':
        context = update_context_data(context, catalog_context=detail_context.catalog_context)
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'student_search':
        context = update_context_data(context, catalog_context=detail_context.catalog_context)
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'answer_list':
        context = update_context_data(context, answer_context=detail_context.answer_context)
        return render(request, 'a_psat/snippets/admin_detail_study_answer_analysis.html', context)
    if view_type == 'problem_list':
        context = update_context_data(context, problem_context=detail_context.problem_context)
        return render(request, 'a_psat/snippets/admin_detail_study_problem_list.html', context)

    context = update_context_data(
        context,
        schedules=detail_context.qs_schedule,
        lecture_context=detail_context.lecture_context,
        category_stat=detail_context.category_stat,
        statistics_context=detail_context.statistics_context,
        catalog_context=detail_context.catalog_context,
        answer_context=detail_context.answer_context,
        problem_context=detail_context.problem_context,
    )
    return render(request, f'a_psat/admin_study_detail.html', context)


@admin_required
def study_create_category_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 카테고리 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            season = form.cleaned_data['season']
            study_type = form.cleaned_data['study_type']
            name = form.cleaned_data['name']
            category_round = form.cleaned_data['category_round']

            category, _ = models.StudyCategory.objects.get_or_create(season=season, study_type=study_type)
            category.name = name
            category.save()

            for rnd in range(1, category_round + 1):
                models.StudyPsat.objects.get_or_create(category=category, round=rnd)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCategoryForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_create_curriculum_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyCurriculumForm(request.POST, request.FILES)
        create_context = AdminCreateCurriculumContext(request=request, form=form)

        view_type = request.headers.get('View-Type', '')
        if view_type == 'category':
            context = update_context_data(context, form=create_context.get_category_form())
            return render(request, 'a_psat/admin_form.html#form_field', context)  # noqa
        if create_context.form.is_valid():
            create_context.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=create_context.form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCurriculumForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_create_organization_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 교육기관 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyOrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyOrganizationForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_create_student_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 학생 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyStudentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            create_context = AdminCreateStudentContext(student=student)
            create_context.create_default_result_instances()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyStudentCreateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_upload_category_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 카테고리 자료 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_context = AdminUploadCategoryContext(request=request)
            upload_context.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_upload_curriculum_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 자료 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_context = AdminUploadCurriculumContext(request=request)
            upload_context.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_upload_answer_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 답안 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyAnswerForm(request.POST, request.FILES)
        if form.is_valid():
            study_curriculum = form.cleaned_data['curriculum']
            upload_context = AdminUploadAnswerContext(request=request, curriculum=study_curriculum)
            upload_context.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyAnswerForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_update_category_view(request: HtmxHttpRequest, pk: int):
    category = get_object_or_404(models.StudyCategory, pk=pk)
    context = get_study_update_context(request, category)
    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def study_update_curriculum_view(request: HtmxHttpRequest, pk: int):
    curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)
    context = get_study_update_context(request, curriculum)
    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def get_study_update_context(request, update_target):
    update_context = AdminUpdateContext(request=request, update_target=update_target)
    next_url = request.headers.get('HX-Current-URL', request.META.get('HTTP_REFERER', '/'))
    context = update_context_data(next_url=next_url)

    view_type = request.headers.get('View-Type', '')
    if view_type == 'score':
        is_updated, message = update_context.update_scores()
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)
    if view_type == 'rank':
        is_updated, message = update_context.update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)
    if view_type == 'statistics':
        is_updated, message = update_context.update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)
    if view_type == 'answer_count':
        is_updated, message = update_context.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)
    return context


@admin_required
def study_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.StudyStudent = models.StudyStudent.objects.filter(pk=pk).first()
    if student:
        return normal_study_detail_view(request, student.curriculum.id, student=student)


@admin_required
def study_statistics_excel(request: HtmxHttpRequest, study_type: str, pk: int):
    category, curriculum = get_category_and_curriculum(study_type, pk)
    return AdminDetailContext(request=request, category=category, curriculum=curriculum).get_statistics_response()


@admin_required
def study_catalog_excel(request: HtmxHttpRequest, study_type: str, pk: int):
    category, curriculum = get_category_and_curriculum(study_type, pk)
    return AdminDetailContext(request=request, category=category, curriculum=curriculum).get_catalog_response()


@admin_required
def study_answer_excel(request: HtmxHttpRequest, study_type: str, pk: int):
    category, curriculum = get_category_and_curriculum(study_type, pk)
    return AdminDetailContext(request=request, category=category, curriculum=curriculum).get_answer_response()


def get_category_and_curriculum(study_type: str, pk: int):
    if study_type == 'category':
        curriculum = None
        category = get_object_or_404(models.StudyCategory, pk=pk)
    else:
        curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)
        category = curriculum.category
    return category, curriculum
