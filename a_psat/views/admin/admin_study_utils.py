import traceback
from collections import defaultdict

import django.db.utils
from django.db import transaction
from django.db.models import Count, F
from django.urls import reverse_lazy

from ... import models


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


def update_data_answers(qs_problem):
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


def get_score_stat_dict(qs_student) -> dict:
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


def update_scores(qs_student, psats):
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
        is_updated_list.append(bulk_create_or_update(
            models.StudyResult, [], list_update, ['score']))

    # Update StudyStudent for score_total
    list_update = []
    student_scores = models.get_study_student_score_calculated_annotation(qs_student)
    for student in student_scores:
        if student.score_total != student.score_calculated:
            student.score_total = student.score_calculated
            list_update.append(student)
    is_updated_list.append(bulk_create_or_update(
        models.StudyStudent, [], list_update, ['score_total']))

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_ranks(qs_student, psats):
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
        bulk_create_or_update(models.StudyResult, [], list_update, ['rank']))

    # Update StudyStudent for score_total
    list_update = []
    ranked_students = models.get_study_student_total_rank_calculated_annotation(qs_student)
    for student in ranked_students:
        if student.rank_total != student.rank_calculated:
            student.rank_total = student.rank_calculated
            list_update.append(student)
    is_updated_list.append(
        bulk_create_or_update(models.StudyStudent, [], list_update, ['rank_total']))

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def get_data_statistics(qs_student):
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


def update_statistics_model(category, data_statistics):
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
    is_updated = bulk_create_or_update(model, list_create, list_update, ['statistics'])
    return is_updated, message_dict[is_updated]


def get_answer_distribution(answer_model, rank_type):
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


def update_answer_count_model(model_dict, rank_type='all'):
    answer_model = model_dict['answer']
    answer_count_model = model_dict[rank_type]

    list_update = []
    list_create = []

    answer_distribution = get_answer_distribution(answer_model, rank_type)
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
    return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def update_answer_counts():
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
        update_answer_count_model(model_dict, 'all'),
        update_answer_count_model(model_dict, 'top'),
        update_answer_count_model(model_dict, 'mid'),
        update_answer_count_model(model_dict, 'low'),
    ]

    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


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
