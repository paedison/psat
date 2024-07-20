from django.db.models import F
from django.shortcuts import render

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models
from .. import utils


def list_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}

    # Hx-Pagination header
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', 'main')
    is_all_student = hx_pagination == 'all_student'

    context = update_context_data(
        info=info, title='Predict', sub_title='합격 예측 [관리자 페이지]',
        icon_menu=icon_set_new.ICON_MENU['score'], pagination_url='?')

    # student
    qs_student = models.PsatStudent.objects.annotate(username=F('user__username')).order_by('id')
    student_page_data = utils.get_page_obj_and_range(qs_student, page)
    context = update_context_data(context, student_page_data=student_page_data)
    if is_all_student:
        return render(request, 'a_predict/snippets/admin_list_student.html#all_student', context)

    qs_psat_exam = models.PsatExam.objects.order_by('id')
    qs_police_exam = models.PoliceExam.objects.order_by('id')
    qs_exam = list(qs_psat_exam) + list(qs_police_exam)
    exam_page_data = utils.get_page_obj_and_range(qs_exam)
    context = update_context_data(context, exam_list=qs_exam, exam_page_data=exam_page_data)
    return render(request, 'a_predict/predict_admin_list.html', context)


def detail_view(request: HtmxHttpRequest, **exam_info):
    exam_vars = utils.get_exam_vars(**exam_info)
    exam_vars.exam = utils.get_exam(exam_vars)

    # page prefix
    prefix_stat = ['all_stat', 'filtered_stat']
    prefix_catalog = ['all_catalog', 'filtered_catalog']
    prefix_answer = [f'answer_{idx}' for idx in range(len(exam_vars.subject_fields))]

    # Hx-Pagination header
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', 'main')
    is_stat = hx_pagination in prefix_stat
    is_catalog = hx_pagination in prefix_catalog
    is_answer = hx_pagination in prefix_answer

    # template names
    template_stat = f'a_predict/snippets/admin_detail_statistics.html#{hx_pagination}'
    template_catalog = f'a_predict/snippets/admin_detail_catalog.html#{hx_pagination}'
    template_answer = f'a_predict/snippets/admin_detail_answer.html#{hx_pagination}'

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam_vars.exam, title='Predict',
        sub_title=exam_vars.sub_title,
        exam_vars=exam_vars,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # default page settings
        pagination_url='?',
        prefix_stat=prefix_stat,
        prefix_catalog=prefix_catalog,
        prefix_answer=prefix_answer,
        answer_title=exam_vars.sub_list
    )

    # stat_page
    if is_stat:
        context = get_context_for_stat_page(exam_vars, page, context, hx_pagination)
        return render(request, template_stat, context)

    # catalog_page
    exam_vars.qs_department = utils.get_qs_department(exam_vars)
    if is_catalog:
        context = get_context_for_catalog_page(exam_vars, page, context, hx_pagination)
        return render(request, template_catalog, context)

    # answer_page
    exam_vars.qs_answer_count = utils.get_qs_answer_count(exam_vars)
    exam_vars.answer_predict = utils.get_data_answer_predict(exam_vars)
    if is_answer:
        context = get_context_for_answer_page(exam_vars, page, context, hx_pagination)
        return render(request, template_answer, context)

    for prefix in prefix_stat:
        context = get_context_for_stat_page(exam_vars, page, context, prefix)
    for prefix in prefix_catalog:
        context = get_context_for_catalog_page(exam_vars, page, context, prefix)
    for prefix in prefix_answer:
        context = get_context_for_answer_page(exam_vars, page, context, prefix)
    return render(request, 'a_predict/predict_admin_detail.html', context)


def get_context_for_stat_page(exam_vars, page, context, prefix):
    category = prefix.split('_')[0]
    qs_department = utils.get_qs_department(exam_vars)
    departments = [{'id': 'total', 'unit': '전체', 'department': '전체'}]
    departments.extend(qs_department)
    stat_page: tuple = utils.get_page_obj_and_range(departments, page)
    utils.update_stat_page(exam_vars, stat_page[0], category)
    return update_context_data(context, **{f'{prefix}_page': stat_page})


def get_context_for_catalog_page(exam_vars, page, context, prefix):
    category = prefix.split('_')[0]
    qs_student = utils.get_qs_student(exam_vars)
    if category == 'filtered':
        qs_student = qs_student.filter(answer_all_confirmed_at__isnull=False)
    qs_student = utils.get_qs_student_for_admin_views(qs_student, category)
    catalog_page: tuple = utils.get_page_obj_and_range(qs_student, page)
    utils.update_admin_catalog_page(exam_vars, catalog_page[0], category)
    return update_context_data(context, **{f'{prefix}_page': catalog_page})


def get_context_for_answer_page(exam_vars, page, context, prefix):
    field_idx = int(prefix.split('_')[1])
    field = exam_vars.subject_fields[field_idx]
    qs_answer_count = exam_vars.qs_answer_count.filter(subject=field)
    answer_page: tuple = utils.get_page_obj_and_range(qs_answer_count, page)
    utils.update_answer_page(exam_vars, answer_page[0])
    update_context_data(context, **{f'answer_{field_idx}_page': answer_page})
    return context
