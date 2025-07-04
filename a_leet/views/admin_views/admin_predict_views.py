from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_leet import models, forms
from a_leet.utils.predict.admin_utils import *
from a_leet.views.normal_views import predict_views
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    menu = menu_eng = 'leet_admin'
    menu_kor = 'LEET 관리자'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격 예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_leet_leet_changelist')
    url_admin_leet_list = reverse_lazy('admin:a_leet_leet_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_leet_problem_changelist')

    url_list = reverse_lazy('leet:admin-predict-list')
    url_problem_update = reverse_lazy('leet:admin-official-update')

    url_predict_create = reverse_lazy('leet:admin-predict-create')


@admin_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = AdminListData(_request=request)
    context = update_context_data(config=config, predict_leet_context=list_data.get_predict_leet_context())

    if list_data.view_type == 'predict_leet_list':
        return render(request, f'a_leet/admin_predict_list.html#study_category_list', context)  # noqa
    return render(request, 'a_leet/admin_predict_list.html', context)


@admin_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    leet = models.Leet.objects.filter(pk=pk).select_related('predict_leet').first()
    context = update_context_data(config=config, leet=leet)
    if not leet or not hasattr(leet, 'predict_leet') or not leet.predict_leet.is_active:
        context = update_context_data(context, message='합격 예측 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_leet/redirect.html', context)

    detail_data = AdminDetailData(_request=request, _leet=leet)

    if detail_data.view_type == 'problem_list':
        context = update_context_data(context, **detail_data.get_problem_context())
        return render(request, 'a_leet/problem_list_content.html', context)

    config.url_admin_predict_update = reverse_lazy('leet:admin-predict-update', args=[pk])
    context = update_context_data(
        context, predict_leet=leet.predict_leet, icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH)

    if detail_data.view_type == 'total_statistics_list':
        statistics_data = detail_data.statistics.get_admin_statistics_context()['statistics_context']['total']
        context = update_context_data(context, statistics_data=statistics_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_statistics.html', context)
    if detail_data.view_type == 'filtered_statistics_list':
        statistics_data = detail_data.statistics.get_admin_statistics_context()['statistics_context']['filtered']
        context = update_context_data(context, statistics_data=statistics_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_statistics.html', context)
    if detail_data.view_type == 'total_catalog_list':
        catalog_data = detail_data.catalog.get_admin_catalog_context()['catalog_context']['total']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_catalog.html', context)
    if detail_data.view_type == 'filtered_catalog_list':
        catalog_data = detail_data.catalog.get_admin_catalog_context()['catalog_context']['filtered']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_catalog.html', context)
    if detail_data.view_type == 'student_search':
        catalog_data = detail_data.catalog.get_admin_catalog_context(for_search=True)['catalog_context']['total']
        context = update_context_data(context, catalog_data=catalog_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_catalog.html', context)
    if detail_data.view_type == 'answer_list':
        answer_data = detail_data.answer.get_admin_answer_context(True)['answer_context'][detail_data.exam_subject]
        context = update_context_data(context, answer_data=answer_data)
        return render(request, 'a_leet/snippets/admin_predict_detail_answer_analysis.html', context)

    context = update_context_data(
        context,
        **detail_data.statistics.get_admin_statistics_context(),
        **detail_data.catalog.get_admin_catalog_context(),
        **detail_data.answer.get_admin_answer_context(),
        **detail_data.get_answer_predict_context(),
        **detail_data.get_answer_official_context(),
        **detail_data.get_problem_context(),
    )
    return render(request, 'a_leet/admin_predict_detail.html', context)


@admin_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'LEET 합격 예측 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PredictLeetForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(_form=form)
            create_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_leet/admin_form.html', context)

    form = forms.PredictLeetForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_leet/admin_form.html', context)


@admin_required
def predict_update_view(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    context = update_context_data(next_url=leet.get_admin_predict_detail_url())
    update_data = AdminUpdateData(_request=request, _leet=leet)

    if update_data.view_type == 'answer_official':
        is_updated, message = update_data.answer_official.update_problem_model_for_answer_official()
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'raw_score':
        is_updated, message = update_data.score.update_raw_scores()
        context = update_context_data(context, header='원점수 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'score':
        is_updated, message = update_data.score.update_scores()
        context = update_context_data(context, header='표준점수 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'rank':
        is_updated, message = update_data.rank.update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'statistics':
        is_updated, message = update_data.statistics.update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'answer_count':
        is_updated, message = update_data.answer_count.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_leet/snippets/admin_modal_predict_update.html', context)


@admin_required
def predict_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.PredictStudent = models.PredictStudent.objects.filter(pk=pk).first()
    if student:
        student = models.PredictStudent.objects.leet_student_with_answer_count(student.user, student.leet)
        return predict_views.predict_detail_view(request, student.leet.id, student=student)
    return redirect('leet:admin-predict-list')


@admin_required
def predict_statistics_print(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    detail_data = AdminDetailData(_request=request, _leet=leet)
    context = update_context_data(leet=leet, **detail_data.statistics.get_admin_statistics_context(200))
    return render(request, 'a_leet/admin_print_statistics.html', context)


@admin_required
def predict_catalog_print(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    student_list = models.PredictStudent.objects.filtered_student_by_leet(leet)
    context = update_context_data(leet=leet, student_list=student_list)
    return render(request, 'a_leet/admin_print_catalog.html', context)


@admin_required
def predict_answer_print(request: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    detail_data = AdminDetailData(_request=request, _leet=leet)
    context = update_context_data(leet=leet, **detail_data.answer.get_admin_answer_context(per_page=1000))
    return render(request, 'a_leet/admin_print_answers.html', context)


@admin_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return AdminExportExcelData(_leet=leet).get_statistics_response()


@admin_required
def predict_prime_id_excel(_: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return AdminExportExcelData(_leet=leet).get_prime_id_response()


@admin_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return AdminExportExcelData(_leet=leet).get_catalog_response()


@admin_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    leet = get_object_or_404(models.Leet, pk=pk)
    return AdminExportExcelData(_leet=leet).get_answer_response()
