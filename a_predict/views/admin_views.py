import pandas as pd
from django.db.models import F, Value
from django.shortcuts import render
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .base_info import PredictExamVars
from .. import models, utils, forms
from a_predict.management import command_utils


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

    qs_psat_exam = models.PsatExam.objects.order_by('id').annotate(type=Value('psat'))
    qs_police_exam = models.PoliceExam.objects.order_by('id').annotate(type=Value('police'))
    qs_exam = list(qs_psat_exam) + list(qs_police_exam)
    exam_page_data = utils.get_page_obj_and_range(qs_exam)
    context = update_context_data(context, exam_list=qs_exam, exam_page_data=exam_page_data)
    return render(request, 'a_predict/predict_admin_list.html', context)


def detail_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    exam = exam_vars.get_exam()

    # page prefix
    header_stat = ['stat_all', 'stat_filtered']
    header_catalog = ['catalog_all', 'catalog_filtered']
    header_answer = [f'answer_{idx}' for idx in range(len(exam_vars.all_subject_fields))]

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
        info=exam_vars.info, exam=exam,
        exam_vars=exam_vars, exam_type=exam_vars.exam_type,
        title='Predict', sub_title=exam_vars.sub_title,

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
        category = hx_pagination.split('_')[1]
        qs_department = exam_vars.get_qs_department()
        stat_page = get_stat_page(qs_department, page)
        utils.update_stat_page(exam_vars, exam, stat_page[0], category)
        context = update_context_data(context, **{f'{hx_pagination}_page': stat_page})
        return render(request, template_stat, context)

    # catalog_page
    if is_catalog:
        category = hx_pagination.split('_')[1]
        qs_student = exam_vars.get_qs_student()
        qs_department = exam_vars.get_qs_department()
        catalog_page = get_catalog_page(qs_student, category, page)
        utils.update_catalog_page(exam_vars, exam, qs_department, catalog_page[0], category)
        context = update_context_data(context, **{f'{hx_pagination}_page': catalog_page})
        return render(request, template_catalog, context)

    # answer_page
    if is_answer:
        qs_answer_count = exam_vars.get_qs_answer_count()
        answer_predict = exam_vars.get_data_answer_predict()
        answer_page = get_answer_page(qs_answer_count, exam_vars.all_subject_fields, page, hx_pagination)
        context = update_context_data(context, **{f'{hx_pagination}_page': answer_page})
        utils.update_answer_page(exam_vars, exam, answer_predict, answer_page[0])
        return render(request, template_answer, context)

    # main_page
    qs_department = exam_vars.get_qs_department()
    for header in header_stat:
        category = header.split('_')[1]
        stat_page = get_stat_page(qs_department, page)
        utils.update_stat_page(exam_vars, exam, stat_page[0], category)
        context = update_context_data(context, **{f'{header}_page': stat_page})

    for header in header_catalog:
        category = header.split('_')[1]
        qs_student = exam_vars.get_qs_student()
        catalog_page = get_catalog_page(qs_student, category, page)
        utils.update_catalog_page(exam_vars, exam, qs_department, catalog_page[0], category)
        context = update_context_data(context, **{f'{header}_page': catalog_page})

    qs_answer_count = exam_vars.get_qs_answer_count()
    answer_predict = exam_vars.get_data_answer_predict()
    for header in header_answer:
        answer_page = get_answer_page(qs_answer_count, exam_vars.all_subject_fields, page, header)
        utils.update_answer_page(exam_vars, exam, answer_predict, answer_page[0])
        context = update_context_data(context, **{f'{header}_page': answer_page})

    return render(request, 'a_predict/predict_admin_detail.html', context)


def get_stat_page(qs_department, page):
    departments = [{'id': 'total', 'unit': '전체', 'department': '전체'}]
    departments.extend(qs_department)
    stat_page: tuple = utils.get_page_obj_and_range(departments, page)
    return stat_page


def get_catalog_page(qs_student, category, page):
    qs_student = utils.get_qs_student_for_admin_views(qs_student, category)
    catalog_page: tuple = utils.get_page_obj_and_range(qs_student, page)
    return catalog_page


def get_answer_page(qs_answer_count, all_subject_fields, page, header):
    field_idx = int(header.split('_')[1])
    field = all_subject_fields[field_idx]
    qs_answer_count = qs_answer_count.filter(subject=field)
    answer_page: tuple = utils.get_page_obj_and_range(qs_answer_count, page)
    return answer_page


@require_POST
def update_view(request: HtmxHttpRequest, **kwargs):
    exam_vars = PredictExamVars(request, **kwargs)
    exam = exam_vars.get_exam()

    # Hx-Update header
    hx_update = request.headers.get('Hx-Admin-Update', 'main')
    is_answer_official = hx_update == 'answer_official'
    is_statistics = hx_update == 'statistics'

    context = {}
    next_url = exam_vars.url_admin_detail
    if is_answer_official:
        is_updated, message = update_answer_official(request, exam_vars, exam)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)
    if is_statistics:
        qs_student = exam_vars.get_qs_student()
        is_updated, message = update_statistics(exam_vars, exam, qs_student)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_predict/snippets/admin_modal_update.html', context)


def update_answer_official(request, exam_vars, exam) -> tuple:
    is_updated = None
    message_dict = {
        None: '에러가 발생했습니다.', True: '문제 정답을 업데이트했습니다.', False: '기존 정답 데이터와 일치합니다.'
    }

    form = forms.UploadAnswerOfficialFileForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['file']
        df = pd.read_excel(uploaded_file, sheet_name='정답', header=0, index_col=0)
        df.fillna(value=0, inplace=True)
        answer_official = {}
        try:
            if not exam.answer_official:
                for subject, rows in df.items():
                    fld = exam_vars.get_subject_field(subject)
                    answer_official.update({fld: [int(row) for row in rows if row]})
                exam.answer_official = answer_official
                exam.save()
                is_updated = True
            else:
                is_updated = False
                for subject, rows in df.items():
                    fld = exam_vars.get_subject_field(subject)
                    for no, ans in enumerate(exam.answer_official[fld], start=1):
                        if ans != int(rows[no]):
                            is_updated = True
                            exam.answer_official[fld][no - 1] = int(rows[no])
                if is_updated:
                    exam.save()
        except ValueError:
            pass
    return is_updated, message_dict[is_updated]


def update_statistics(exam_vars, exam, qs_student):
    is_updated = None
    message = '정답을 업로드해주세요.'
    if exam.answer_official:
        is_updated = True
        message = '통계가 업데이트됐습니다.'

        # Update student_model for data(score)
        score_data, score_lists = command_utils.get_score_data_score_lists(exam_vars, exam, qs_student, ['data'])
        command_utils.create_or_update_model(exam_vars.student_model, ['data'], score_data)

        # Update student_model for rank
        rank_data = command_utils.get_rank_data(exam_vars, exam, qs_student, score_lists)
        command_utils.create_or_update_model(exam_vars.student_model, ['rank'], rank_data)

        # Update exam_model for participants
        participants = command_utils.get_participants(exam_vars, exam, qs_student)
        exam_model_data = command_utils.get_exam_model_data(exam, participants)
        command_utils.create_or_update_model(exam_vars.exam_model, ['participants'], exam_model_data)

        # Update exam_model for statistics
        qs_department = command_utils.get_qs_department(exam_vars)
        statistics = command_utils.get_statistics(exam_vars, score_lists, qs_department)
        statistics_data = command_utils.get_statistics_data(exam, statistics)
        command_utils.create_or_update_model(exam_vars.exam_model, ['statistics'], statistics_data)

        # Update answer_count_model
        answer_lists = command_utils.get_answer_lists(qs_student, exam_vars.answer_fields)
        count_lists = command_utils.get_count_lists(exam_vars, exam, answer_lists)
        answer_fields = exam_vars.count_fields + ['count_multiple', 'count_total', 'answer']
        answer_count_data = command_utils.get_answer_count_model_data(exam_vars, answer_fields, count_lists)
        command_utils.create_or_update_model(exam_vars.answer_count_model, answer_fields, answer_count_data)

        # Update answer_count_model by rank
        answer_lists_by_category = command_utils.get_total_answer_lists_by_category(exam_vars, exam, qs_student)
        total_count_dict = command_utils.get_total_count_dict_by_category(exam_vars, answer_lists_by_category)
        total_answer_count_data = command_utils.get_total_answer_count_model_data(
            exam_vars, ['all', 'filtered'], total_count_dict)
        command_utils.create_or_update_model(
            exam_vars.answer_count_model, ['all', 'filtered'], total_answer_count_data)

    return is_updated, message
