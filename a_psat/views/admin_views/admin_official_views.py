from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_psat import models, forms
from a_psat.utils.official_utils import *
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data


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
    list_data = AdminListData(request=request)
    context = update_context_data(
        config=config,
        sub_title=list_data.sub_title,
        psat_form=list_data.filterset.form,
        psat_context=list_data.get_psat_context()
    )
    if list_data.view_type == 'exam_list':
        return render(request, f'a_psat/admin_official_list.html#exam_list', context)  # noqa
    return render(request, 'a_psat/admin_official_list.html', context)


@admin_required
def official_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    psat = get_object_or_404(models.Psat, pk=pk)
    detail_data = AdminDetailData(request=request, psat=psat)
    context = update_context_data(config=config, psat=psat, problem_context=detail_data.get_problem_context())

    if detail_data.view_type == 'problem_list':
        return render(request, 'a_psat/problem_list_content.html', context)

    context = update_context_data(context, answer_official_context=detail_data.get_answer_official_context())
    return render(request, 'a_psat/admin_official_detail.html', context)


@admin_required
def official_psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(form=form)
            create_data.process_post_request()
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
            update_data = AdminUpdateData(request=request, psat=psat)
            update_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)
