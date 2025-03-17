import traceback
from collections import defaultdict
from datetime import timedelta, datetime

import django.db.utils
import pandas as pd
from django.db import transaction

from ... import models


def append_list_create(model, list_create, **kwargs):
    try:
        model.objects.get(**kwargs)
    except model.DoesNotExist:
        list_create.append(model(**kwargs))


def create_predict_answer_count_model_instances(original_psat):
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


def create_predict_statistics_model_instances(original_psat):
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


def create_problem_model_instances(psat, exam):
    list_create = []

    def append_list(problem_count: int, *subject_list):
        for subject in subject_list:
            for number in range(1, problem_count + 1):
                problem_info = {'psat': psat, 'subject': subject, 'number': number}
                append_list_create(models.Problem, list_create, **problem_info)

    if exam in ['행시', '입시']:
        append_list(40, '언어', '자료', '상황')
        append_list(25, '헌법')
    elif exam in ['칠급']:
        append_list(25, '언어', '자료', '상황')

    bulk_create_or_update(models.Problem, list_create, [], [])


def update_problem_count(page_obj):
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
        psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)


def update_study_statistics(page_obj, is_curriculum=False):
    for obj in page_obj:
        if is_curriculum:
            qs_student = models.StudyStudent.objects.filter(curriculum=obj, score_total__isnull=False)
        else:
            qs_student = models.StudyStudent.objects.filter(curriculum__category=obj, score_total__isnull=False)
        score_list = qs_student.values_list('score_total', flat=True)
        participants = len(score_list)
        sorted_scores = sorted(score_list, reverse=True)
        if sorted_scores:
            top_10_threshold = max(1, int(participants * 0.10))
            top_25_threshold = max(1, int(participants * 0.25))
            top_50_threshold = max(1, int(participants * 0.50))
            obj.max = sorted_scores[0]
            obj.t10 = sorted_scores[top_10_threshold - 1]
            obj.t25 = sorted_scores[top_25_threshold - 1]
            obj.t50 = sorted_scores[top_50_threshold - 1]
            obj.avg = round(sum(score_list) / participants, 1)


def upload_data_to_study_category_and_psat_model(excel_file):
    df = pd.read_excel(excel_file, sheet_name='category', header=0, index_col=0)

    for _, row in df.iterrows():
        season = row['season']
        study_type = row['study_type']
        name = row['name']
        study_round = row['round']
        update_expr = {'name': name, 'round': study_round}

        category, _ = models.StudyCategory.objects.get_or_create(season=season, study_type=study_type)
        fields_not_match = [getattr(category, k) != v for k, v in update_expr.items()]
        if any(fields_not_match):
            for key, val in update_expr.items():
                setattr(category, key, val)
            category.save()

        list_create = []
        for rnd in range(1, study_round + 1):
            try:
                models.StudyPsat.objects.get(category=category, round=rnd)
            except models.StudyPsat.DoesNotExist:
                list_create.append(models.StudyPsat(category=category, round=rnd))
        bulk_create_or_update(models.StudyPsat, list_create, [], [])


def upload_data_to_study_problem_model(excel_file):
    df = pd.read_excel(excel_file, sheet_name='problem', header=0)

    psat_dict: dict[tuple, models.StudyPsat] = {}
    for p in models.StudyPsat.objects.with_select_related():
        psat_dict[(p.category.season, p.category.study_type, p.round)] = p

    problem_dict: dict[tuple, models.StudyProblem] = {}
    for p in models.StudyProblem.objects.with_select_related():
        problem_dict[(p.psat.category.season, p.psat.category.study_type, p.psat.round, p.number)] = p

    list_create = []
    for _, row in df.iterrows():
        season = row['season']
        study_type = row['study_type']
        study_round = row['round']
        round_problem_number = row['round_problem_number']

        year = row['year']
        exam = row['exam']
        subject = row['subject']
        number = row['number']

        psat_key = (season, study_type, study_round)
        problem_key = (season, study_type, study_round, round_problem_number)
        if psat_key in psat_dict and problem_key not in problem_dict:
            psat = psat_dict[psat_key]
            try:
                problem = models.Problem.objects.get(
                    psat__year=year, psat__exam=exam, subject=subject, number=number)
                study_problem = models.StudyProblem(
                    psat=psat, number=round_problem_number, problem=problem)
                list_create.append(study_problem)
            except models.Problem.DoesNotExist:
                print(f'Problem with {year}{exam}{subject}-{number:02} does not exist.')

    bulk_create_or_update(models.StudyProblem, list_create, [], [])


def update_study_psat_models():
    problem_count_list = models.StudyProblem.objects.get_ordered_qs_by_subject_field()
    problem_count_dict = defaultdict(dict)
    for p in problem_count_list:
        problem_count_dict[p['psat_id']][p['subject']] = p['count']
    for psat in models.StudyPsat.objects.all():
        problem_counts = problem_count_dict[psat.id]
        problem_counts['total'] = sum(problem_counts.values())
        psat.problem_counts = problem_counts
        psat.save()


def create_study_answer_count_models():
    problems = models.StudyProblem.objects.order_by('id')
    model_dict = {
        'answer_count_top': models.StudyAnswerCount,
        'answer_count_top_rank': models.StudyAnswerCountTopRank,
        'answer_count_mid_rank': models.StudyAnswerCountMidRank,
        'answer_count_low_rank': models.StudyAnswerCountLowRank,
    }
    for related_name, model in model_dict.items():
        list_create = []
        for problem in problems:
            if not hasattr(problem, related_name):
                append_list_create(model, list_create, problem=problem)
        bulk_create_or_update(model, list_create, [], [])


def upload_data_to_study_curriculum_model(excel_file, curriculum_dict):
    df = pd.read_excel(excel_file, sheet_name='curriculum', header=0, index_col=0)

    category_dict: dict[tuple, models.StudyCategory] = {}
    for c in models.StudyCategory.objects.all():
        category_dict[(c.season, c.study_type)] = c

    organization_dict: dict[str, models.StudyOrganization] = {}
    for o in models.StudyOrganization.objects.all():
        organization_dict[o.name] = o

    list_create = []
    list_update = []
    for _, row in df.iterrows():
        organization_name = row['organization_name']
        curriculum_key = (row['organization_name'], row['year'], row['semester'])
        category_key = (row['category_season'], row['category_study_type'])

        if organization_name in organization_dict.keys() and category_key in category_dict.keys():
            organization = organization_dict[organization_name]
            category = category_dict[category_key]

            find_expr = {'organization': organization, 'year': curriculum_key[1], 'semester': curriculum_key[2]}
            update_expr = {'category': category, 'name': row['curriculum_name']}

            if curriculum_key in curriculum_dict.keys():
                curriculum = curriculum_dict[curriculum_key]
                fields_not_match = [getattr(curriculum, k) != v for k, v in update_expr.items()]
                if any(fields_not_match):
                    for key, val in update_expr.items():
                        setattr(curriculum, key, val)
                    list_update.append(curriculum)
            else:
                list_create.append(models.StudyCurriculum(**find_expr, **update_expr))
    update_fields = ['category', 'name']
    bulk_create_or_update(models.StudyCurriculum, list_create, list_update, update_fields)


def update_study_student_model(excel_file, curriculum_dict, student_dict):
    df = pd.read_excel(
        excel_file, sheet_name='student', header=0, index_col=0, dtype={'serial': str})

    list_create = []
    list_update = []
    for _, row in df.iterrows():
        year = row['year']
        organization_name = row['organization_name']
        semester = row['semester']
        serial = row['serial']
        name = row['name']

        curriculum_key = (organization_name, year, semester)
        student_key = (organization_name, year, semester, serial)
        if student_key in student_dict.keys():
            student = student_dict[student_key]
            if student.name != name:
                student.name = name
                list_update.append(student)
        else:
            if curriculum_key in curriculum_dict.keys():
                curriculum = curriculum_dict[curriculum_key]
                list_create.append(
                    models.StudyStudent(curriculum=curriculum, serial=serial, name=name)
                )
    bulk_create_or_update(models.StudyStudent, list_create, list_update, ['name'])


def update_study_result_model(student: models.StudyStudent | None = None):
    if student is None:
        # Get all StudyPsat data
        psat_dict: dict[models.StudyCategory, list[models.StudyPsat]] = {}
        for p in models.StudyPsat.objects.with_select_related():
            if p.category not in psat_dict.keys():
                psat_dict[p.category] = []
            psat_dict[p.category].append(p)

        # Get all StudyResult data
        result_dict: dict[tuple[models.StudyStudent, models.StudyPsat], models.StudyResult] = {}
        for r in models.StudyResult.objects.select_related('student', 'psat'):
            result_dict[(r.student, r.psat)] = r

        list_create = []
        for s in models.StudyStudent.objects.with_select_related():
            psats = psat_dict[s.curriculum.category]
            for p in psats:
                if (s, p) not in result_dict.keys():
                    list_create.append(models.StudyResult(student=s, psat=p))
        bulk_create_or_update(models.StudyResult, list_create, [], [])
    else:
        psats = models.StudyPsat.objects.filter(category=student.curriculum.category)
        list_create = []
        for psat in psats:
            try:
                models.StudyResult.objects.get(student=student, psat=psat)
            except models.StudyResult.DoesNotExist:
                list_create.append(models.StudyResult(student=student, psat=psat))
        bulk_create_or_update(models.StudyResult, list_create, [], [])


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

    homework_end_datetime = (lecture_datetime + timedelta(days=6)).replace(
        hour=23, minute=59, second=59, microsecond=999999)

    if lecture_number == 8:
        lecture_datetime = None
    return lecture_open_datetime, homework_end_datetime, lecture_datetime


def update_study_curriculum_schedule_model(lecture_nums, lecture_start_datetime, curriculum):
    list_create = []
    list_update = []
    for lecture_number in range(1, lecture_nums + 1):
        lecture_theme = get_lecture_theme(lecture_nums, lecture_number)
        lecture_round, homework_round = get_lecture_and_homework_round(lecture_number)
        lecture_open_datetime, homework_end_datetime, lecture_datetime = get_lecture_datetimes(
            lecture_start_datetime, lecture_number)
        find_expr = {'curriculum': curriculum, 'lecture_number': lecture_number}
        matching_expr = {
            'lecture_theme': lecture_theme,
            'lecture_round': lecture_round,
            'homework_round': homework_round,
            'lecture_open_datetime': lecture_open_datetime,
            'homework_end_datetime': homework_end_datetime,
            'lecture_datetime': lecture_datetime,
        }
        try:
            schedule = models.StudyCurriculumSchedule.objects.get(**find_expr)
            fields_not_match = [getattr(schedule, key) != val for key, val in matching_expr.items()]
            if any(fields_not_match):
                for key, val in matching_expr.items():
                    setattr(schedule, key, val)
                list_update.append(schedule)
        except models.StudyCurriculumSchedule.DoesNotExist:
            list_create.append(models.StudyCurriculumSchedule(**find_expr, **matching_expr))
    update_fields = [
        'lecture_number', 'lecture_theme', 'lecture_round', 'homework_round',
        'lecture_open_datetime', 'homework_end_datetime', 'lecture_datetime'
    ]
    bulk_create_or_update(models.StudyCurriculumSchedule, list_create, list_update, update_fields)


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
