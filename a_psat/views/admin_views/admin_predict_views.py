from collections import defaultdict

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import models, forms
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_data
from ..normal_views import predict_views
from ...utils import admin_view_utils


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
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    page_number = request.GET.get('page', '1')

    sub_title = admin_view_utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    predict_exam_list = models.PredictPsat.objects.select_related('psat')
    context = update_context_data(config=config, sub_title=sub_title)
    template_name = 'a_psat/admin_predict_list.html'

    if view_type == 'predict_exam_list':
        page_obj, page_range = get_paginator_data(predict_exam_list, page_number)
        context = update_context_data(context, page_obj=page_obj, page_range=page_range)
        return render(request, f'{template_name}#study_category_list', context)

    page_obj, page_range = get_paginator_data(predict_exam_list, page_number)
    context = update_context_data(context, page_obj=page_obj, page_range=page_range)

    return render(request, 'a_psat/admin_predict_list.html', context)


@admin_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    psat = get_object_or_404(models.Psat, pk=pk)
    qs_problem = models.Problem.objects.get_filtered_qs_by_psat(psat)
    page_obj, page_range = get_paginator_data(qs_problem, page_number)

    problem_dict = defaultdict(list)
    for qs_p in qs_problem.order_by('id'):
        problem_dict[qs_p.subject].append(qs_p)

    sub_list = admin_view_utils.get_sub_list(psat)
    answer_official_list = [problem_dict[sub] for sub in sub_list]

    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat(psat)
    answer_count_dict = defaultdict(list)
    for qs_ac in qs_answer_count.order_by('id'):
        answer_count_dict[qs_ac.sub].append(qs_ac)
    answer_predict_list = [answer_count_dict[sub] for sub in sub_list]

    context = update_context_data(
        config=config, psat=psat, subjects=sub_list,
        answer_official_list=answer_official_list,
        answer_predict_list=answer_predict_list,
        page_obj=page_obj, page_range=page_range,
    )

    if view_type == 'problem_list':
        return render(request, 'a_psat/problem_list_content.html', context)

    predict_psat = admin_view_utils.get_predict_psat(psat)
    if predict_psat:
        config.url_admin_predict_update = reverse_lazy('psat:admin-predict-update', args=[pk])
        context = update_context_data(
            context, predict_psat=predict_psat, icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH)

        if view_type == 'total_statistics_list':
            statistics_context = admin_view_utils.get_predict_statistics_context(psat, page_number)
            context = update_context_data(context, statistics_data=statistics_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)
        if view_type == 'filtered_statistics_list':
            statistics_context = admin_view_utils.get_predict_statistics_context(psat, page_number)
            context = update_context_data(context, statistics_data=statistics_context['filtered'])
            return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)
        if view_type == 'total_catalog_list':
            catalog_context = admin_view_utils.get_predict_catalog_context(psat, page_number)
            context = update_context_data(context, catalog_data=catalog_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'filtered_catalog_list':
            catalog_context = admin_view_utils.get_predict_catalog_context(psat, page_number)
            context = update_context_data(context, catalog_data=catalog_context['filtered'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'student_search':
            searched_student = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(
                psat).filter(name=student_name)
            catalog_context = admin_view_utils.get_predict_catalog_context(psat, page_number, searched_student)
            context = update_context_data(context, catalog_data=catalog_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'answer_list':
            answer_context = admin_view_utils.get_predict_answer_context(psat, subject, page_number)
            context = update_context_data(context, answer_data=answer_context[subject])
            return render(request, 'a_psat/snippets/admin_detail_predict_answer_analysis.html', context)

        statistics_context = admin_view_utils.get_predict_statistics_context(psat)
        catalog_context = admin_view_utils.get_predict_catalog_context(psat)
        answer_context = admin_view_utils.get_predict_answer_context(psat)
        context = update_context_data(
            context, statistics_context=statistics_context,
            catalog_context=catalog_context, answer_context=answer_context
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
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            original_psat = models.Psat.objects.get(year=year, exam=exam)

            new_predict_psat, _ = models.PredictPsat.objects.get_or_create(psat=original_psat)
            new_predict_psat.is_active = True
            new_predict_psat.page_opened_at = form.cleaned_data['page_opened_at']
            new_predict_psat.exam_started_at = form.cleaned_data['exam_started_at']
            new_predict_psat.exam_finished_at = form.cleaned_data['exam_finished_at']
            new_predict_psat.answer_predict_opened_at = form.cleaned_data['answer_predict_opened_at']
            new_predict_psat.answer_official_opened_at = form.cleaned_data['answer_official_opened_at']
            new_predict_psat.predict_closed_at = form.cleaned_data['predict_closed_at']
            new_predict_psat.save()

            admin_view_utils.create_predict_answer_count_model_instances(original_psat)
            admin_view_utils.create_predict_statistics_model_instances(original_psat)
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
    view_type = request.headers.get('View-Type', '')

    next_url = psat.get_admin_predict_detail_url()
    context = update_context_data(next_url=next_url)
    qs_student = models.PredictStudent.objects.get_filtered_qs_by_psat(psat)

    if view_type == 'answer_official':
        form = forms.UploadFileForm(request.POST, request.FILES)
        file = request.FILES.get('file')
        is_updated, message = admin_view_utils.update_problem_model_for_answer_official(psat, form, file)
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        model_dict = {'answer': models.PredictAnswer, 'score': models.PredictScore}
        is_updated, message = admin_view_utils.update_predict_scores(psat, qs_student, model_dict)
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        model_dict = {'total': models.PredictRankTotal, 'department': models.PredictRankCategory}
        is_updated, message = admin_view_utils.update_predict_ranks(psat, qs_student, model_dict)
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        is_updated, message = admin_view_utils.update_predict_statistics(psat)
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        model_dict = {
            'answer': models.PredictAnswer,
            'all': models.PredictAnswerCount,
            'top': models.PredictAnswerCountTopRank,
            'mid': models.PredictAnswerCountMidRank,
            'low': models.PredictAnswerCountLowRank,
        }
        is_updated, message = admin_view_utils.update_predict_answer_counts(model_dict)
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def predict_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.PredictStudent = models.PredictStudent.objects.filter(pk=pk).first()
    if student:
        student = models.PredictStudent.objects.get_filtered_qs_by_psat_and_user_with_answer_count(student.user, student.psat)
        return predict_views.predict_detail_view(request, student.psat.id, student=student)
    return redirect('psat:admin-predict-list')


@admin_required
def predict_statistics_print(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    statistics_context = admin_view_utils.get_predict_statistics_context(psat, 1, 200)
    context = update_context_data(psat=psat, statistics_context=statistics_context)
    return render(request, 'a_psat/admin_print_statistics.html', context)


@admin_required
def predict_catalog_print(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    student_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    context = update_context_data(psat=psat, student_list=student_list)
    return render(request, 'a_psat/admin_print_catalog.html', context)


@admin_required
def predict_answer_print(request: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    answer_context = admin_view_utils.get_predict_answer_context(psat, None, 1, 1000)
    context = update_context_data(psat=psat, answer_context=answer_context)
    return render(request, 'a_psat/admin_print_answers.html', context)


@admin_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return admin_view_utils.get_predict_statistics_response(psat)


@admin_required
def predict_prime_id_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return admin_view_utils.get_predict_prime_id_response(psat)


@admin_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return admin_view_utils.get_predict_catalog_response(psat)


@admin_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return admin_view_utils.get_predict_answer_response(psat)
