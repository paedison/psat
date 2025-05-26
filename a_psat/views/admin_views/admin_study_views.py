import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from a_psat import models, forms
from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data, get_paginator_context
from ..normal_views import study_views
from ...utils import admin_view_utils


class ViewConfiguration:
    menu = menu_eng = 'psat_admin'
    menu_kor = 'PSAT 관리자'
    submenu = submenu_eng = 'study'
    submenu_kor = '스터디'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-study-list')


@admin_required
def study_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    page_number = request.GET.get('page', '1')

    sub_title = admin_view_utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    study_category_list = models.StudyCategory.objects.annotate_student_count()
    study_curriculum_list = models.StudyCurriculum.objects.annotate_student_count()
    context = update_context_data(config=config, sub_title=sub_title)
    template_name = 'a_psat/admin_study_list.html'

    if view_type == 'study_category_list':
        category_context = get_paginator_context(study_category_list, page_number)
        admin_view_utils.update_study_statistics(category_context['page_obj'])
        context = update_context_data(context, category_context=category_context)
        return render(request, f'{template_name}#study_category_list', context)
    elif view_type == 'study_curriculum_list':
        curriculum_context = get_paginator_context(study_curriculum_list, page_number)
        admin_view_utils.update_study_statistics(curriculum_context['page_obj'], True)
        context = update_context_data(context, curriculum_context=curriculum_context)
        return render(request, f'{template_name}#study_curriculum_list', context)

    category_context = get_paginator_context(study_category_list)
    curriculum_context = get_paginator_context(study_curriculum_list)
    admin_view_utils.update_study_statistics(category_context['page_obj'])
    admin_view_utils.update_study_statistics(curriculum_context['page_obj'], True)
    context = update_context_data(context, category_context=category_context, curriculum_context=curriculum_context)

    return render(request, 'a_psat/admin_study_list.html', context)


@admin_required
def study_detail_view(request: HtmxHttpRequest, study_type: str, pk: int):
    config = ViewConfiguration()
    config.study_type = study_type

    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    student_name = request.GET.get('student_name', '')

    curriculum, qs_schedule = None, None
    if study_type == 'category':
        category = get_object_or_404(models.StudyCategory, pk=pk)
        qs_psat = models.StudyPsat.objects.get_qs_psat(category)

        config.url_study_update = reverse_lazy('psat:admin-study-category-update', args=[category.pk])
        page_title = category.full_reference
        qs_student = models.StudyStudent.objects.get_filtered_qs_by_category_for_catalog(category)
        result_count_dict = models.StudyResult.objects.get_result_count_dict_by_category(category)
    else:
        curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)
        category = curriculum.category
        qs_psat = models.StudyPsat.objects.get_qs_psat(category)

        config.url_study_update = reverse_lazy('psat:admin-study-curriculum-update', args=[curriculum.pk])
        page_title = curriculum.full_reference
        qs_schedule = models.StudyCurriculumSchedule.objects.filter(curriculum=curriculum).order_by('-lecture_number')
        qs_student = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_catalog(curriculum)

        result_count_dict = models.StudyResult.objects.get_result_count_dict_by_curriculum(curriculum)
        data_statistics = admin_view_utils.get_study_data_statistics(qs_student)
        data_statistics_by_study_round = {}
        for d in data_statistics:
            data_statistics_by_study_round[d['study_round']] = d
        for p in qs_psat:
            p.statistics = data_statistics_by_study_round.get(p.round)

    study_rounds = '1' * category.round
    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(category)
    admin_view_utils.update_study_data_answers(qs_problem)

    context = update_context_data(
        config=config, category=category, curriculum=curriculum, study_rounds=study_rounds,
        page_title=page_title, icon_image=icon_set_new.ICON_IMAGE, icon_search=icon_set_new.ICON_SEARCH,
    )
    if view_type == 'lecture_list':
        context = update_context_data(
            context, lecture_context=admin_view_utils.get_study_lecture_context(qs_schedule, page_number))
        return render(request, 'a_psat/snippets/study_detail_lecture.html', context)
    if view_type == 'statistics_list':
        context = update_context_data(
            context, category_stat=admin_view_utils.get_study_score_stat_dict(qs_student),
            statistics_context=get_paginator_context(qs_psat, page_number))
        return render(request, 'a_psat/snippets/admin_detail_study_statistics.html', context)
    if view_type == 'catalog_list':
        catalog_context = get_paginator_context(
            qs_student, page_number, result_count=result_count_dict)
        context = update_context_data(context, catalog_context=catalog_context)
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'student_search':
        if student_name:
            qs_student = qs_student.filter(name=student_name)
        catalog_context = get_paginator_context(
            qs_student, page_number, result_count=result_count_dict)
        context = update_context_data(context, catalog_context=catalog_context)
        return render(request, 'a_psat/snippets/admin_detail_study_catalog.html', context)
    if view_type == 'answer_list':
        context = update_context_data(
            context, answer_context=get_paginator_context(qs_problem, page_number))
        return render(request, 'a_psat/snippets/admin_detail_study_answer_analysis.html', context)
    if view_type == 'problem_list':
        context = update_context_data(
            context, problem_context=get_paginator_context(qs_problem, page_number))
        return render(request, 'a_psat/snippets/admin_detail_study_problem_list.html', context)

    context = update_context_data(
        context, schedules=qs_schedule,
        lecture_context=admin_view_utils.get_study_lecture_context(qs_schedule, page_number),
        category_stat=admin_view_utils.get_study_score_stat_dict(qs_student),
        statistics_context=get_paginator_context(qs_psat),
        catalog_context=get_paginator_context(qs_student, result_count=result_count_dict),
        answer_context=get_paginator_context(qs_problem),
        problem_context=get_paginator_context(qs_problem),
    )
    return render(request, f'a_psat/admin_study_detail.html', context)


@admin_required
def study_category_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 카테고리 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            season = form.cleaned_data['season']
            study_type = form.cleaned_data['study_type']
            name = form.cleaned_data['name']
            category_round = form.cleaned_data['category_round']

            category, _ = models.StudyCategory.objects.get_or_create(season=season, study_type=study_type)
            category.name = name
            category.save()

            for rnd in range(1, category_round + 1):
                models.StudyPsat.objects.get_or_create(category=category, round=rnd)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCategoryForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_category_upload_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 카테고리 자료 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            xls = pd.ExcelFile(file)

            if 'category' in xls.sheet_names:
                admin_view_utils.upload_data_to_study_category_and_psat_model(xls)
            if 'problem' in xls.sheet_names:
                admin_view_utils.upload_data_to_study_problem_model(xls)
                admin_view_utils.update_study_psat_models()
                admin_view_utils.create_study_answer_count_models()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_category_update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    category = get_object_or_404(models.StudyCategory, pk=pk)

    context = {}
    next_url = request.headers.get('HX-Current-URL', request.META.get('HTTP_REFERER', '/'))

    qs_student = models.StudyStudent.objects.get_filtered_qs_by_category_for_catalog(category)
    psats = models.StudyPsat.objects.get_qs_psat(category)

    if view_type == 'score':
        is_updated, message = admin_view_utils.update_study_scores(qs_student, psats)
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = admin_view_utils.update_study_ranks(qs_student, psats)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = admin_view_utils.get_study_data_statistics(qs_student)
        is_updated, message = admin_view_utils.update_study_statistics_model(category, data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = admin_view_utils.update_study_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def study_curriculum_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 등록'
    context = update_context_data(config=config, title=title)

    view_type = request.headers.get('View-Type', '')
    if request.method == 'POST':
        form = forms.StudyCurriculumForm(request.POST, request.FILES)
        if view_type == 'category':
            organization_id = request.POST.get('organization')
            organization = models.StudyOrganization.objects.get(id=organization_id)
            semester = request.POST.get('semester')
            category_basic = models.StudyCategory.objects.filter(study_type='기본').first()
            category_advanced = models.StudyCategory.objects.filter(study_type='심화').first()
            category_set = {
                ('서울과기대', '1'): category_advanced,
                ('서울과기대', '2'): category_basic,
                ('한국외대', '1'): category_basic,
                ('한국외대', '2'): category_advanced,
            }
            category = category_set.get((organization.name, semester))
            if category:
                category_form = forms.StudyCurriculumCategoryForm(initial={'category': category})
            else:
                category_form = forms.StudyCurriculumCategoryForm()
            context = update_context_data(context, form=category_form)
            return render(request, 'a_psat/admin_form.html#form_field', context)
        if form.is_valid():
            year = form.cleaned_data['year']
            organization = form.cleaned_data['organization']
            semester = int(form.cleaned_data['semester'])
            category = form.cleaned_data['category']
            lecture_start_datetime = form.cleaned_data['lecture_start_datetime']
            lecture_nums = int(form.cleaned_data['lecture_nums'])
            curriculum_name = models.choices.study_curriculum_name()[organization.name][semester]

            curriculum, _ = models.StudyCurriculum.objects.get_or_create(
                year=year, organization=organization, semester=semester)
            curriculum.category = category
            curriculum.name = curriculum_name
            curriculum.save()

            admin_view_utils.update_study_curriculum_schedule_model(lecture_nums, lecture_start_datetime, curriculum)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCurriculumForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_curriculum_upload_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 자료 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            xls = pd.ExcelFile(file)

            # Get all StudyCurriculum data
            curriculum_dict: dict[tuple, models.StudyCurriculum] = {}
            for c in models.StudyCurriculum.objects.with_select_related():
                curriculum_dict[(c.organization.name, c.year, c.semester)] = c

            # Get all StudyStudent data
            student_dict: dict[tuple, models.StudyStudent] = {}
            for s in models.StudyStudent.objects.with_select_related():
                student_dict[(
                    s.curriculum.organization.name, s.curriculum.year, s.curriculum.semester, s.serial
                )] = s

            if 'curriculum' in xls.sheet_names:
                admin_view_utils.upload_data_to_study_curriculum_model(xls, curriculum_dict)
            if 'student' in xls.sheet_names:
                admin_view_utils.update_study_student_model(xls, curriculum_dict, student_dict)
                admin_view_utils.update_study_result_model()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_curriculum_update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    curriculum = get_object_or_404(models.StudyCurriculum, pk=pk)

    context = {}
    next_url = request.headers.get('HX-Current-URL', request.META.get('HTTP_REFERER', '/'))

    qs_curriculum_student = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_catalog(curriculum)
    psats = models.StudyPsat.objects.get_qs_psat(curriculum.category)

    if view_type == 'score':
        is_updated, message = admin_view_utils.update_study_scores(qs_curriculum_student, psats)
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    qs_category_student = models.StudyStudent.objects.get_filtered_qs_by_category_for_catalog(curriculum.category)
    if view_type == 'rank':
        is_updated, message = admin_view_utils.update_study_ranks(qs_category_student, psats)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = admin_view_utils.get_study_data_statistics(qs_category_student)
        is_updated, message = admin_view_utils.update_study_statistics_model(curriculum.category, data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = admin_view_utils.update_study_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@admin_required
def study_organization_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 교육기관 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyOrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyOrganizationForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_student_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 학생 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyStudentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            admin_view_utils.update_study_result_model(student=student)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyStudentCreateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_answer_add_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 답안 업로드'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyAnswerForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_excel(file, header=[0, 1], index_col=0)
            df.fillna(value=0, inplace=True)

            study_curriculum = form.cleaned_data['curriculum']

            student_dict: dict[str, models.StudyStudent] = {}
            for s in models.StudyStudent.objects.with_select_related().filter(curriculum=study_curriculum):
                student_dict[s.serial] = s

            problem_dict: dict[tuple[int, int], models.StudyProblem] = {}
            for p in models.StudyProblem.objects.with_select_related().filter(
                    psat__category__curriculum=study_curriculum):
                problem_dict[(p.psat.round, p.number)] = p

            for serial, row in df.iterrows():
                list_update = []
                list_create = []
                if str(serial) in student_dict.keys():
                    student = student_dict[str(serial)]
                    for col in df.columns[1:]:
                        study_round = col[0]
                        number = col[1]
                        answer = row[col]
                        if answer:
                            try:
                                study_answer = models.StudyAnswer.objects.get(
                                    student=student,
                                    problem__psat__category=study_curriculum.category,
                                    problem__psat__round=study_round,
                                    problem__number=number
                                )
                                if study_answer.answer != answer:
                                    study_answer.answer = answer
                                    list_update.append(study_answer)
                            except models.StudyAnswer.DoesNotExist:
                                problem = models.StudyProblem.objects.get(
                                    psat__category=study_curriculum.category,
                                    psat__round=study_round, number=number
                                )
                                study_answer = models.StudyAnswer(
                                    student=student, problem=problem, answer=answer)
                                list_create.append(study_answer)
                            except ValueError as error:
                                print(error)

                admin_view_utils.bulk_create_or_update(
                    models.StudyAnswer, list_create, list_update, ['answer'])
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyAnswerForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.StudyStudent = models.StudyStudent.objects.filter(pk=pk).first()
    if student:
        return study_views.study_detail_view(request, student.curriculum.id, student=student)
