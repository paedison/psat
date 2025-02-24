import itertools
from datetime import timedelta, datetime

import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
from . import admin_index_utils
from ... import models, utils, forms, filters


class ViewConfiguration:
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
    url_psat_create = reverse_lazy('psat:admin-psat-create')
    url_problem_update = reverse_lazy('psat:admin-problem-update')

    url_predict_create = reverse_lazy('psat:admin-predict-create')

    url_study_category_detail = reverse_lazy('psat:admin-study-category-detail')
    url_study_category_upload = reverse_lazy('psat:admin-study-category-upload')
    url_study_category_create = reverse_lazy('psat:admin-study-category-create')

    url_study_curriculum_upload = reverse_lazy('psat:admin-study-curriculum-upload')
    url_study_curriculum_detail = reverse_lazy('psat:admin-study-curriculum-detail')
    url_study_organization_create = reverse_lazy('psat:admin-study-organization-create')
    url_study_curriculum_create = reverse_lazy('psat:admin-study-curriculum-create')
    url_study_student_create = reverse_lazy('psat:admin-study-student-create')
    url_study_answer_add = reverse_lazy('psat:admin-study-answer-add')


@admin_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    page_number = request.GET.get('page', '1')

    sub_title = utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    filterset = filters.PsatFilter(data=request.GET, request=request)
    predict_exam_list = models.PredictPsat.objects.select_related('psat')
    study_category_list = models.StudyCategory.objects.annotate_student_count()
    study_curriculum_list = models.StudyCurriculum.objects.annotate_student_count()
    context = update_context_data(config=config, sub_title=sub_title, psat_form=filterset.form)
    template_name = 'a_psat/admin_list.html'

    if view_type == 'exam_list':
        page_obj, page_range = utils.get_paginator_data(filterset.qs, page_number)
        admin_index_utils.update_problem_count(page_obj)
        context = update_context_data(context, page_obj=page_obj, page_range=page_range)
        return render(request, f'{template_name}#exam_list', context)
    elif view_type == 'predict_exam_list':
        predict_page_obj, predict_page_range = utils.get_paginator_data(predict_exam_list, page_number)
        context = update_context_data(
            context, predict_page_obj=predict_page_obj, predict_page_range=predict_page_range)
        return render(request, f'{template_name}#study_category_list', context)
    elif view_type == 'study_category_list':
        category_page_obj, category_page_range = utils.get_paginator_data(study_category_list, page_number)
        admin_index_utils.update_category_statistics(category_page_obj)
        context = update_context_data(
            context, category_page_obj=category_page_obj, category_page_range=category_page_range)
        return render(request, f'{template_name}#study_category_list', context)
    elif view_type == 'study_curriculum_list':
        curriculum_page_obj, curriculum_page_range = utils.get_paginator_data(study_curriculum_list, page_number)
        admin_index_utils.update_curriculum_statistics(curriculum_page_obj)
        context = update_context_data(
            context, curriculum_page_obj=curriculum_page_obj, curriculum_page_range=curriculum_page_range)
        return render(request, f'{template_name}#study_curriculum_list', context)

    page_obj, page_range = utils.get_paginator_data(filterset.qs, page_number)
    admin_index_utils.update_problem_count(page_obj)
    predict_page_obj, predict_page_range = utils.get_paginator_data(predict_exam_list, page_number)
    category_page_obj, category_page_range = utils.get_paginator_data(study_category_list, page_number)
    admin_index_utils.update_category_statistics(category_page_obj)
    curriculum_page_obj, curriculum_page_range = utils.get_paginator_data(study_curriculum_list, page_number)
    admin_index_utils.update_curriculum_statistics(curriculum_page_obj)

    context = update_context_data(
        context,
        page_obj=page_obj, page_range=page_range,
        predict_page_obj=predict_page_obj, predict_page_range=predict_page_range,
        category_page_obj=category_page_obj, category_page_range=category_page_range,
        curriculum_page_obj=curriculum_page_obj, curriculum_page_range=curriculum_page_range,
    )

    return render(request, 'a_psat/admin_list.html', context)


@admin_required
def psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            psat = form.save(commit=False)
            exam = form.cleaned_data['exam']
            exam_order = {'행시': 1, '입시':2, '칠급': 3}
            psat.order = exam_order.get(exam)
            psat.save()
            admin_index_utils.create_problem_model_instances(psat, exam)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.PsatForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def psat_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.PsatActiveForm(request.POST)
        if form.is_valid():
            psat = get_object_or_404(models.Psat, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@admin_required
def problem_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 문제 업데이트'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            psat = get_object_or_404(models.Psat, year=year, exam=exam)

            file = request.FILES['file']
            df = pd.read_excel(file, header=0, index_col=0)

            answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
            keys = list(answer_symbol.keys())
            combinations = []
            for i in range(1, 6):
                combinations.extend(itertools.combinations(keys, i))

            replace_dict = {}
            for combination in combinations:
                key = ''.join(combination)
                value = int(''.join(str(answer_symbol[k]) for k in combination))
                replace_dict[key] = value

            df['answer'].replace(to_replace=replace_dict, inplace=True)
            df = df.infer_objects(copy=False)

            for index, row in df.iterrows():
                problem = models.Problem.objects.get(psat=psat, subject=row['subject'], number=row['number'])
                problem.paper_type = row['paper_type']
                problem.answer = row['answer']
                problem.question = row['question']
                problem.data = row['data']
                problem.save()

            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 합격 예측 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PredictPsatForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            original_psat = models.Psat.objects.get(year=year, exam=exam)

            new_predict_psat, _ = models.PredictPsat.objects.get_or_create(psat=original_psat)
            new_predict_psat.is_active = True
            new_predict_psat.page_opened_at = form.cleaned_data['page_opened_at']
            new_predict_psat.exam_started_at = form.cleaned_data['exam_started_at']
            new_predict_psat.exam_finished_at = form.cleaned_data['exam_finished_at']
            new_predict_psat.answer_predict_opened_at = form.cleaned_data['answer_predict_opened_at']
            new_predict_psat.answer_official_opened_at = form.cleaned_data['answer_official_opened_at']
            new_predict_psat.predict_closed_at = form.cleaned_data['predict_closed_at']
            new_predict_psat.save()

            admin_index_utils.create_predict_answer_count_model_instances(original_psat)
            admin_index_utils.create_predict_statistics_model_instances(original_psat)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.PredictPsatForm()
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
                admin_index_utils.upload_data_to_study_category_and_psat_model(xls)
            if 'problem' in xls.sheet_names:
                admin_index_utils.upload_data_to_study_problem_model(xls)
                admin_index_utils.update_study_psat_models()
                admin_index_utils.create_study_answer_count_models()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


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
                admin_index_utils.upload_data_to_study_curriculum_model(xls, curriculum_dict)
            if 'student' in xls.sheet_names:
                admin_index_utils.update_study_student_model(xls, curriculum_dict, student_dict)
                admin_index_utils.update_study_result_model()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
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

                admin_index_utils.bulk_create_or_update(
                    models.StudyAnswer, list_create, list_update, ['answer'])
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyAnswerForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


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
def study_curriculum_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 커리큘럼 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyCurriculumForm(request.POST, request.FILES)
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

            list_create = []
            list_update = []
            for lecture_number in range(1, lecture_nums + 1):
                lecture_theme = get_lecture_theme(lecture_nums, lecture_number)
                lecture_round, homework_round = get_lecture_and_homework_round(lecture_number)
                lecture_open_datetime, homework_end_datetime, lecture_datetime = get_lecture_datetimes(
                    lecture_start_datetime, lecture_number)
                try:
                    schedule = models.StudyCurriculumSchedule.objects.get(
                        curriculum=curriculum, lecture_number=lecture_number)
                    fields_not_match = [
                        schedule.lecture_theme != lecture_theme,
                        schedule.lecture_round != lecture_round,
                        schedule.homework_round != homework_round,
                        schedule.lecture_open_datetime != lecture_open_datetime,
                        schedule.homework_end_datetime != homework_end_datetime,
                        schedule.lecture_datetime != lecture_datetime,
                    ]
                    if any(fields_not_match):
                        schedule.lecture_theme = lecture_theme
                        schedule.lecture_round = lecture_round
                        schedule.homework_round = homework_round
                        schedule.lecture_open_datetime = lecture_open_datetime
                        schedule.homework_end_datetime = homework_end_datetime
                        schedule.lecture_datetime = lecture_datetime
                        list_update.append(schedule)
                except models.StudyCurriculumSchedule.DoesNotExist:
                    list_create.append(
                        models.StudyCurriculumSchedule(
                            curriculum=curriculum,
                            lecture_number=lecture_number,
                            lecture_theme=lecture_theme,
                            lecture_round=lecture_round,
                            homework_round=homework_round,
                            lecture_open_datetime=lecture_open_datetime,
                            homework_end_datetime=homework_end_datetime,
                            lecture_datetime=lecture_datetime,
                        )
                    )
            update_fields = [
                'lecture_number', 'lecture_theme', 'lecture_round', 'homework_round',
                'lecture_open_datetime', 'homework_end_datetime', 'lecture_datetime'
            ]
            admin_index_utils.bulk_create_or_update(
                models.StudyCurriculumSchedule, list_create, list_update, update_fields)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCurriculumForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


def get_lecture_theme(lecture_nums, lecture_number) -> int:
    if lecture_nums <= 15:
        return lecture_number
    else:
        if lecture_number < 15:
            return lecture_number
        elif lecture_number == 15:
            return 0
        else:
            return 15


def get_lecture_and_homework_round(lecture_number) -> tuple:
    lecture_round = None
    homework_round = None
    if 3 <= lecture_number <= 14:
        lecture_round = lecture_number - 2
    if 2 <= lecture_number <= 13:
        homework_round = lecture_number - 1
    return lecture_round, homework_round


def get_lecture_datetimes(lecture_start_datetime: datetime, lecture_number) -> tuple:
    lecture_datetime = lecture_start_datetime + timedelta(days=7) * (lecture_number - 1)

    if lecture_number == 8:
        lecture_open_datetime = lecture_datetime - timedelta(days=14)
    else:
        lecture_open_datetime = lecture_datetime - timedelta(days=7)
    lecture_open_datetime = lecture_open_datetime.replace(hour=11, minute=0, second=0)

    homework_end_datetime = (lecture_datetime - timedelta(days=1)).replace(
        hour=23, minute=59, second=59, microsecond=999999)

    if lecture_number == 8:
        lecture_datetime = None
    return lecture_open_datetime, homework_end_datetime, lecture_datetime


@admin_required
def study_student_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 학생 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.StudyStudentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            admin_index_utils.update_study_result_model(student=student)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyStudentCreateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)
