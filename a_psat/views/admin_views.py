import itertools
import traceback
from itertools import zip_longest

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common import utils
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms, filters


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')
    url_list = reverse_lazy('psat:admin-menu')
    url_psat_create = reverse_lazy('psat:admin-psat-create')
    url_problem_update = reverse_lazy('psat:admin-problem-update')


@admin_required
def admin_menu_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')

    sub_title = utils.get_sub_title_by_psat(exam_year, exam_exam, exam_subject, end_string='PSAT')
    filterset = filters.PsatFilter(data=request.GET, request=request)

    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for problem in psat.problems.all() if problem.question and problem.data)
        psat.image_problem_count = sum(1 for problem in psat.problems.all() if problem.has_image)

    context = update_context_data(
        config=config, sub_title=sub_title, psat_form=filterset.form,
        page_obj=page_obj, page_range=page_range)
    if view_type == 'exam_list':
        template_name = 'a_psat/admin_menu.html#list_content'
        return render(request, template_name, context)

    return render(request, 'a_psat/admin_menu.html', context)


@admin_required
def psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            exam = form.cleaned_data['exam']
            psat = form.save()
            create_list = []
            if exam == '행시':
                append_create_list(create_list, psat, 40, *['언어', '자료', '상황'])
                append_create_list(create_list, psat, 25, *['헌법'])

            messages = {}
            if create_list:
                try:
                    with transaction.atomic():
                        if create_list:
                            models.Problem.objects.bulk_create(create_list)
                            messages['create'] = f'Successfully updated {len(create_list)} Problem instances.'
                        else:
                            messages['error'] = f'No changes were made to Problem instances.'
                except django.db.utils.IntegrityError:
                    traceback_message = traceback.format_exc()
                    print(traceback_message)
                    messages['error'] = 'An error occurred during the transaction.'

            for message in messages.values():
                if message:
                    print(message)

            response = redirect('psat:admin-menu')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_psat/admin_exam_create.html', context)

    form = forms.PsatForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_exam_create.html', context)


def append_create_list(create_list: list, psat: models.Psat, problem_count: int, *subject_list):
    for subject in subject_list:
        for number in range(1, problem_count + 1):
            problem_info = {'psat': psat, 'subject': subject, 'number': number}
            try:
                models.Problem.objects.get(**problem_info)
            except models.Problem.DoesNotExist:
                create_list.append(models.Problem(**problem_info))


@admin_required
def psat_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.PsatActiveForm(request.POST)
        if form.is_valid():
            psat = get_object_or_404(models.Psat, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@admin_required
def problem_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            psat = get_object_or_404(models.Psat, year=year, exam=exam)

            update_file = request.FILES['update_file']
            df = pd.read_excel(update_file, header=0, index_col=0)

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

            response = redirect('psat:admin-menu')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_psat/admin_problem_update.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_problem_update.html', context)


@admin_required
def admin_problem_list_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page = request.GET.get('page', '1')
    psat = get_object_or_404(models.Psat, pk=pk)
    problems = models.Problem.objects.select_related(
        'psat').filter(psat=psat).annotate(no=F('number'), ans=F('answer'))
    config.url_admin = reverse_lazy(f'admin:a_psat_problem_changelist')
    page_obj, page_range = utils.get_page_obj_and_range(page, problems)

    subject_list = models.choices.subject_choice()
    problem_count = 40
    if psat.exam in ['칠급', '칠예', '민경']:
        subject_list.pop('헌법')
        problem_count = 25

    icons = []
    queryset_list = []
    for subject in subject_list.keys():
        icons.append(icon_set_new.ICON_SUBJECT[subject])
        queryset = problems.filter(subject=subject).order_by('id')
        queryset_list.append(list(queryset))
    problem_list = list(zip_longest(*queryset_list, fillvalue=None))

    context = update_context_data(
        config=config, psat=psat,
        subjects=subject_list.values(), icons=icons,
        problem_count=range(1, problem_count + 1),
        problem_list=problem_list,
        queryset_list=queryset_list,
        page_obj=page_obj, page_range=page_range,
    )
    return render(request, 'a_psat/admin_problem_list.html', context)
