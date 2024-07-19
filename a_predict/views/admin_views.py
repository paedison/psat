from django.db.models import F, Case, When, Value, IntegerField
from django.db.models.fields.json import KeyTextTransform
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
    student_page_data = utils.get_page_obj_and_range(qs_student, page_number=page)
    context = update_context_data(context, student_page_data=student_page_data)
    if is_all_student:
        return render(request, 'a_predict/snippets/admin_list_student.html#all_student', context)

    qs_psat_exam = models.PsatExam.objects.order_by('id')
    qs_police_exam = models.PoliceExam.objects.order_by('id')
    qs_exam = list(qs_psat_exam) + list(qs_police_exam)
    exam_page_data = utils.get_page_obj_and_range(qs_exam)
    context = update_context_data(context, exam_list=qs_exam, exam_page_data=exam_page_data)
    return render(request, 'a_predict/admin_list.html', context)


def detail_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = utils.get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)

    # page prefix
    stat_prefix = ['all_stat', 'filtered_stat']
    catalog_prefix = ['all_catalog', 'filtered_catalog']
    answer_prefix = [f'answer_{idx}' for idx in range(len(exam_vars.subject_fields))]

    # Hx-Pagination header
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', 'main')
    is_stat = hx_pagination in stat_prefix
    is_catalog = hx_pagination in catalog_prefix
    is_answer = hx_pagination in answer_prefix

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam, title='Predict',
        sub_title=exam_vars.sub_title,
        exam_vars=exam_vars,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # default page settings
        pagination_url='?',
        stat_prefix=stat_prefix,
        catalog_prefix=catalog_prefix,
        answer_prefix=answer_prefix,
        answer_title=exam_vars.sub_list
    )

    # stat_page
    if is_stat:
        context = get_context_for_stat_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=hx_pagination)
        return render(request, f'a_predict/snippets/admin_detail_statistics.html#{hx_pagination}', context)

    # catalog_page
    if is_catalog:
        context = get_context_for_catalog_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=hx_pagination)
        return render(request, f'a_predict/snippets/admin_detail_catalog.html#{hx_pagination}', context)

    # answer_page
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars)
    answer_predict = utils.get_data_answer_predict(exam_vars=exam_vars, qs_answer_count=qs_answer_count)
    if is_answer:
        context = get_context_for_answer_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=hx_pagination,
            qs_answer_count=qs_answer_count, answer_predict=answer_predict)
        return render(request, f'a_predict/snippets/admin_detail_answer.html#{hx_pagination}', context)

    for prefix in stat_prefix:
        context = get_context_for_stat_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=prefix)
    for prefix in catalog_prefix:
        context = get_context_for_catalog_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=prefix)
    for prefix in answer_prefix:
        context = get_context_for_answer_page(
            exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=prefix,
            qs_answer_count=qs_answer_count, answer_predict=answer_predict)
    return render(request, 'a_predict/admin_detail.html', context)


def get_context_for_stat_page(exam_vars, exam, page, context, prefix):
    category = prefix.split('_')[0]
    qs_department = utils.get_qs_department(exam_vars=exam_vars)
    departments = [{'id': 'total', 'unit': '전체', 'department': '전체'}]
    departments.extend(qs_department)
    stat_page: tuple = utils.get_page_obj_and_range(departments, page_number=page)
    utils.update_stat_page(
        exam_vars=exam_vars, exam=exam, page_obj=stat_page[0], category=category)
    return update_context_data(context, **{f'{prefix}_page': stat_page})


def get_context_for_catalog_page(exam_vars, exam, page, context, prefix):
    category = prefix.split('_')[0]
    qs_department = utils.get_qs_department(exam_vars=exam_vars)
    qs_student = utils.get_qs_student(exam_vars=exam_vars)
    if category == 'filtered':
        qs_student = qs_student.filter(answer_all_confirmed_at__isnull=False)
    qs_student = qs_student.annotate(
        all_psat_rank=KeyTextTransform('psat_avg', KeyTextTransform(
            'total', KeyTextTransform(category, 'rank'))),
        zero_rank_order=Case(
            When(all_psat_rank=0, then=Value(1)),
            default=Value(0), output_field=IntegerField(),
        )
    ).order_by('zero_rank_order', 'all_psat_rank')
    catalog_page: tuple = utils.get_page_obj_and_range(qs_student, page_number=page)
    utils.update_admin_catalog_page(
        exam_vars=exam_vars, exam=exam, qs_department=qs_department,
        page_obj=catalog_page[0], category=category)
    return update_context_data(context, **{f'{prefix}_page': catalog_page})


def get_context_for_answer_page(
        exam_vars, exam, page, context, prefix, qs_answer_count, answer_predict
):
    field_idx = int(prefix.split('_')[1])
    field = exam_vars.subject_fields[field_idx]
    qs_answer_count = qs_answer_count.filter(subject=field)
    answer_page: tuple = utils.get_page_obj_and_range(qs_answer_count, page_number=page)
    utils.update_answer_page(
        exam_vars=exam_vars, exam=exam, page_obj=answer_page[0],
        answer_predict=answer_predict)
    update_context_data(context, **{f'answer_{field_idx}_page': answer_page})
    return context
