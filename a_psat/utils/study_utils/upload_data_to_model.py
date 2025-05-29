from collections import defaultdict
from datetime import timedelta

import pandas as pd

from a_psat import models
from a_psat.utils.decorators import *
from a_psat.utils.modify_models_methods import *


@for_admin_views
@with_bulk_create_or_update()
def admin_update_curriculum_schedule_model(lecture_nums, lecture_start_datetime, curriculum):
    list_create, list_update = [], []
    for lecture_number in range(1, lecture_nums + 1):
        if lecture_nums <= 15:
            lecture_theme = lecture_number
        else:
            if lecture_number < 15:
                lecture_theme = lecture_number
            elif lecture_number == 15:
                lecture_theme = 0
            else:
                lecture_theme = 15

        lecture_round, homework_round = None, None
        if 3 <= lecture_number <= 14:
            lecture_round = lecture_number - 2
        if 2 <= lecture_number <= 13:
            homework_round = lecture_number - 1

        lecture_datetime = lecture_start_datetime + timedelta(days=7) * (lecture_number - 1)
        reserved_days_for_open = 14 if lecture_number == 8 else 7
        lecture_open_datetime = lecture_datetime - timedelta(days=reserved_days_for_open)
        lecture_open_datetime = lecture_open_datetime.replace(hour=11, minute=0, second=0)
        homework_end_datetime = (lecture_datetime + timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999)

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
    return models.StudyCurriculumSchedule, list_create, list_update, update_fields


@for_admin_views
@with_bulk_create_or_update()
def admin_create_result_model_instances_of_student(student: models.StudyStudent):
    psats = models.StudyPsat.objects.filter(category=student.curriculum.category)
    list_create = []
    for psat in psats:
        try:
            models.StudyResult.objects.get(student=student, psat=psat)
        except models.StudyResult.DoesNotExist:
            list_create.append(models.StudyResult(student=student, psat=psat))
    return models.StudyResult, list_create, [], []


@for_admin_views
@with_bulk_create_or_update()
def admin_upload_category_data_to_category_and_psat_model(row: pd.Series):
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

    list_create, list_update = [], []
    for rnd in range(1, study_round + 1):
        try:
            models.StudyPsat.objects.get(category=category, round=rnd)
        except models.StudyPsat.DoesNotExist:
            list_create.append(models.StudyPsat(category=category, round=rnd))
    return models.StudyPsat, list_create, list_update, []


@for_admin_views
@with_bulk_create_or_update()
def admin_upload_category_data_to_problem_model(df: pd.DataFrame):
    psat_dict: dict[tuple, models.StudyPsat] = {}
    for p in models.StudyPsat.objects.with_select_related():
        psat_dict[(p.category.season, p.category.study_type, p.round)] = p

    problem_dict: dict[tuple, models.StudyProblem] = {}
    for p in models.StudyProblem.objects.with_select_related():
        problem_dict[(p.psat.category.season, p.psat.category.study_type, p.psat.round, p.number)] = p

    list_create, list_update = [], []
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
    return models.StudyProblem, list_create, list_update, []


@for_admin_views
def admin_update_problem_counts_in_psat_model_instances():
    problem_count_list = models.StudyProblem.objects.get_ordered_qs_by_subject_field()
    problem_count_dict = defaultdict(dict)
    for p in problem_count_list:
        problem_count_dict[p['psat_id']][p['subject']] = p['count']
    for psat in models.StudyPsat.objects.all():
        problem_counts = problem_count_dict[psat.id]
        problem_counts['total'] = sum(problem_counts.values())
        psat.problem_counts = problem_counts
        psat.save()


@for_admin_views
def admin_create_answer_count_model_instances():
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


@for_admin_views
@with_bulk_create_or_update()
def admin_upload_data_to_curriculum_model(df: pd.DataFrame, curriculum_dict: dict):
    category_dict: dict[tuple, models.StudyCategory] = {}
    for c in models.StudyCategory.objects.all():
        category_dict[(c.season, c.study_type)] = c

    organization_dict: dict[str, models.StudyOrganization] = {}
    for o in models.StudyOrganization.objects.all():
        organization_dict[o.name] = o

    list_create, list_update = [], []
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
    return models.StudyCurriculum, list_create, list_update, ['category', 'name']


@for_admin_views
@with_bulk_create_or_update()
def admin_upload_data_to_student_model(df: pd.DataFrame, curriculum_dict, student_dict):
    list_create, list_update = [], []
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
    return models.StudyStudent, list_create, list_update, ['name']


@for_admin_views
@with_bulk_create_or_update()
def admin_create_result_model_instances():
    psat_dict: dict[models.StudyCategory, list[models.StudyPsat]] = defaultdict(list)
    for p in models.StudyPsat.objects.with_select_related():
        psat_dict[p.category].append(p)

    result_dict: dict[tuple[models.StudyStudent, models.StudyPsat], models.StudyResult] = defaultdict()
    for r in models.StudyResult.objects.select_related('student', 'psat'):
        result_dict[(r.student, r.psat)] = r

    list_create = []
    for s in models.StudyStudent.objects.with_select_related():
        psats = psat_dict[s.curriculum.category]
        for p in psats:
            if (s, p) not in result_dict.keys():
                list_create.append(models.StudyResult(student=s, psat=p))
    return models.StudyResult, list_create, [], []


@for_admin_views
def admin_upload_data_to_answer_model(df: pd.DataFrame,  study_curriculum):
    student_dict: dict[str, models.StudyStudent] = {}
    for s in models.StudyStudent.objects.with_select_related().filter(curriculum=study_curriculum):
        student_dict[s.serial] = s

    for serial, row in df.iterrows():
        list_create, list_update = [], []
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

        bulk_create_or_update(models.StudyAnswer, list_create, list_update, ['answer'])
