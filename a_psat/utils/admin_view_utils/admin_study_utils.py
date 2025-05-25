from collections import defaultdict
from datetime import timedelta, datetime

import pandas as pd
from django.db.models import Count, F
from django.urls import reverse_lazy

from a_psat import models
from . import common_utils


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


def update_lecture_paginator_data(lecture_page_obj):
    lecture_dict = {}
    for lec in models.Lecture.objects.all():
        lecture_dict[(lec.subject, lec.order)] = lec.id

    for obj in lecture_page_obj:
        obj: models.StudyCurriculumSchedule
        theme = obj.get_lecture_theme_display()

        lecture_id = color_code = None
        if '언어' in theme:
            color_code = 'primary'
            lecture_id = lecture_dict[('언어', int(theme[-1]))]
        elif '자료' in theme:
            color_code = 'success'
            lecture_id = lecture_dict[('자료', int(theme[-1]))]
        elif '상황' in theme:
            color_code = 'warning'
            lecture_id = lecture_dict[('상황', int(theme[-1]))]
        elif '시험' in theme:
            color_code = 'danger'
        obj.color_code = color_code
        obj.lecture_topic = models.choices.study_lecture_topic().get(obj.get_lecture_theme_display())
        if lecture_id:
            obj.url_lecture = reverse_lazy('psat:lecture-detail', args=[lecture_id])
        if '공부법' in theme:
            lecture_ids = [lecture_dict[('공부', i)] for i in range(1, 4)]
            obj.url_lecture_list = [
                reverse_lazy('psat:lecture-detail', args=[l_id]) for l_id in lecture_ids
            ]


def update_study_data_answers(qs_problem):
    for entry in qs_problem:
        ans_official = entry.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        entry.no = entry.number
        entry.ans_official = ans_official
        entry.ans_official_circle = entry.problem.get_answer_display()
        entry.ans_list = answer_official_list

        entry.rate_correct = entry.answer_count.get_answer_rate(ans_official)
        entry.rate_correct_top = entry.answer_count_top_rank.get_answer_rate(ans_official)
        entry.rate_correct_mid = entry.answer_count_mid_rank.get_answer_rate(ans_official)
        entry.rate_correct_low = entry.answer_count_low_rank.get_answer_rate(ans_official)
        try:
            entry.rate_gap = entry.rate_correct_top - entry.rate_correct_low
        except TypeError:
            entry.rate_gap = None


def get_study_score_stat_dict(qs_student) -> dict:
    # stat_dict keys: participants, max, avg, t10, t25, t50
    stat_dict = models.get_study_statistics_aggregation(qs_student)
    participants = stat_dict['participants']
    if participants == 0:
        return {}

    score_list = list(qs_student.values_list('score_total', flat=True))

    def get_score(rank_rate: float):
        threshold = max(1, int(participants * rank_rate))
        return score_list[threshold] if threshold < participants else None

    stat_dict['t10'] = get_score(0.10)
    stat_dict['t25'] = get_score(0.25)
    stat_dict['t50'] = get_score(0.50)
    return stat_dict


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
        common_utils.bulk_create_or_update(models.StudyPsat, list_create, [], [])


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

    common_utils.bulk_create_or_update(models.StudyProblem, list_create, [], [])


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
                common_utils.append_list_create(model, list_create, problem=problem)
        common_utils.bulk_create_or_update(model, list_create, [], [])


def update_study_scores(qs_student, psats):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = []

    # Update StudyResult for score
    for qs_s in qs_student:
        qs_result = models.StudyResult.objects.filter(student=qs_s, psat__in=psats)
        list_update = []
        for qs_r in qs_result:
            qs_answer = models.StudyAnswer.objects.filter(student=qs_r.student, problem__psat=qs_r.psat)
            if not qs_answer.exists():
                score = None
            else:
                score = 0
                for qs_a in qs_answer:
                    answer_correct_list = {int(digit) for digit in str(qs_a.answer_correct)}
                    if qs_a.answer in answer_correct_list:
                        score += 1
            if qs_r.score != score:
                qs_r.score = score
                list_update.append(qs_r)
        is_updated_list.append(common_utils.bulk_create_or_update(
            models.StudyResult, [], list_update, ['score']))

    # Update StudyStudent for score_total
    list_update = []
    student_scores = models.get_study_student_score_calculated_annotation(qs_student)
    for student in student_scores:
        if student.score_total != student.score_calculated:
            student.score_total = student.score_calculated
            list_update.append(student)
    is_updated_list.append(common_utils.bulk_create_or_update(
        models.StudyStudent, [], list_update, ['score_total']))

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_study_ranks(qs_student, psats):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '등수를 업데이트했습니다.',
        False: '기존 등수와 일치합니다.',
    }
    is_updated_list = []

    # Update StudyResult for rank
    list_update = []
    ranked_results = models.StudyResult.objects.get_rank_calculated(qs_student, psats)
    for result in ranked_results:
        if result.rank_calculated != models.StudyResult.objects.get(id=result.id).rank:
            result.rank = result.rank_calculated
            list_update.append(result)
    is_updated_list.append(
        common_utils.bulk_create_or_update(models.StudyResult, [], list_update, ['rank']))

    # Update StudyStudent for score_total
    list_update = []
    ranked_students = models.get_study_student_total_rank_calculated_annotation(qs_student)
    for student in ranked_students:
        if student.rank_total != student.rank_calculated:
            student.rank_total = student.rank_calculated
            list_update.append(student)
    is_updated_list.append(
        common_utils.bulk_create_or_update(models.StudyStudent, [], list_update, ['rank_total']))

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_study_statistics_model(category, data_statistics):
    model = models.StudyPsat
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    list_update = []
    list_create = []

    round_num = models.StudyPsat.objects.filter(category=category).count()
    participants_num = models.StudyStudent.objects.filter(curriculum__category=category).count()
    if category.round != round_num or category.participants != participants_num:
        category.round = round_num
        category.participants = participants_num
        category.save()
        category.refresh_from_db()

    for data_stat in data_statistics[1:]:
        study_round = data_stat['study_round']
        try:
            new_query = model.objects.get(category=category, round=study_round)
            fields_not_match = any(
                new_query.statistics.get(fld) != val for fld, val in data_stat.items()
            )
            if fields_not_match:
                new_query.statistics = data_stat
                list_update.append(new_query)
        except model.DoesNotExist:
            list_create.append(model(category=category, **data_stat))
    is_updated = common_utils.bulk_create_or_update(model, list_create, list_update, ['statistics'])
    return is_updated, message_dict[is_updated]


def get_study_data_statistics(qs_student):
    data_statistics = []
    score_dict = defaultdict(list)
    for student in qs_student:
        if student.score_total is not None:
            score_dict['전체'].append(student.score_total)
        for r in student.result_list:
            if r.score is not None:
                score_dict[r.psat.round].append(r.score)

    for study_round, scores in score_dict.items():
        participants = len(scores)
        sorted_scores = sorted(scores, reverse=True)

        def get_top_score(percentage):
            if sorted_scores:
                threshold = max(1, int(participants * percentage))
                return sorted_scores[threshold - 1]

        data_statistics.append({
            'study_round': study_round,
            'participants': participants,
            'max': sorted_scores[0] if sorted_scores else None,
            't10': get_top_score(0.10),
            't25': get_top_score(0.25),
            't50': get_top_score(0.50),
            'avg': round(sum(scores) / participants, 1) if sorted_scores else None,
        })
    return data_statistics


def update_study_answer_count_model(model_dict, rank_type='all'):
    answer_model = model_dict['answer']
    answer_count_model = model_dict[rank_type]

    list_update = []
    list_create = []

    answer_distribution = get_study_answer_distribution(answer_model, rank_type)
    organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

    for entry in answer_distribution:
        problem_id = entry['problem_id']
        answer = entry['answer']
        count = entry['count']
        organized_distribution[problem_id][answer] = count

    count_fields = [
        'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
    ]
    for problem_id, answers_original in organized_distribution.items():
        update_data = {'count_multiple': 0}
        for answer, count in answers_original.items():
            if answer <= 5:
                update_data[f'count_{answer}'] = count
            else:
                update_data['count_multiple'] = count
        update_data['count_sum'] = sum(update_data[fld] for fld in count_fields)

        try:
            new_query = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in update_data.items()
            )
            if fields_not_match:
                for fld, val in update_data.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except answer_count_model.DoesNotExist:
            list_create.append(answer_count_model(problem_id=problem_id, **update_data))
    update_fields = [
        'problem_id', 'count_0', 'count_1', 'count_2', 'count_3',
        'count_4', 'count_5', 'count_multiple', 'count_sum',
    ]
    return common_utils.bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def get_study_answer_distribution(answer_model, rank_type):
    lookup_field = f'student__rank_total'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants = F('student__curriculum__category__participants')

    lookup_exp = {}
    if rank_type == 'top':
        lookup_exp[f'{lookup_field}__lte'] = participants * top_rank_threshold
    elif rank_type == 'mid':
        lookup_exp[f'{lookup_field}__gt'] = participants * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants * mid_rank_threshold
    elif rank_type == 'low':
        lookup_exp[f'{lookup_field}__gt'] = participants * mid_rank_threshold

    return (
        answer_model.objects.filter(**lookup_exp).values('problem_id', 'answer')
        .annotate(count=Count('id')).order_by('problem_id', 'answer')
    )


def update_study_answer_counts():
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문항분석표를 업데이트했습니다.',
        False: '기존 문항분석표 데이터와 일치합니다.',
    }

    model_dict = {
        'answer': models.StudyAnswer,
        'all': models.StudyAnswerCount,
        'top': models.StudyAnswerCountTopRank,
        'mid': models.StudyAnswerCountMidRank,
        'low': models.StudyAnswerCountLowRank,
    }

    is_updated_list = [
        update_study_answer_count_model(model_dict, 'all'),
        update_study_answer_count_model(model_dict, 'top'),
        update_study_answer_count_model(model_dict, 'mid'),
        update_study_answer_count_model(model_dict, 'low'),
    ]

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


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
    common_utils.bulk_create_or_update(models.StudyCurriculumSchedule, list_create, list_update, update_fields)


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
    common_utils.bulk_create_or_update(models.StudyCurriculum, list_create, list_update, update_fields)


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
    common_utils.bulk_create_or_update(models.StudyStudent, list_create, list_update, ['name'])


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
        common_utils.bulk_create_or_update(models.StudyResult, list_create, [], [])
    else:
        psats = models.StudyPsat.objects.filter(category=student.curriculum.category)
        list_create = []
        for psat in psats:
            try:
                models.StudyResult.objects.get(student=student, psat=psat)
            except models.StudyResult.DoesNotExist:
                list_create.append(models.StudyResult(student=student, psat=psat))
        common_utils.bulk_create_or_update(models.StudyResult, list_create, [], [])
