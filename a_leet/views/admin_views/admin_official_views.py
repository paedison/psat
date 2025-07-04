from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_leet import models, forms
from a_leet.utils.official_utils import *
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    menu = menu_eng = 'leet_admin'
    menu_kor = 'LEET 관리자'
    submenu = submenu_eng = 'official'
    submenu_kor = '기출문제'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_leet_leet_changelist')
    url_admin_leet_list = reverse_lazy('admin:a_leet_leet_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_leet_problem_changelist')

    url_list = reverse_lazy('leet:admin-official-list')
    url_leet_create = reverse_lazy('leet:admin-official-leet-create')
    url_problem_update = reverse_lazy('leet:admin-official-update')


@admin_required
def official_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = AdminListData(request=request)
    context = update_context_data(
        config=config,
        sub_title=list_data.sub_title,
        leet_form=list_data.filterset.form,
        leet_context=list_data.get_leet_context()
    )
    if list_data.view_type == 'exam_list':
        return render(request, f'a_leet/admin_official_list.html#exam_list', context)  # noqa
    return render(request, 'a_leet/admin_official_list.html', context)


@admin_required
def official_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    leet = get_object_or_404(models.Leet, pk=pk)
    detail_data = AdminDetailData(request=request, leet=leet)
    context = update_context_data(config=config, leet=leet, problem_context=detail_data.get_problem_context())

    if detail_data.view_type == 'problem_list':
        return render(request, 'a_leet/problem_list_content.html', context)

    context = update_context_data(context, answer_official_context=detail_data.get_answer_official_context())
    return render(request, 'a_leet/admin_official_detail.html', context)


@admin_required
def official_leet_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'LEET 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.LeetForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(form=form)
            create_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_leet/admin_form.html', context)

    form = forms.LeetForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_leet/admin_form.html', context)


@admin_required
def official_leet_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.LeetActiveForm(request.POST)
        if form.is_valid():
            leet = get_object_or_404(models.Leet, pk=pk)
            is_active = form.cleaned_data['is_active']
            leet.is_active = is_active
            leet.save()
    return HttpResponse('')


@admin_required
def official_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'LEET 문제 업데이트'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            leet = get_object_or_404(models.Leet, year=year, exam=exam)
            update_data = AdminUpdateData(request=request, leet=leet)
            update_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_leet/admin_form.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_leet/admin_form.html', context)
