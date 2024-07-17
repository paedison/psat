from django.db.models import F, Case, When, Value, IntegerField
from django.db.models.fields.json import KeyTextTransform
from django.shortcuts import render

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .base_info import PsatExamVars
from .. import models
from .. import utils


def list_view(request: HtmxHttpRequest):
    info = {'menu': 'predict', 'view_type': 'predict'}

    main_page = 'main'
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', main_page)

    context = update_context_data(
        info=info, title='Predict', sub_title='성적 예측 [관리자 페이지]',
        icon_menu=icon_set_new.ICON_MENU['score'], pagination_url='?')

    # student
    if hx_pagination in ['main', 'all_student']:
        qs_student = models.PsatStudent.objects.annotate(username=F('user__username')).order_by('id')
        student_page_data = utils.get_page_obj_and_range(qs_student, page_number=page)
        context = update_context_data(context, student_page_data=student_page_data)
        if hx_pagination == 'all_student':
            return render(request, 'a_predict/snippets/admin_list_student.html#all_student', context)

    qs_exam = models.PsatExam.objects.order_by('id')
    exam_page_data = utils.get_page_obj_and_range(qs_exam)
    context = update_context_data(context, exam_list=qs_exam, exam_page_data=exam_page_data)
    return render(request, 'a_predict/admin_list.html', context)


def detail_view(
        request: HtmxHttpRequest, exam_year: int, exam_exam: str, exam_round: int
):
    exam_vars = get_exam_vars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    exam = utils.get_exam(exam_vars=exam_vars)

    main_page = 'main'
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', main_page)

    stat_prefix = ['all_stat', 'filtered_stat']
    catalog_prefix = ['all_catalog', 'filtered_catalog']
    answer_prefix = [f'answer_{idx}' for idx in range(len(exam_vars.subject_fields))]

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam, title='Predict',
        sub_title=utils.get_sub_title(exam),
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
    context = update_context_for_page(
        exam_vars=exam_vars, exam=exam, page=page, context=context,
        hx_pagination=hx_pagination, main_page=main_page,
        prefix_list=stat_prefix, context_fn=get_context_for_stat_page)
    if hx_pagination in stat_prefix:
        return render(request, f'a_predict/snippets/admin_detail_statistics.html#{hx_pagination}', context)

    # catalog_page
    context = update_context_for_page(
        exam_vars=exam_vars, exam=exam, page=page, context=context,
        hx_pagination=hx_pagination, main_page=main_page,
        prefix_list=catalog_prefix, context_fn=get_context_for_catalog_page)
    if hx_pagination in catalog_prefix:
        return render(request, f'a_predict/snippets/admin_detail_catalog.html#{hx_pagination}', context)

    # answer_page
    qs_answer_count = utils.get_qs_answer_count(exam_vars=exam_vars)
    answer_predict = utils.get_data_answer_predict(exam_vars=exam_vars, qs_answer_count=qs_answer_count)
    context = update_context_for_page(
        exam_vars=exam_vars, exam=exam, page=page, context=context,
        hx_pagination=hx_pagination, main_page=main_page,
        prefix_list=answer_prefix, context_fn=get_context_for_answer_page,
        qs_answer_count=qs_answer_count, answer_predict=answer_predict)
    if hx_pagination in answer_prefix:
        return render(request, f'a_predict/snippets/admin_detail_answer.html#{hx_pagination}', context)

    return render(request, 'a_predict/admin_detail.html', context)


def get_exam_vars(exam_year: int, exam_exam: str, exam_round: int):
    if exam_exam == '행시' or exam_exam == '칠급':
        return PsatExamVars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)


def update_context_for_page(
        exam_vars, exam, page, context, hx_pagination, main_page, prefix_list, context_fn, **kwargs
):
    for prefix in prefix_list:
        if hx_pagination in [main_page, prefix]:
            context = context_fn(
                exam_vars=exam_vars, exam=exam, page=page, context=context, prefix=prefix, **kwargs)
    return context


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


def get_context_for_answer_page(exam_vars, exam, page, context, prefix, **kwargs):
    field_idx = int(prefix.split('_')[1])
    field = exam_vars.subject_fields[field_idx]
    qs_answer_count = kwargs.get('qs_answer_count')
    answer_predict = kwargs.get('answer_predict')

    qs_answer_count = qs_answer_count.filter(subject=field)
    answer_page: tuple = utils.get_page_obj_and_range(qs_answer_count, page_number=page)
    utils.update_answer_page(
        exam_vars=exam_vars, exam=exam, page_obj=answer_page[0],
        answer_predict=answer_predict)
    update_context_data(context, **{f'answer_{field_idx}_page': answer_page})
    return context
