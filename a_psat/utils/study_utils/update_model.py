from collections import defaultdict

from django.db.models import F

from a_psat import models
from a_psat.utils.decorators import *
from a_psat.utils.modify_models_methods import *
from a_psat.utils.study_utils import get_normal_answer_data

UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@for_admin_views
@with_update_message(UPDATE_MESSAGES['score'])
def admin_update_scores(qs_student, psats):
    update_list = admin_get_update_list_of_result_model(qs_student, psats)
    update_list.append(admin_get_update_list_of_student_model_for_score_total(qs_student))
    return update_list


@for_admin_views
@with_update_message(UPDATE_MESSAGES['rank'])
def admin_update_ranks(qs_student, psats):
    return [
        admin_get_update_rank_list_of_result_model(qs_student, psats),
        admin_get_update_rank_total_list_of_student_model(qs_student)
    ]


@for_admin_views
@with_update_message(UPDATE_MESSAGES['statistics'])
def admin_update_statistics(category, data_statistics):
    return [admin_get_update_list_of_statistics_model(category, data_statistics)]


@for_admin_views
@with_update_message(UPDATE_MESSAGES['answer_count'])
def admin_update_answer_counts():
    model_dict = {
        'all': models.StudyAnswerCount, 'top': models.StudyAnswerCountTopRank,
        'mid': models.StudyAnswerCountMidRank, 'low': models.StudyAnswerCountLowRank,
    }
    return [
        admin_get_update_list_of_answer_count_model(model_dict, 'all'),
        admin_get_update_list_of_answer_count_model(model_dict, 'top'),
        admin_get_update_list_of_answer_count_model(model_dict, 'mid'),
        admin_get_update_list_of_answer_count_model(model_dict, 'low'),
    ]


@for_admin_views
def admin_get_update_list_of_result_model(qs_student, psats):
    update_list = []
    for student in qs_student:
        update_list.append(admin_get_update_list_of_result_model_for_each_student(student, psats))
    return update_list


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_list_of_result_model_for_each_student(student, psats):
    qs_result = models.StudyResult.objects.filter(student=student, psat__in=psats)
    list_create, list_update = [], []
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
    return models.StudyResult, list_create, list_update, ['score']


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_list_of_student_model_for_score_total(qs_student):
    list_create, list_update = [], []
    student_scores = models.get_study_student_score_calculated_annotation(qs_student)
    for student in student_scores:
        if student.score_total != student.score_calculated:
            student.score_total = student.score_calculated
            list_update.append(student)
    return models.StudyStudent, list_create, list_update, ['score_total']


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_rank_list_of_result_model(qs_student, psats):
    list_create, list_update = [], []
    ranked_results = models.StudyResult.objects.get_rank_calculated(qs_student, psats)
    for result in ranked_results:
        if result.rank_calculated != models.StudyResult.objects.get(id=result.id).rank:
            result.rank = result.rank_calculated
            list_update.append(result)
    return models.StudyResult, list_create, list_update, ['rank']


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_rank_total_list_of_student_model(qs_student):
    list_create, list_update = [], []
    ranked_students = models.get_study_student_total_rank_calculated_annotation(qs_student)
    for student in ranked_students:
        if student.rank_total != student.rank_calculated:
            student.rank_total = student.rank_calculated
            list_update.append(student)
    return models.StudyStudent, list_create, list_update, ['rank_total']


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_list_of_statistics_model(category, data_statistics):
    model = models.StudyPsat
    list_create, list_update = [], []

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
    return model, list_create, list_update, ['statistics']


@for_admin_views
@with_bulk_create_or_update()
def admin_get_update_list_of_answer_count_model(model_dict, rank_type='all'):
    answer_count_model = model_dict[rank_type]
    list_create, list_update = [], []

    answer_distribution = models.StudyAnswer.objects.get_study_answer_distribution(rank_type)
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
    return answer_count_model, list_create, list_update, update_fields


@for_normal_views
def update_normal_result_and_student_model_instance(answer_data, result):
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.StudyProblem.objects.get(psat=result.psat, number=no)
        list_create.append(models.StudyAnswer(student=result.student, problem=problem, answer=ans))
    bulk_create_or_update(models.StudyAnswer, list_create, [], [])

    qs_answer_count = models.StudyAnswerCount.objects.get_filtered_qs_by_psat(result.psat)
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
        qs_ac.save()

    qs_answer = models.StudyAnswer.objects.filter(student=result.student, problem__psat=result.psat)
    score = 0
    for qs_a in qs_answer:
        answer_correct_list = {int(digit) for digit in str(qs_a.answer_correct)}
        if qs_a.answer in answer_correct_list:
            score += 1
    result.score = score
    result.save()

    student = result.student
    student.score_total = score if student.score_total is None else F('score_total') + score
    student.save()
