from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import forms, filters
from a_psat.utils.official_utils import *
from a_psat.utils.variables import RequestContext, OfficialModelData
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_context

_model = OfficialModelData()


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
    request_context = RequestContext(_request=request)
    filterset = filters.PsatFilter(data=request.GET, request=request)

    psat_context = get_paginator_context(filterset.qs, request_context.page_number)
    for psat in psat_context['page_obj']:
        psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
        psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)

    context = update_context_data(
        config=config,
        sub_title=request_context.get_sub_title(),
        psat_form=filterset.form,
        psat_context=psat_context,
    )
    if request_context.view_type == 'exam_list':
        return render(request, f'a_psat/admin_official_list.html#exam_list', context)  # noqa
    return render(request, 'a_psat/admin_official_list.html', context)


@admin_required
def official_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    psat = get_object_or_404(_model.psat, pk=pk)
    detail_context = AdminDetailContext(request=request, psat=psat)
    context = update_context_data(config=config, psat=psat, problem_context=detail_context.get_problem_context())

    view_type = request.headers.get('View-Type', '')
    if view_type == 'problem_list':
        return render(request, 'a_psat/problem_list_content.html', context)

    context = update_context_data(context, answer_official_context=detail_context.get_answer_official_context())
    return render(request, 'a_psat/admin_official_detail.html', context)


@admin_required
def official_psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            AdminCreateContext(form=form).process_post_request()
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
            psat = get_object_or_404(_model.psat, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@admin_required
def official_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 자료 업데이트'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        context = update_context_data(context, form=form)
        if form.is_valid():
            AdminUpdateContext(_request=request, _context=context).process_post_request()
            return redirect(config.url_list)
        return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def official_update_by_psat_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    psat = get_object_or_404(_model.psat, pk=pk)
    title = f'{psat.full_reference} 자료 업데이트'
    context = update_context_data(config=config, title=title, psat=psat)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        context = update_context_data(context, form=form)
        if form.is_valid():
            AdminUpdateContext(_request=request, _context=context).process_post_request()
            return redirect(config.url_list)
        return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)
