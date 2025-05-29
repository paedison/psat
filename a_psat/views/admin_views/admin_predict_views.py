from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import models, forms
from a_psat.utils import predict_utils
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_context
from ..normal_views import predict_views


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

    sub_title = predict_utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    predict_psat_list = models.PredictPsat.objects.select_related('psat')
    predict_psat_context = get_paginator_context(predict_psat_list, page_number)
    context = update_context_data(config=config, sub_title=sub_title, predict_psat_context=predict_psat_context)

    if view_type == 'predict_psat_list':
        return render(request, f'a_psat/admin_predict_list.html#study_category_list', context)  # noqa
    return render(request, 'a_psat/admin_predict_list.html', context)


@admin_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    psat = get_object_or_404(models.Psat, pk=pk)
    context = update_context_data(config=config, psat=psat)

    if view_type == 'problem_list':
        qs_problem = models.Problem.objects.get_filtered_qs_by_psat(psat)
        context = update_context_data(context, problem_context=get_paginator_context(qs_problem, page_number))
        return render(request, 'a_psat/problem_list_content.html', context)

    if hasattr(psat, 'predict_psat'):
        config.url_admin_predict_update = reverse_lazy('psat:admin-predict-update', args=[pk])
        context = update_context_data(
            context, predict_psat=psat.predict_psat, icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH)

        if view_type == 'total_statistics_list':
            statistics_context = predict_utils.get_admin_statistics_context(psat, page_number)
            context = update_context_data(context, statistics_data=statistics_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)
        if view_type == 'filtered_statistics_list':
            statistics_context = predict_utils.get_admin_statistics_context(psat, page_number)
            context = update_context_data(context, statistics_data=statistics_context['filtered'])
            return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)
        if view_type == 'total_catalog_list':
            catalog_context = predict_utils.get_admin_catalog_context(psat, page_number)
            context = update_context_data(context, catalog_data=catalog_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'filtered_catalog_list':
            catalog_context = predict_utils.get_admin_catalog_context(psat, page_number)
            context = update_context_data(context, catalog_data=catalog_context['filtered'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'student_search':
            searched_student = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(
                psat).filter(name=student_name)
            catalog_context = predict_utils.get_admin_catalog_context(psat, page_number, searched_student)
            context = update_context_data(context, catalog_data=catalog_context['total'])
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'answer_list':
            answer_context = predict_utils.get_admin_answer_context(psat, subject, page_number)
            context = update_context_data(context, answer_data=answer_context[subject])
            return render(request, 'a_psat/snippets/admin_detail_predict_answer_analysis.html', context)

        subject_vars = predict_utils.get_subject_vars(psat, True)
        qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat(psat)
        qs_problem = models.Problem.objects.get_filtered_qs_by_psat(psat)

        context = update_context_data(
            context,
            statistics_context=predict_utils.get_admin_statistics_context(psat),
            catalog_context=predict_utils.get_admin_catalog_context(psat),
            answer_context=predict_utils.get_admin_answer_context(psat),
            answer_predict_context=predict_utils.get_admin_only_answer_context(qs_answer_count, subject_vars),
            answer_official_context=predict_utils.get_admin_only_answer_context(qs_problem, subject_vars),
            problem_context=get_paginator_context(qs_problem),
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

            predict_utils.create_admin_answer_count_model_instances(original_psat)
            predict_utils.create_admin_statistics_model_instances(original_psat)
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
        is_updated, message = predict_utils.update_admin_problem_model_for_answer_official(psat, form, file)
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        model_dict = {'answer': models.PredictAnswer, 'score': models.PredictScore}
        is_updated, message = predict_utils.update_admin_scores(psat, qs_student, model_dict)
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        model_dict = {'all': models.PredictRankTotal, 'department': models.PredictRankCategory}
        is_updated, message = predict_utils.update_admin_ranks(psat, qs_student, model_dict)
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        is_updated, message = predict_utils.update_admin_statistics(psat)
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        model_dict = {
            'answer': models.PredictAnswer,
            'all': models.PredictAnswerCount,
            'top': models.PredictAnswerCountTopRank,
            'mid': models.PredictAnswerCountMidRank,
            'low': models.PredictAnswerCountLowRank,
        }
        is_updated, message = predict_utils.update_admin_answer_counts(model_dict)
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
    statistics_context = predict_utils.get_admin_statistics_context(psat, 1, 200)
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
    answer_context = predict_utils.get_admin_answer_context(psat, None, 1, 1000)
    context = update_context_data(psat=psat, answer_context=answer_context)
    return render(request, 'a_psat/admin_print_answers.html', context)


@admin_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return predict_utils.get_admin_statistics_response(psat)


@admin_required
def predict_prime_id_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return predict_utils.get_admin_prime_id_response(psat)


@admin_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return predict_utils.get_admin_catalog_response(psat)


@admin_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    psat = get_object_or_404(models.Psat, pk=pk)
    return predict_utils.get_admin_answer_response(psat)
