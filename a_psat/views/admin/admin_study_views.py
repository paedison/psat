from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
from . import admin_utils
from ... import models, utils


class ViewConfiguration:
    current_time = timezone.now()

    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-list')


def detail_view(request: HtmxHttpRequest, study_type: str, pk: int):
    config = ViewConfiguration()
    config.study_type = study_type

    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    student_name = request.GET.get('student_name', '')

    if study_type == 'category':
        category = get_object_or_404(models.StudyCategory, pk=pk)
        curriculum = None
    else:
        curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)
        category = curriculum.category
    qs_schedule = models.StudyCurriculumSchedule.objects.filter(curriculum=curriculum).order_by('-lecture_number')

    config.url_study_category_update = reverse_lazy('psat:admin-study-category-update', args=[category.pk])

    qs_psat = models.StudyPsat.objects.get_qs_psat(category)
    if study_type == 'category':
        qs_student = models.StudyStudent.objects.get_filtered_qs_by_category_for_catalog(category)
    else:
        qs_student = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_catalog(curriculum)
        data_statistics = admin_utils.get_data_statistics(qs_student)
        data_statistics_by_study_round = {}
        for d in data_statistics:
            data_statistics_by_study_round[d['study_round']] = d
        for p in qs_psat:
            p.statistics = data_statistics_by_study_round.get(p.round)

    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(category)
    admin_utils.update_data_answers(qs_problem)

    if study_type == 'category':
        page_title = category.full_reference
    else:
        page_title = curriculum.full_reference

    context = update_context_data(
        config=config, category=category, curriculum=curriculum, page_title=page_title,
        icon_image=icon_set_new.ICON_IMAGE, icon_search=icon_set_new.ICON_SEARCH,
    )
    if view_type == 'lecture':
        lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
        admin_utils.update_lecture_paginator_data(lecture_page_obj)
        context = update_context_data(
            context, lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range)
        return render(request, 'a_psat/snippets/study_list_lecture.html', context)
    if view_type == 'statistics_list':
        category_stat = admin_utils.get_score_stat_dict(qs_student)
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(qs_psat, page_number)
        context = update_context_data(
            context, category_stat=category_stat,
            statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range
        )
        return render(request, 'a_psat/snippets/admin_detail_study_statistics.html', context)
    if view_type == 'catalog_list':
        study_rounds = '1' * category.round
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(qs_student, page_number)
        context = update_context_data(
            context, study_rounds=study_rounds,
            catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        )
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'student_search':
        study_rounds = '1' * category.round
        if student_name:
            searched_student = qs_student.filter(name=student_name)
        else:
            searched_student = qs_student
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
        context = update_context_data(
            context, study_rounds=study_rounds,
            catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'answer_list':
        answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)
        context = update_context_data(
            context, answer_page_obj=answer_page_obj, answer_page_range=answer_page_range)
        return render(request, 'a_psat/snippets/admin_detail_study_answer_analysis.html', context)
    if view_type == 'problem_list':
        problem_page_obj, problem_page_range = utils.get_paginator_data(qs_problem, page_number)
        context = update_context_data(
            context, problem_page_obj=problem_page_obj, problem_page_range=problem_page_range)
        return render(request, 'a_psat/snippets/study_problem_list_content.html', context)

    category_stat = admin_utils.get_score_stat_dict(qs_student)
    study_rounds = '1' * category.round

    lecture_page_obj, lecture_page_range = utils.get_paginator_data(qs_schedule, page_number, 4)
    admin_utils.update_lecture_paginator_data(lecture_page_obj)
    statistics_page_obj, statistics_page_range = utils.get_paginator_data(qs_psat, page_number)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(qs_student, page_number)
    answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)
    problem_page_obj, problem_page_range = utils.get_paginator_data(qs_problem, page_number)
    context = update_context_data(
        context, category_stat=category_stat, study_rounds=study_rounds,
        lecture_page_obj=lecture_page_obj, lecture_page_range=lecture_page_range,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answer_page_obj=answer_page_obj, answer_page_range=answer_page_range,
        problem_page_obj=problem_page_obj, problem_page_range=problem_page_range,
    )
    return render(request, f'a_psat/admin_detail_study.html', context)


@admin_required
def category_update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    category = get_object_or_404(models.StudyCategory, pk=pk)

    context = {}
    next_url = request.headers.get('HX-Current-URL', request.META.get('HTTP_REFERER', '/'))

    qs_student = models.StudyStudent.objects.get_filtered_qs_by_category_for_catalog(category)
    psats = models.StudyPsat.objects.get_qs_psat(category)

    if view_type == 'score':
        is_updated, message = admin_utils.update_scores(qs_student, psats)
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = admin_utils.update_ranks(qs_student, psats)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = admin_utils.get_data_statistics(qs_student)
        is_updated, message = admin_utils.update_statistics_model(category, data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = admin_utils.update_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)
