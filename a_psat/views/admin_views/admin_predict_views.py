from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import models, forms
from a_psat.utils.predict.admin_utils import *
from a_psat.utils.variables import RequestContext, SubjectVariants
from a_psat.views.normal_views import predict_views
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_context


class ViewConfiguration:
    menu = menu_eng = 'psat_admin'
    menu_kor = 'PSAT 관리자'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격 예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-predict-list')
    url_problem_update = reverse_lazy('psat:admin-official-update')

    url_predict_create = reverse_lazy('psat:admin-predict-create')


@admin_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    request_ctx = RequestContext(_request=request)
    predict_psat_list = models.PredictPsat.objects.select_related('psat')
    predict_psat_context = get_paginator_context(predict_psat_list, request_ctx.page_number)
    context = update_context_data(config=config, predict_psat_context=predict_psat_context)

    if request_ctx.view_type == 'predict_psat_list':
        return render(request, f'a_psat/admin_predict_list.html#predict_psat_list', context)  # noqa
    return render(request, 'a_psat/admin_predict_list.html', context)


def prepare_detail_context(pk):
    config = ViewConfiguration()
    config.url_admin_predict_update = reverse_lazy('psat:admin-predict-update', args=[pk])
    psat = get_object_or_404(models.Psat.objects.select_related('predict_psat'), pk=pk)
    subject_variants = SubjectVariants(_psat=psat)

    context = update_context_data(
        config=config, psat=psat, predict_psat=psat.predict_psat,
        icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH,

        subject_vars=subject_variants.subject_vars,
        subject_fields_avg_first=subject_variants.subject_fields_avg_first,
        sub_list=subject_variants.sub_list,
    )
    return psat, context


@admin_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    psat, context = prepare_detail_context(pk)

    qs_problem = models.Problem.objects.filtered_problem_by_psat(psat)
    qs_answer_count = models.PredictAnswerCount.objects.predict_filtered_by_psat(psat)
    context = update_context_data(context, qs_problem=qs_problem, qs_answer_count=qs_answer_count)

    detail_ctx = AdminDetailContext(request=request, _context=context)

    view_type = request.headers.get('View-Type', '')
    if view_type == 'problem_list':
        context = update_context_data(context, problem_context=detail_ctx.get_admin_problem_context())
        return render(request, 'a_psat/problem_list_content.html', context)

    if view_type == 'total_statistics_list':
        statistics_data = detail_ctx.get_admin_statistics_context()['total']
        context = update_context_data(context, statistics_data=statistics_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)

    if view_type == 'filtered_statistics_list':
        statistics_data = detail_ctx.get_admin_statistics_context()['filtered']
        context = update_context_data(context, statistics_data=statistics_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)

    if view_type == 'total_catalog_list':
        catalog_data = detail_ctx.get_admin_catalog_context()['total']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)

    if view_type == 'filtered_catalog_list':
        catalog_data = detail_ctx.get_admin_catalog_context()['filtered']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)

    if view_type == 'student_search':
        catalog_data = detail_ctx.get_admin_catalog_context()['total']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)

    if view_type == 'answer_list':
        answer_data = detail_ctx.get_admin_answer_context_for_sub()
        context = update_context_data(context, answer_data=answer_data)
        return render(request, 'a_psat/snippets/admin_detail_predict_answer_analysis.html', context)

    context = update_context_data(
        context,
        problem_context=detail_ctx.get_admin_problem_context(),
        answer_predict_context=detail_ctx.get_admin_answer_predict_context(),
        answer_official_context=detail_ctx.get_admin_answer_official_context(),
        statistics_context=detail_ctx.get_admin_statistics_context(),
        catalog_context=detail_ctx.get_admin_catalog_context(),
        answer_context=detail_ctx.get_admin_answer_context(),
    )
    return render(request, 'a_psat/admin_predict_detail.html', context)


@admin_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 합격 예측 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PredictPsatForm(request.POST, request.FILES)
        if form.is_valid():
            AdminCreateContext(form=form).process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.PredictPsatForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def predict_update_view(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    context = update_context_data(next_url=psat.get_admin_predict_detail_url())
    update_ctx = AdminUpdateContext(request=request, psat=psat)

    view_type = request.headers.get('View-Type', '')
    if view_type == 'answer_official':
        is_updated, message = update_ctx.update_problem_model_for_answer_official()
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = update_ctx.update_scores()
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = update_ctx.update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        is_updated, message = update_ctx.update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = update_ctx.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def predict_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.PredictStudent = models.PredictStudent.objects.filter(pk=pk).first()
    if student:
        student = models.PredictStudent.objects.psat_student_with_answer_count(student.user, student.psat)
        return predict_views.predict_detail_view(request, student.psat.id, student=student)
    return redirect('psat:admin-predict-list')


@admin_required
def predict_statistics_print(request: HtmxHttpRequest, pk: int):
    psat, context = prepare_detail_context(pk)
    detail_ctx = AdminDetailContext(request=request, _context=context)
    context = update_context_data(context, statistics_context=detail_ctx.get_admin_statistics_context(200))
    return render(request, 'a_psat/admin_print_statistics.html', context)


@admin_required
def predict_catalog_print(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    student_list = models.PredictStudent.objects.filtered_student_by_psat(psat)
    context = update_context_data(psat=psat, student_list=student_list)
    return render(request, 'a_psat/admin_print_catalog.html', context)


@admin_required
def predict_answer_print(request: HtmxHttpRequest, pk: int):
    psat, context = prepare_detail_context(pk)
    detail_ctx = AdminDetailContext(request=request, _context=context)
    context = update_context_data(context, answer_context=detail_ctx.get_admin_answer_context(per_page=1000))
    return render(request, 'a_psat/admin_print_answers.html', context)


@admin_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return AdminExportExcelContext(psat=psat).get_statistics_response()


@admin_required
def predict_prime_id_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return AdminExportExcelContext(psat=psat).get_prime_id_response()


@admin_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return AdminExportExcelContext(psat=psat).get_catalog_response()


@admin_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return AdminExportExcelContext(psat=psat).get_answer_response()
