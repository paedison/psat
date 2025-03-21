from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import only_staff_allowed, admin_required
from common.utils import HtmxHttpRequest, update_context_data
from . import admin_utils, result_views
from .. import models, utils, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임Leet'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:admin-list')
    url_leet_create = reverse_lazy('prime_leet:admin-leet-create')


@only_staff_allowed()
def list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Leet.objects.all()
    config = ViewConfiguration()
    exam_page_obj, exam_page_range = utils.get_paginator_data(exam_list, page_number)

    student_list = models.ResultRegistry.objects.select_related('user', 'student').order_by('id')
    student_page_obj, student_page_range = utils.get_paginator_data(student_list, page_number)

    context = update_context_data(
        config=config,
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
    )
    if view_type == 'student_list':
        return render(request, 'a_prime_leet/admin_list.html#student_list', context)
    return render(request, 'a_prime_leet/admin_list.html', context)


@only_staff_allowed()
def detail_view(request: HtmxHttpRequest, model_type: str, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')
    score_type = '결과' if model_type == 'result' else '예측'

    leet = get_object_or_404(models.Leet, pk=pk)
    answer_tab = admin_utils.get_answer_tab()

    config.model_type = model_type
    config.url_admin_update = reverse_lazy('prime_leet:admin-update', args=[model_type, leet.id])
    config.url_statistics_print = reverse_lazy('prime_leet:admin-statistics-print', args=[model_type, leet.id])
    config.url_catalog_print = reverse_lazy('prime_leet:admin-catalog-print', args=[model_type, leet.id])
    config.url_answers_print = reverse_lazy('prime_leet:admin-answers-print', args=[model_type, leet.id])
    config.url_export_statistics_excel = reverse_lazy('prime_leet:admin-export-statistics-excel', args=[model_type, leet.id])
    config.url_export_catalog_excel = reverse_lazy('prime_leet:admin-export-catalog-excel', args=[model_type, leet.id])
    config.url_export_answers_excel = reverse_lazy('prime_leet:admin-export-answers-excel', args=[model_type, leet.id])
    config.url_export_statistics_pdf = reverse_lazy('prime_leet:admin-export-statistics-pdf', args=[model_type, leet.id])

    context = update_context_data(
        config=config, leet=leet, answer_tab=answer_tab, score_type=score_type,
        icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH,
    )
    data_statistics = admin_utils.get_qs_statistics(leet, model_type)
    student_list = admin_utils.get_student_list(leet, model_type)
    registry_list = None
    if model_type == 'result':
        registry_list = models.ResultRegistry.objects.prime_leet_registry_list_by_leet(leet)
    qs_answer_count = admin_utils.get_qs_answer_count(leet, model_type, subject)

    if view_type == 'statistics_list':
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_statistics.html', context)
    if view_type == 'catalog_list':
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_catalog.html', context)
    if view_type == 'student_search':
        searched_student = student_list.filter(name=student_name)
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_catalog.html', context)
    if view_type == 'registry_list':
        registry_page_obj, registry_page_range = utils.get_paginator_data(registry_list, page_number)
        context = update_context_data(
            context, registry_page_obj=registry_page_obj, registry_page_range=registry_page_range)
        return render(request, 'a_prime_leet/snippets/admin_detail_registry.html', context)
    if view_type == 'answer_list':
        subject_vars = admin_utils.get_subject_vars()
        subject_idx = subject_vars[subject][2]
        answers_page_obj_group, answers_page_range_group = (
            admin_utils.get_answer_page_data(qs_answer_count, page_number, model_type))
        context = update_context_data(
            context,
            tab=answer_tab[subject_idx],
            answers=answers_page_obj_group[subject],
            answers_page_range=answers_page_range_group[subject],
        )
        return render(request, 'a_prime_leet/snippets/admin_detail_answer.html', context)

    statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
    registry_page_obj, registry_page_range = utils.get_paginator_data(registry_list, page_number)
    answers_page_obj_group, answers_page_range_group = (
        admin_utils.get_answer_page_data(qs_answer_count, page_number, model_type))

    context = update_context_data(
        context,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
        registry_page_obj=registry_page_obj, registry_page_range=registry_page_range,
    )
    return render(request, 'a_prime_leet/admin_detail.html', context)


@only_staff_allowed()
def result_student_detail_view(request: HtmxHttpRequest, pk: int):
    student = get_object_or_404(models.ResultStudent, pk=pk)
    return result_views.detail_view(request, student.leet.pk, student=student, is_for_print=True)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, model_type: str, pk: int):
    view_type = request.headers.get('View-Type', '')
    leet = get_object_or_404(models.Leet, pk=pk)

    next_url = leet.get_admin_detail_url(model_type)
    context = update_context_data(next_url=next_url)
    qs_student = admin_utils.get_qs_student(leet, model_type)
    upload_form = forms.UploadFileForm(request.POST, request.FILES)
    file = request.FILES.get('file')

    if view_type == 'answer_official':
        is_updated, message = admin_utils.update_problem_model_for_answer_official(leet, upload_form, file)
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_student':
        is_updated, message = admin_utils.update_result_answer_model_for_answer_student(leet, upload_form, file)
        context = update_context_data(context, header='제출 답안 업데이트', is_updated=is_updated, message=message)

    if view_type == 'raw_score':
        is_updated, message = admin_utils.update_raw_scores(qs_student, model_type)
        context = update_context_data(context, header='원점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        score_model = models.ResultScore if model_type == 'result' else models.PredictScore
        is_updated, message = admin_utils.update_scores(leet, score_model)
        context = update_context_data(context, header='표준점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = admin_utils.update_ranks(qs_student, model_type)
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics, filtered_data_statistics = admin_utils.get_data_statistics(leet, model_type)
        is_updated, message = admin_utils.update_statistics(
            leet, data_statistics, filtered_data_statistics, model_type)
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = admin_utils.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_prime_leet/snippets/admin_modal_update.html', context)


@only_staff_allowed()
def leet_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.LeetForm(request.POST, request.FILES)
        if form.is_valid():
            leet, _ = models.Leet.objects.get_or_create(
                year=form.cleaned_data['year'], exam=form.cleaned_data['exam'],
                round=form.cleaned_data['round'], name=form.cleaned_data['name'],
            )
            leet.is_active = True
            leet.abbr = form.cleaned_data['abbr']
            leet.page_opened_at = form.cleaned_data['page_opened_at']
            leet.exam_started_at = form.cleaned_data['exam_started_at']
            leet.exam_finished_at = form.cleaned_data['exam_finished_at']
            leet.answer_predict_opened_at = form.cleaned_data['answer_predict_opened_at']
            leet.answer_official_opened_at = form.cleaned_data['answer_official_opened_at']
            leet.save()

            admin_utils.create_default_problems(leet)
            admin_utils.create_default_statistics(leet)
            admin_utils.create_default_statistics(leet, 'predict')

            problems = models.Problem.objects.filter(leet=leet).order_by('id')
            admin_utils.create_default_answer_counts(problems, 'result')
            admin_utils.create_default_answer_counts(problems, 'predict')

            response = redirect('prime_leet:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_prime_leet/admin_form.html', context)

    form = forms.LeetForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_prime_leet/admin_form.html', context)


@admin_required
def leet_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.LeetActiveForm(request.POST)
        if form.is_valid():
            leet = get_object_or_404(models.Leet, pk=pk)
            is_active = form.cleaned_data['is_active']
            leet.is_active = is_active
            leet.save()
    return HttpResponse('')


@only_staff_allowed()
def statistics_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    data_statistics, filtered_data_statistics = admin_utils.get_data_statistics(leet, model_type)
    context = update_context_data(
        leet=leet, model_type=model_type,
        data_statistics=data_statistics, filtered_data_statistics=filtered_data_statistics,
    )
    return render(request, 'a_prime_leet/admin_print_statistics.html', context)


@only_staff_allowed()
def catalog_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    student_list = admin_utils.get_student_list(leet, model_type)
    context = update_context_data(leet=leet, student_list=student_list)
    return render(request, 'a_prime_leet/admin_print_catalog.html', context)


@only_staff_allowed()
def answers_print_view(request: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    qs_answer_count = admin_utils.get_qs_answer_count(leet, model_type).order_by('id')
    answers_page_obj_group, answers_page_range_group = (
        admin_utils.get_answer_page_data(qs_answer_count, 1, model_type, 1000))
    context = update_context_data(leet=leet, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_prime_leet/admin_print_answers.html', context)


@only_staff_allowed()
def export_statistics_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return admin_utils.get_statistics_response(leet, model_type)


@only_staff_allowed()
def export_catalog_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return admin_utils.get_catalog_response(leet, model_type)


@only_staff_allowed()
def export_answers_excel_view(_: HtmxHttpRequest, model_type: str, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return admin_utils.get_answer_response(leet, model_type)
