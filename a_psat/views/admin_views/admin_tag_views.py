import pandas as pd
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from a_psat import models, forms, filters
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_data
from ...utils import admin_view_utils


class ViewConfiguration:
    menu = menu_eng = 'psat_admin'
    menu_kor = 'PSAT 관리자'
    submenu = submenu_eng = 'tag'
    submenu_kor = '태그'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-tag-list')

    url_tag_import_problem_list = reverse_lazy('psat:admin-tag-import-problem-list')
    url_tag_export_problem_list = reverse_lazy('psat:admin-tag-export-problem-list')
    url_tag_import_tag_list = reverse_lazy('psat:admin-tag-import-tag-list')
    url_tag_export_tag_list = reverse_lazy('psat:admin-tag-export-tag-list')


@admin_required
def tag_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')

    qs_tag = models.ProblemTag.objects.order_by('-id')
    problem_tag_filterset = filters.ProblemTagFilter(data=request.GET, request=request)
    tagged_item_filterset = filters.ProblemTaggedItemFilter(data=request.GET, request=request)
    context = update_context_data(
        config=config, icon_image=icon_set_new.ICON_IMAGE,
        problem_form=problem_tag_filterset.form,
        tag_form=tagged_item_filterset.form
    )

    if view_type in ['problem_container', 'problem_list']:
        problem_page_obj, problem_page_range = get_paginator_data(problem_tag_filterset.qs, page_number)
        context = update_context_data(context, problem_page_obj=problem_page_obj, problem_page_range=problem_page_range)
        return render(request, f'a_psat/admin_tag_list.html#{view_type}', context)

    if view_type in ['tagged_problem_container', 'tagged_problem_list']:
        tagged_item_page_obj, tagged_item_page_range = get_paginator_data(tagged_item_filterset.qs, page_number)
        context = update_context_data(context, tagged_item_page_obj=tagged_item_page_obj, tagged_item_page_range=tagged_item_page_range)
        return render(request, f'a_psat/admin_tag_list.html#{view_type}', context)

    if view_type in ['tag_container', 'tag_list']:
        tag_page_obj, tag_page_range = get_paginator_data(qs_tag, page_number)
        context = update_context_data(context, tag_page_obj=tag_page_obj, tag_page_range=tag_page_range)
        return render(request, f'a_psat/admin_tag_list.html#{view_type}', context)

    problem_page_obj, problem_page_range = get_paginator_data(problem_tag_filterset.qs, page_number)
    tagged_item_page_obj, tagged_item_page_range = get_paginator_data(tagged_item_filterset.qs, page_number)
    tag_page_obj, tag_page_range = get_paginator_data(qs_tag, page_number)
    context = update_context_data(
        context,
        tagged_item_page_obj=tagged_item_page_obj, tagged_item_page_range=tagged_item_page_range,
        problem_page_obj=problem_page_obj, problem_page_range=problem_page_range,
        tag_page_obj=tag_page_obj, tag_page_range=tag_page_range,
    )
    return render(request, 'a_psat/admin_tag_list.html', context)


@admin_required
def tag_detail_view(request: HtmxHttpRequest, pk: int):
    pass


@admin_required
def tag_import_problem_list(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '문제별 태그 목록 불러오기'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        user = request.user
        form = forms.UploadFileForm(request.POST, files=request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_excel(file, header=0, index_col=0)
            df.fillna(value=pd.NA, inplace=True)
            for index, row in df.iterrows():
                problem_id = row['id']
                year = row['year']
                exam = row['exam']
                subject = row['subject']
                number = row['number']
                tags = row['tags'].split(', ') if not pd.isna(row['tags']) else pd.NA

                problem = None
                if not pd.isna(problem_id):
                    problem = models.Problem.objects.get(id=problem_id)
                elif not pd.isna(row[['year', 'exam', 'subject', 'number']]).any():
                    problem = models.Problem.objects.get(
                        psat__year=year, psat__exam=exam, subject=subject, number=number)

                if problem:
                    problem.tags.add(*tags, through_defaults={'user_id': user.id})
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)



@admin_required
def tag_export_problem_list(_: HtmxHttpRequest):
    qs_problem = models.Problem.objects.filter(
        tagged_problems__isnull=False, tagged_problems__is_active=True).select_related('psat').distinct()
    rows = []
    for qs_p in qs_problem:
        tag_string = ', '.join(qs_p.tags.names())
        rows.append({
            'id': qs_p.id,
            'year': qs_p.psat.year,
            'exam': qs_p.psat.exam,
            'subject': qs_p.subject,
            'number': qs_p.number,
            'tags': tag_string,
        })
    df = pd.DataFrame(rows, index=None)
    return admin_view_utils.get_response_for_excel_file(df, 'problem_list.xlsx')


@admin_required
def tag_import_tag_list(request: HtmxHttpRequest):

    pass


@admin_required
def tag_export_tag_list(_: HtmxHttpRequest):
    qs_tagged_problem = models.ProblemTaggedItem.objects.select_related(
        'tag', 'content_object', 'content_object__psat')
    rows = []
    for qs_tp in qs_tagged_problem:
        rows.append({
            'id': qs_tp.id,
            'problem_id': qs_tp.content_object_id,
            'year': qs_tp.content_object.psat.year,
            'exam': qs_tp.content_object.psat.exam,
            'subject': qs_tp.content_object.subject,
            'number': qs_tp.content_object.number,
            'tag': qs_tp.tag.name,
            'slug': qs_tp.tag.slug,
            'user_id': qs_tp.user_id,
            'username': qs_tp.user.username,
        })
    df = pd.DataFrame(rows, index=None)
    return admin_view_utils.get_response_for_excel_file(df, 'tag_list.xlsx')
