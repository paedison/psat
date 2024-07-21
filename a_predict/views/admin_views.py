import pandas as pd
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms


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
    exam_vars = utils.get_admin_exam_vars(**exam_info)
    exam_vars.exam = utils.get_exam(exam_vars)

    # page prefix
    header_stat = ['all_stat', 'filtered_stat']
    header_catalog = ['all_catalog', 'filtered_catalog']
    header_answer = [f'answer_{idx}' for idx in range(len(exam_vars.subject_fields))]

    # Hx-Pagination header
    page = request.GET.get('page', 1)
    hx_pagination = request.headers.get('Hx-Pagination', 'main')
    is_stat = hx_pagination in header_stat
    is_catalog = hx_pagination in header_catalog
    is_answer = hx_pagination in header_answer

    # template names
    template_stat = f'a_predict/snippets/admin_detail_statistics.html#{hx_pagination}'
    template_catalog = f'a_predict/snippets/admin_detail_catalog.html#{hx_pagination}'
    template_answer = f'a_predict/snippets/admin_detail_answer.html#{hx_pagination}'

    form = forms.UploadAnswerOfficialFileForm()

    context = update_context_data(
        # base info
        info=exam_vars.info, exam=exam_vars.exam, title='Predict',
        sub_title=exam_vars.sub_title, exam_vars=exam_vars,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # default page settings
        pagination_url='?', header_stat=header_stat,
        header_catalog=header_catalog, header_answer=header_answer,
        answer_title=exam_vars.sub_list, form=form,
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

    for header in header_stat:
        context = get_context_for_stat_page(exam_vars, page, context, header)
    for header in header_catalog:
        context = get_context_for_catalog_page(exam_vars, page, context, header)
    for header in header_answer:
        context = get_context_for_answer_page(exam_vars, page, context, header)
    return render(request, 'a_predict/predict_admin_detail.html', context)


def get_context_for_stat_page(exam_vars, page, context, header):
    category = header.split('_')[0]
    qs_department = utils.get_qs_department(exam_vars)
    departments = [{'id': 'total', 'unit': '전체', 'department': '전체'}]
    departments.extend(qs_department)
    stat_page: tuple = utils.get_page_obj_and_range(departments, page)
    utils.update_stat_page(exam_vars, stat_page[0], category)
    return update_context_data(context, **{f'{header}_page': stat_page})


def get_context_for_catalog_page(exam_vars, page, context, header):
    category = header.split('_')[0]
    qs_student = utils.get_qs_student(exam_vars)
    if category == 'filtered':
        qs_student = qs_student.filter(answer_all_confirmed_at__isnull=False)
    qs_student = utils.get_qs_student_for_admin_views(qs_student, category)
    catalog_page: tuple = utils.get_page_obj_and_range(qs_student, page)
    utils.update_admin_catalog_page(exam_vars, catalog_page[0], category)
    return update_context_data(context, **{f'{header}_page': catalog_page})


def get_context_for_answer_page(exam_vars, page, context, header):
    field_idx = int(header.split('_')[1])
    field = exam_vars.subject_fields[field_idx]
    qs_answer_count = exam_vars.qs_answer_count.filter(subject=field)
    answer_page: tuple = utils.get_page_obj_and_range(qs_answer_count, page)
    utils.update_answer_page(exam_vars, answer_page[0])
    update_context_data(context, **{f'answer_{field_idx}_page': answer_page})
    return context


@require_POST
def update_view(request: HtmxHttpRequest, **exam_info):
    exam_vars = utils.get_exam_vars(**exam_info)
    exam_vars.exam = utils.get_exam(exam_vars)

    # Hx-Update header
    hx_update = request.headers.get('Hx-Admin-Update', 'main')
    is_main = hx_update == 'main'
    is_answer_official = hx_update == 'answer_official'
    is_statistics = hx_update == 'statistics'

    if is_answer_official:
        context = get_context_for_update_answer_official(request, exam_vars)
    if is_statistics:
        context = get_context_for_update_statistics(request, exam_vars)

    return render(request, 'a_predict/snippets/admin_modal_update.html', context)


def get_context_for_update_answer_official(request, exam_vars):
    exam = exam_vars.exam
    header = '정답 업데이트'
    next_url = exam_vars.url_admin_detail
    is_updated = None
    message = '에러가 발생했습니다.'

    form = forms.UploadAnswerOfficialFileForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['file']
        df = pd.read_excel(uploaded_file, header=0, index_col=0)
        df.dropna(inplace=True)

        answer_official = {}
        try:
            for subject, answers in df.items():
                field = exam_vars.get_subject_field(subject)
                answer_official.update({
                    field: [int(ans) for ans in answers if ans]
                })
            if exam.answer_official == answer_official:
                is_updated = False
                message = '기존 정답 데이터와 일치합니다.'
            else:
                is_updated = True
                exam.answer_official = answer_official
                exam.save()
                message = '문제 정답을 업데이트했습니다.'
        except ValueError:
            pass
    return update_context_data(
        header=header, next_url=next_url, is_updated=is_updated, message=message)


def get_context_for_update_statistics(request, exam_vars):
    exam_model = exam_vars.exam_model
    student_model = exam_vars.student_model
    answer_count_model = exam_vars.answer_count_model
    exam_vars.exam = exam_model.objects.get(**exam_vars.exam_info)

    header = '정답 업데이트'
    next_url = exam_vars.url_admin_detail
    is_updated = True
    message = '통계가 업데이트됐습니다.'

    # Update student_model for score
    qs_student = student_model.objects.filter(**exam_vars.exam_info)
    total_answer_lists, score_data = utils.get_total_answer_lists_and_score_data(exam_vars, qs_student)
    utils.create_or_update_model(student_model, ['score'], score_data)

    # Update student_model for rank
    rank_data = utils.get_rank_data(exam_vars, qs_student)
    utils.create_or_update_model(student_model, ['rank'], rank_data)

    # Update exam_model for participants
    participants = utils.get_participants(exam_vars, qs_student)
    exam_model_data = utils.get_exam_model_data(exam_vars, participants)
    utils.create_or_update_model(exam_model, ['participants'], exam_model_data)

    # Update exam_model for statistics
    qs_department = utils.get_qs_department(exam_vars)
    statistics = utils.get_statistics(exam_vars, qs_department, qs_student)
    statistics_data = utils.get_statistics_data(exam_vars, statistics)
    utils.create_or_update_model(exam_model, ['statistics'], statistics_data)

    # Update answer_count_model
    all_count_dict = utils.get_all_count_dict(exam_vars, total_answer_lists)
    answer_fields = exam_vars.count_fields + ['count_multiple', 'count_total']
    answer_count_data = utils.get_answer_count_model_data(exam_vars, answer_fields, all_count_dict)
    utils.create_or_update_model(answer_count_model, answer_fields, answer_count_data)

    # Update answer_count_model by rank
    total_answer_lists = utils.get_total_answer_lists_by_category(exam_vars, qs_student)
    total_count_dict = utils.get_total_count_dict_by_category(exam_vars, total_answer_lists)
    total_answer_count_data = utils.get_total_answer_count_model_data(
        exam_vars, ['all', 'filtered'], total_count_dict)
    utils.create_or_update_model(
        answer_count_model, ['all', 'filtered'], total_answer_count_data)

    return update_context_data(
        header=header, next_url=next_url, is_updated=is_updated, message=message)
