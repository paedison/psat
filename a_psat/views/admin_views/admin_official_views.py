import itertools
from collections import defaultdict

import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import models, forms, filters
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_data
from ...utils import admin_view_utils


class ViewConfiguration:
    menu = menu_eng = 'psat_admin'
    menu_kor = 'PSAT 관리자'
    submenu = submenu_eng = 'official'
    submenu_kor = '기출문제'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-official-list')
    url_psat_create = reverse_lazy('psat:admin-official-psat-create')
    url_problem_update = reverse_lazy('psat:admin-official-update')


@admin_required
def official_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    page_number = request.GET.get('page', '1')

    sub_title = admin_view_utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    filterset = filters.PsatFilter(data=request.GET, request=request)
    context = update_context_data(config=config, sub_title=sub_title, psat_form=filterset.form)
    template_name = 'a_psat/admin_official_list.html'

    if view_type == 'exam_list':
        page_obj, page_range = get_paginator_data(filterset.qs, page_number)
        admin_view_utils.update_official_problem_count(page_obj)
        context = update_context_data(context, page_obj=page_obj, page_range=page_range)
        return render(request, f'{template_name}#exam_list', context)

    page_obj, page_range = get_paginator_data(filterset.qs, page_number)
    admin_view_utils.update_official_problem_count(page_obj)
    context = update_context_data(context, page_obj=page_obj, page_range=page_range)
    return render(request, 'a_psat/admin_official_list.html', context)


@admin_required
def official_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')

    psat = get_object_or_404(models.Psat, pk=pk)
    qs_problem = models.Problem.objects.get_filtered_qs_by_psat(psat)
    page_obj, page_range = get_paginator_data(qs_problem, page_number)

    sub_list = admin_view_utils.get_sub_list(psat)

    problem_dict = defaultdict(list)
    for qs_p in qs_problem.order_by('id'):
        problem_dict[qs_p.subject].append(qs_p)
    answer_official_list = [problem_dict[sub] for sub in sub_list]

    context = update_context_data(
        config=config, psat=psat, subjects=sub_list,
        answer_official_list=answer_official_list,
        page_obj=page_obj, page_range=page_range,
    )

    if view_type == 'problem_list':
        return render(request, 'a_psat/problem_list_content.html', context)

    return render(request, 'a_psat/admin_official_detail.html', context)


@admin_required
def official_psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            psat = form.save(commit=False)
            exam = form.cleaned_data['exam']
            exam_order = {'행시': 1, '입시': 2, '칠급': 3}
            psat.order = exam_order.get(exam)
            psat.save()
            admin_view_utils.create_official_problem_model_instances(psat, exam)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.PsatForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def official_psat_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.PsatActiveForm(request.POST)
        if form.is_valid():
            psat = get_object_or_404(models.Psat, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@admin_required
def official_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 문제 업데이트'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            psat = get_object_or_404(models.Psat, year=year, exam=exam)

            file = request.FILES['file']
            df = pd.read_excel(file, header=0, index_col=0)

            answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
            keys = list(answer_symbol.keys())
            combinations = []
            for i in range(1, 6):
                combinations.extend(itertools.combinations(keys, i))

            replace_dict = {}
            for combination in combinations:
                key = ''.join(combination)
                value = int(''.join(str(answer_symbol[k]) for k in combination))
                replace_dict[key] = value

            df['answer'].replace(to_replace=replace_dict, inplace=True)
            df = df.infer_objects(copy=False)

            for index, row in df.iterrows():
                problem = models.Problem.objects.get(psat=psat, subject=row['subject'], number=row['number'])
                problem.paper_type = row['paper_type']
                problem.answer = row['answer']
                problem.question = row['question']
                problem.data = row['data']
                problem.save()

            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)
