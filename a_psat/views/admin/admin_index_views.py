import itertools
import traceback

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
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
    url_study_category_create = reverse_lazy('psat:admin-study-category-create')
    url_study_problem_add = reverse_lazy('psat:admin-study-problem-add')

    url_study_curriculum_detail = reverse_lazy('psat:admin-study-curriculum-detail')
    url_study_organization_create = reverse_lazy('psat:admin-study-organization-create')
    url_study_curriculum_create = reverse_lazy('psat:admin-study-curriculum-create')
    url_study_student_add = reverse_lazy('psat:admin-study-student-add')
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

    page_obj, page_range = utils.get_paginator_data(filterset.qs, page_number)
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
        psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)

    predict_exam_list = models.PredictPsat.objects.all()
    predict_page_obj, predict_page_range = utils.get_paginator_data(predict_exam_list, page_number)

    study_category_list = models.StudyCategory.objects.all()
    study_category_page_obj, study_category_page_range = utils.get_paginator_data(study_category_list, page_number)

    study_curriculum_list = models.StudyCurriculum.objects.all()
    study_page_obj, study_page_range = utils.get_paginator_data(study_curriculum_list, page_number)

    context = update_context_data(
        config=config, sub_title=sub_title, psat_form=filterset.form,
        page_obj=page_obj, page_range=page_range,
        predict_page_obj=predict_page_obj, predict_page_range=predict_page_range,
        study_category_page_obj=study_category_page_obj, study_category_page_range=study_category_page_range,
        study_page_obj=study_page_obj, study_page_range=study_page_range,
    )
    if view_type == 'exam_list':
        template_name = 'a_psat/admin_list.html#exam_list'
        return render(request, template_name, context)
    elif view_type == 'study_category_list':
        template_name = 'a_psat/admin_list.html#study_category_list'
        return render(request, template_name, context)

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
            list_create = []

            def append_list(problem_count: int, *subject_list):
                for subject in subject_list:
                    for number in range(1, problem_count + 1):
                        problem_info = {'psat': psat, 'subject': subject, 'number': number}
                        try:
                            models.Problem.objects.get(**problem_info)
                        except models.Problem.DoesNotExist:
                            list_create.append(models.Problem(**problem_info))

            if exam in ['행시', '입시']:
                append_list(40, '언어', '자료', '상황')
                append_list(25, '헌법')
            elif exam in ['칠급']:
                append_list(25, '언어', '자료', '상황')

            bulk_create_or_update(models.Problem, list_create, [], [])
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

            problems = models.Problem.objects.filter(psat=original_psat).order_by('id')
            model_list = [
                models.PredictAnswerCount,
                models.PredictAnswerCountTopRank,
                models.PredictAnswerCountMidRank,
                models.PredictAnswerCountLowRank,
            ]
            for model in model_list:
                list_create = []
                for problem in problems:
                    append_list_create(model, list_create, problem=problem)
                bulk_create_or_update(model, list_create, [], [])

            department_list = list(
                models.PredictCategory.objects.filter(exam=original_psat.exam).order_by('order')
                .values_list('department', flat=True)
            )
            department_list.insert(0, '전체')

            list_create = []
            for department in department_list:
                append_list_create(
                    models.PredictStatistics, list_create, psat=original_psat, department=department)
            bulk_create_or_update(models.PredictStatistics, list_create, [], [])

            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.PredictPsatForm()
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
def study_problem_add_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 문제 추가'
    context = update_context_data(config=config, title=title)

    list_update = []
    list_create = []

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_excel(file, sheet_name='problem', header=0)

            problem_list = models.StudyProblem.objects.annotate(
                psat_info=Concat(
                    F('psat__category__season'), Value('-'),
                    F('psat__category__study_type'), Value('-'),
                    F('psat__round'), Value('-'), F('number'),
                    output_field=CharField(),
                )
            ).values_list('psat_info', flat=True)

            for _, row in df.iterrows():
                season = row['season']
                study_type = row['study_type']
                study_round = row['round']
                round_problem_number = row['round_problem_number']

                year = row['year']
                exam = row['exam']
                subject = row['subject']
                number = row['number']

                prob_info = '-'.join([str(season), study_type, str(study_round), str(number)])
                if prob_info not in problem_list:
                    study_psat = models.StudyPsat.objects.get(
                        category__season=season, category__study_type=study_type, round=study_round)
                    problem = models.Problem.objects.get(
                        psat__year=year, psat__exam=exam, subject=subject, number=number)

                    try:
                        study_problem = models.StudyProblem.objects.get(
                            psat=study_psat, number=round_problem_number)
                        if study_problem.problem != problem:
                            study_problem.problem = problem
                            list_update.append(study_problem)
                    except models.StudyProblem.DoesNotExist:
                        study_problem = models.StudyProblem(
                            psat=study_psat, number=round_problem_number, problem=problem)
                        list_create.append(study_problem)
                    except ValueError as error:
                        print(error)

            update_fields = ['psat', 'number', 'problem']
            bulk_create_or_update(models.StudyProblem, list_create, list_update, update_fields)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.UploadFileForm()
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
            form.save()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyCurriculumForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


@admin_required
def study_student_add_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 스터디 학생 추가'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_excel(file, sheet_name='attendance', header=0)

            study_student_dict: dict[str, models.StudyStudent] = {}
            study_students = models.StudyStudent.objects.all()
            for s in study_students:
                study_student_dict[f'{s.curriculum_info}-{s.student_info}'] = s

            for _, row in df.iterrows():
                year = row['year']
                organization_name = row['organization_name']
                semester = row['semester']
                serial = row['serial']
                name = row['name']

                student_info = '-'.join([organization_name, str(year), str(semester), str(serial), name])
                if student_info in study_student_dict.keys():
                    study_student = study_student_dict[student_info]
                    if not hasattr(study_student, 'score') or not hasattr(study_student, 'rank'):
                        models.StudyScore.objects.get_or_create(student=study_student)
                        models.StudyRank.objects.get_or_create(student=study_student)
                else:
                    study_curriculum = models.StudyCurriculum.objects.get(
                        year=year, organization__name=organization_name, semester=semester)
                    study_student, _ = models.StudyStudent.objects.get_or_create(
                        curriculum=study_curriculum, serial=serial)
                    if study_student.name != name:
                        study_student.name = name
                        study_student.save()
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
    title = 'PSAT 스터디 답안 추가'
    context = update_context_data(config=config, title=title)

    list_update = []
    list_create = []

    if request.method == 'POST':
        form = forms.StudyAnswerForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_excel(file, header=0)
            df = df.dropna()

            study_curriculum = form.cleaned_data['curriculum']
            study_answer_list = (
                models.StudyAnswer.objects.filter(student__curriculum=study_curriculum)
                .annotate(
                    answer_info=Concat(
                        F('student__serial'), Value('-'),
                        F('problem__psat__round'), Value('-'),
                        F('problem__number'), Value('-'),
                        output_field=CharField(),
                    )
                )
                .values_list('answer_info', flat=True)
            )

            study_student_dict = {}
            study_students = models.StudyStudent.objects.filter(curriculum=study_curriculum)
            for s in study_students:
                study_student_dict[s.serial] = s

            study_problem_dict = {}
            study_problems = models.StudyProblem.objects.filter(psat__category__curriculum=study_curriculum)
            for p in study_problems:
                study_problem_dict[f'{p.psat.round}-{p.number}'] = p

            ref_serial = None
            study_student = None
            for _, row in df.iterrows():
                serial = row['serial']
                study_round = row['round']
                number = row['round_problem_number']
                answer = row['answer']

                if serial != ref_serial:
                    ref_serial = serial
                    study_student = study_student_dict[str(serial)]

                answer_info = '-'.join([str(serial), str(study_round), str(number)])
                if answer_info not in study_answer_list and answer:
                    study_problem = study_problem_dict[f'{study_round}-{number}']

                    try:
                        study_answer = models.StudyAnswer.objects.get(
                            student=study_student, problem=study_problem)
                        if study_answer.answer != answer:
                            study_answer.answer = answer
                            list_update.append(study_answer)

                    except models.StudyAnswer.DoesNotExist:
                        study_answer = models.StudyAnswer(
                            student=study_student, problem=study_problem, answer=answer)
                        list_create.append(study_answer)
                    except ValueError as error:
                        print(error)

            update_fields = ['psat', 'number', 'problem']
            bulk_create_or_update(models.StudyAnswer, list_create, list_update, update_fields)
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_psat/admin_form.html', context)

    form = forms.StudyAnswerForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_psat/admin_form.html', context)


def append_list_create(model, list_create, **kwargs):
    try:
        model.objects.get(**kwargs)
    except model.DoesNotExist:
        list_create.append(model(**kwargs))


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated
