__all__ = [
    'CommandPredictExamVars', 'get_empty_model_data',
    'get_student_data_answer_lists', 'get_old_answer_data',
    'get_score_data_score_lists', 'get_rank_data',

    'get_confirmed_scores', 'get_participants',
    'get_default_dict', 'get_department_dict', 'get_qs_department',
    'get_exam_model_data', 'get_statistics', 'get_statistics_data',
    'get_count_lists', 'get_answer_count_model_data',
    'get_total_answer_lists_by_category',
    'get_total_count_dict_by_category',
    'get_total_answer_count_model_data',
    'create_or_update_model', 'update_model_data', 'add_obj_to_model_update_data',
]

import traceback
from collections import Counter

import django
from django.db import transaction
from django.db.models import F

from a_predict.views.base_info import PredictExamVars
from predict import models as old_predict_models


class CommandPredictExamVars(PredictExamVars):
    request = None

    all_departments = [
        '5급 일반행정', '5급 재경', '5급 기술', '5급 기타', '일반외교',
        '7급 행정', '7급 기술', '지역인재 7급 행정', '지역인재 7급 기술', '기타 직렬'
    ]

    unit_dict = {
        1: '5급 행정(전국)',
        2: '5급 행정(지역)',
        3: '5급 기술(전국)',
        4: '5급 기술(지역)',
        5: '외교관후보자',
        6: '지역인재 7급',
        7: '입법고시',
        8: '7급 국가직(일반)',
        9: '7급 국가직(장애인)',
        10: '민간경력',
        11: '프라임 모의고사',
    }
    department_dict = {
        1: '5급 행정(전국)-일반행정',
        2: '5급 행정(전국)-인사조직',
        3: '5급 행정(전국)-법무행정',
        4: '5급 행정(전국)-재경',
        5: '5급 행정(전국)-국제통상',
        6: '5급 행정(전국)-교육행정',
        7: '5급 행정(전국)-사회복지',
        8: '5급 행정(전국)-교정',
        9: '5급 행정(전국)-보호',
        10: '5급 행정(전국)-검찰',
        11: '5급 행정(전국)-출입국관리',
        12: '5급 행정(지역)-서울',
        13: '5급 행정(지역)-부산',
        14: '5급 행정(지역)-대구',
        15: '5급 행정(지역)-인천',
        16: '5급 행정(지역)-광주',
        17: '5급 행정(지역)-대전',
        18: '5급 행정(지역)-울산',
        19: '5급 행정(지역)-세종',
        20: '5급 행정(지역)-경기',
        132: '5급 행정(지역)-강원',
        21: '5급 행정(지역)-충북',
        22: '5급 행정(지역)-충남',
        23: '5급 행정(지역)-전북',
        24: '5급 행정(지역)-전남',
        25: '5급 행정(지역)-경북',
        26: '5급 행정(지역)-경남',
        27: '5급 행정(지역)-제주',
        28: '5급 기술(전국)-일반기계',
        29: '5급 기술(전국)-전기',
        30: '5급 기술(전국)-화공',
        31: '5급 기술(전국)-일반농업',
        32: '5급 기술(전국)-산림자원',
        33: '5급 기술(전국)-일반수산',
        34: '5급 기술(전국)-일반환경',
        35: '5급 기술(전국)-기상',
        36: '5급 기술(전국)-일반토목',
        37: '5급 기술(전국)-건축',
        38: '5급 기술(전국)-시설조경',
        39: '5급 기술(전국)-방재안전',
        40: '5급 기술(전국)-전산개발',
        41: '5급 기술(전국)-데이터',
        42: '5급 기술(전국)-정보보호',
        43: '5급 기술(전국)-통신기술',
        44: '5급 기술(지역)-서울',
        45: '5급 기술(지역)-부산',
        46: '5급 기술(지역)-대구',
        47: '5급 기술(지역)-인천',
        48: '5급 기술(지역)-광주',
        49: '5급 기술(지역)-대전',
        50: '5급 기술(지역)-울산',
        51: '5급 기술(지역)-세종',
        52: '5급 기술(지역)-경기',
        53: '5급 기술(지역)-충북',
        54: '5급 기술(지역)-충남',
        55: '5급 기술(지역)-전북',
        56: '5급 기술(지역)-전남',
        57: '5급 기술(지역)-경북',
        58: '5급 기술(지역)-경남',
        59: '5급 기술(지역)-제주',
        60: '외교관후보자-일반외교',
        61: '지역인재 7급-행정',
        133: '지역인재 7급-기술',
    }


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def get_student_data_answer_lists(exam_vars: CommandPredictExamVars):
    """
    Get student_data for creating or updating student_model from old predict_data.
    Get answer_lists for further process(updating answer_count_model).
    """
    student_data = get_empty_model_data()
    answer_lists: dict[str, list] = {fld: [] for fld in exam_vars.answer_fields}
    old_students = old_predict_models.Student.objects.filter(
        exam__ex=exam_vars.exam_exam, exam__round=exam_vars.exam_round).annotate(created_at=F('timestamp'))

    for student in old_students:
        old_answer_data = get_old_answer_data(exam_vars, student)
        for dt in old_answer_data['data'][:-1]:
            answer_lists[dt[0]].append(dt[-1])

        student_info = {}
        base_info = {
            'user_id': student.user_id, 'year': exam_vars.exam_year,
            'exam': exam_vars.exam_exam, 'round': exam_vars.exam_round,
            'name': student.name, 'serial': student.serial,
        }
        extra_info = {
            'unit': exam_vars.unit_dict[student.unit_id],
            'department': exam_vars.department_dict[student.department_id],
            'password': student.password,
            'prime_id': student.prime_id,
        }
        answer_info = {
            'data': old_answer_data['data'],
            'answer_all_confirmed_at': old_answer_data['answer_all_confirmed_at'],
        }
        student_info.update(base_info)
        student_info.update(extra_info)
        student_info.update(answer_info)

        answer_fields = [key for key in answer_info.keys()]
        update_model_data(
            student_data, exam_vars.student_model, base_info, student_info, answer_fields)

    return student_data, answer_lists


def get_answer_lists(qs_student, answer_fields):
    """
    Get answer_lists for further process(updating answer_count_model).
    """
    answer_lists: dict[str, list] = {fld: [] for fld in answer_fields}
    for student in qs_student:
        for dt in student.data[:-1]:
            answer_lists[dt[0]].append(dt[-1])
    return answer_lists


def get_old_answer_data(exam_vars: CommandPredictExamVars, student):
    """
    Convert old answer_data into new student_model
    """
    answer_fields: list = exam_vars.answer_fields

    old_answers = [
        old_predict_models.Answer.objects.filter(student=student, sub=sub).first() for sub in exam_vars.sub_list
    ]
    data = [[fld, False, 0, [0 for _ in range(cnt)]] for fld, cnt in exam_vars.problem_count.items()]
    data.append([exam_vars.final_field, False, 0, []])

    answer_dict = {fld: [0 for _ in range(cnt)] for fld, cnt in exam_vars.problem_count.items()}
    answer_confirmed_dict = {fld: False for fld in answer_fields}
    answer_updated_at_dict = {fld: None for fld in answer_fields}
    answer_all_confirmed_at = None

    for answer in old_answers:
        if answer:
            fld = exam_vars.subject_vars[answer.sub][1]
            fld_idx = exam_vars.get_field_idx(fld)
            data[fld_idx][1] = answer_confirmed_dict[fld] = answer.is_confirmed
            answer_updated_at_dict[fld] = answer.updated_at

            for i in range(exam_vars.problem_count[fld]):
                ans = getattr(answer, f'prob{i + 1}') or 0
                answer_dict[fld][i] = ans
            data[fld_idx][-1] = answer_dict[fld]

    data[-1][1] = final_confirmed = all([val for val in answer_confirmed_dict.values()])
    if final_confirmed:
        try:
            answer_all_confirmed_at = max([val for val in answer_updated_at_dict.values()])
        except ValueError:
            pass

    return {
        'data': data,
        'answer': answer_dict,
        'answer_all_confirmed_at': answer_all_confirmed_at,
    }


def get_score_data_score_lists(
        exam_vars: CommandPredictExamVars, exam, qs_student, update_fields: list):
    score_data = get_empty_model_data()
    d_ids = exam_vars.department_model.objects.filter(exam=exam_vars.exam_exam).values_list('id', flat=True)
    score_lists: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': {fld: [] for fld in exam_vars.score_fields}},
        'filtered': {'total': {fld: [] for fld in exam_vars.score_fields}}
    }
    score_lists['all'].update({
        d_id: {fld: [] for fld in exam_vars.score_fields} for d_id in d_ids
    })
    score_lists['filtered'].update({
        d_id: {fld: [] for fld in exam_vars.score_fields} for d_id in d_ids
    })

    for student in qs_student:
        d_id = exam_vars.department_model.objects.get(name=student.department).id
        data = []
        score_sum = 0
        for dt in student.data:
            fld = dt[0]
            answer_student = dt[-1]
            correct_count = 0
            score_unit = 4 if fld in ['heonbeob'] else 2.5
            for idx, ans_student in enumerate(answer_student):
                ans_official = exam.answer_official[fld][idx]
                if 1 <= ans_official <= 5:
                    is_correct = ans_student == ans_official
                else:
                    ans_official_list = [int(digit) for digit in str(ans_official)]
                    is_correct = ans_student in ans_official_list
                correct_count += 1 if is_correct else 0

            _score = correct_count * score_unit
            score_sum += _score if fld in exam_vars.only_psat_fields else 0
            dt[2] = _score

            data.append(dt)
            score_lists['all']['total'][fld].append(_score)
            score_lists['all'][d_id][fld].append(_score)
            if dt[1]:
                score_lists['filtered'][d_id][dt[0]].append(_score)
                all_confirmed_at = student.answer_all_confirmed_at
                if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                    score_lists['filtered']['total'][dt[0]].append(_score)

        score_final = round(score_sum / 3, 1)
        data[-1][2] = score_final

        score_lists['all']['total'][exam_vars.final_field].append(score_final)
        score_lists['all'][d_id][exam_vars.final_field].append(score_final)
        if data[-1][1]:
            score_lists['filtered']['total'][exam_vars.final_field].append(score_final)
            score_lists['filtered'][d_id][exam_vars.final_field].append(score_final)

        score_data['update_list'].append(student)
        score_data['update_count'] += 1

        add_obj_to_model_update_data(score_data, student, {'data': data}, update_fields)
    return score_data, score_lists


def get_rank_data(exam_vars: CommandPredictExamVars, exam, qs_student, score_lists):
    rank_data = get_empty_model_data()

    sorted_scores = {}
    for ctgry, val in score_lists.items():
        sorted_scores[ctgry] = {}
        for dep, score_lst in val.items():
            sorted_scores[ctgry][dep] = {}
            for fld, scores in score_lst.items():
                sorted_scores[ctgry][dep][fld] = sorted(scores, reverse=True)

    for student in qs_student:
        d_id = exam_vars.department_model.objects.get(name=student.department).id
        rank = {
            'all': {
                'total': {field: 0 for field in exam_vars.score_fields},
                'department': {field: 0 for field in exam_vars.score_fields},
            },
            'filtered': {
                'total': {field: 0 for field in exam_vars.score_fields},
                'department': {field: 0 for field in exam_vars.score_fields},
            },
        }
        for dt in student.data:
            fld = dt[0]
            is_confirmed = dt[1]
            score = dt[2]
            if is_confirmed:
                rank['all']['total'][fld] = (sorted_scores['all']['total'][fld].index(score) + 1)
                rank['all']['department'][fld] = (sorted_scores['all'][d_id][fld].index(score) + 1)
                all_confirmed_at = student.answer_all_confirmed_at
                if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                    rank['filtered']['total'][fld] = (
                            sorted_scores['filtered']['total'][fld].index(score) + 1)
                    rank['filtered']['department'][fld] = (
                            sorted_scores['filtered'][d_id][fld].index(score) + 1)

        if student.rank != rank:
            student.rank = rank
            rank_data['update_list'].append(student)
            rank_data['update_count'] += 1

    return rank_data


def get_confirmed_scores(
        exam_vars: CommandPredictExamVars, exam, qs_student, department: str | None = None
) -> dict:
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    if department:
        qs_student = qs_student.filter(department=department)

    scores = {
        'all': {field: [] for field in score_fields},
        'filtered': {field: [] for field in score_fields},
    }
    for idx, fld in enumerate(score_fields):
        for student in qs_student:
            if student.data[idx][1]:
                scores['all'][fld].append(student.data[idx][2])

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                scores['filtered'][fld].append(student.data[idx][2])

    sorted_scores = {
        'all': {fld: sorted(scores['all'][fld], reverse=True) for fld in score_fields},
        'filtered': {fld: sorted(scores['filtered'][fld], reverse=True) for fld in score_fields},
    }
    return sorted_scores


def get_participants(exam_vars: CommandPredictExamVars, exam, qs_student):
    participants = get_default_dict(exam_vars, 0)
    department_dict = get_department_dict(exam_vars)

    for student in qs_student:
        d_id = department_dict[student.department]
        for field, is_confirmed in student.answer_confirmed.items():
            if is_confirmed:
                participants['all']['total'][field] += 1
                participants['all'][d_id][field] += 1

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                participants['filtered']['total'][field] += 1
                participants['filtered'][d_id][field] += 1
    return participants


def get_default_dict(exam_vars: CommandPredictExamVars, default):
    score_fields = exam_vars.score_fields
    department_dict = get_department_dict(exam_vars)
    default_dict = {
        'all': {'total': {fld: default for fld in score_fields}},
        'filtered': {'total': {fld: default for fld in score_fields}},
    }
    default_dict['all'].update({
        d_id: {fld: default for fld in score_fields} for d_id in department_dict.values()
    })
    default_dict['filtered'].update({
        d_id: {fld: default for fld in score_fields} for d_id in department_dict.values()
    })
    return default_dict


def get_department_dict(exam_vars: CommandPredictExamVars):
    qs_department = get_qs_department(exam_vars)
    return {department.name: department.id for department in qs_department}


def get_qs_department(exam_vars: CommandPredictExamVars, unit=None):
    if unit:
        return exam_vars.department_model.objects.filter(
            exam=exam_vars.exam_exam, unit=unit).order_by('id')
    return exam_vars.department_model.objects.filter(exam=exam_vars.exam_exam).order_by('order')


def get_exam_model_data(exam, participants):
    exam_model_data = get_empty_model_data()
    if exam.participants != participants:
        exam.participants = participants
        exam_model_data['update_list'].append(exam)
        exam_model_data['update_count'] += 1
    return exam_model_data


def get_statistics(exam_vars: CommandPredictExamVars, exam, qs_department, qs_student):
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    scores_total = get_confirmed_scores(exam_vars, exam, qs_student)
    scores: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': scores_total['all']},
        'filtered': {'total': scores_total['filtered']},
    }
    statistics: dict[str, dict[str | int, dict]] = {
        'all': {
            'total': {field: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for field in score_fields},
        },
        'filtered': {
            'total': {field: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for field in score_fields},
        },
    }
    for department in qs_department:
        scores_department = get_confirmed_scores(exam_vars, exam, qs_student, department.name)
        scores['all'][department.id] = scores_department['all']
        scores['filtered'][department.id] = scores_department['filtered']
        statistics['all'][department.id] = {field: {} for field in score_fields}
        statistics['filtered'][department.id] = {field: {} for field in score_fields}

    for key, value in scores.items():
        for department, scores_dict in value.items():
            for field, score_list in scores_dict.items():
                participants = len(score_list)
                top_10 = max(1, int(participants * 0.1))
                top_20 = max(1, int(participants * 0.2))

                if score_list:
                    statistics[key][department][field]['max'] = round(score_list[0], 1)
                    statistics[key][department][field]['t10'] = round(score_list[top_10 - 1], 1)
                    statistics[key][department][field]['t20'] = round(score_list[top_20 - 1], 1)
                    statistics[key][department][field]['avg'] = round(
                        sum(score_list) / participants if participants else 0, 1)
    return statistics


def get_statistics_data(exam, statistics):
    statistics_data = get_empty_model_data()
    if exam.statistics != statistics:
        exam.statistics = statistics
        statistics_data['update_list'].append(exam)
        statistics_data['update_count'] += 1
    return statistics_data


def get_count_lists(
        exam_vars: CommandPredictExamVars, exam, total_answer_lists: dict) -> dict[str, list]:
    count_lists: dict[str, list] = {}
    for fld in exam_vars.answer_fields:
        ans_official = exam.answer_official[fld] if fld in exam.answer_official else None
        count_lists[fld] = []
        problem_count = exam_vars.get_problem_count(fld)
        for i in range(1, problem_count + 1):
            answer = ans_official[i - 1] if ans_official else 0
            problem_info = exam_vars.get_problem_info(fld, i)
            count_fields_info = {fld: 0 for fld in exam_vars.all_count_fields}
            append_dict = dict(problem_info, **count_fields_info, **{'answer': answer})
            count_lists[fld].append(append_dict)

    for fld, answer_lists in total_answer_lists.items():
        if answer_lists:
            problem_count = exam_vars.get_problem_count(fld)
            distributions = [Counter() for _ in range(problem_count)]
            for lst in answer_lists:
                for i, value in enumerate(lst):
                    if value > 5:
                        distributions[i]['count_multiple'] += 1
                    else:
                        distributions[i][value] += 1

            for idx, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                count_lists[fld][idx].update(count_dict)
    return count_lists


def get_answer_count_model_data(exam_vars: CommandPredictExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for fld in exam_vars.answer_fields:
        for row in all_count_dict[fld]:
            if row['count_total']:
                problem_info = exam_vars.get_problem_info(row['subject'], row['number'])
                update_model_data(
                    answer_count_model_data, exam_vars.answer_count_model,
                    problem_info, row, matching_fields)
    return answer_count_model_data


def get_total_answer_lists_by_category(exam_vars: CommandPredictExamVars, exam, qs_student):
    answer_fields = exam_vars.answer_fields
    rank_list = exam_vars.rank_list
    participants = exam.participants
    total_answer_lists_by_category: dict[str, dict[str, dict[str, list]]] = {
        'all': {rnk: {fld: [] for fld in answer_fields} for rnk in rank_list},
        'filtered': {rnk: {fld: [] for fld in answer_fields} for rnk in rank_list},
    }

    participants_all = participants['all']['total']['psat_avg']
    participants_filtered = participants['filtered']['total']['psat_avg']

    for student in qs_student:
        rank_all_student = student.rank['all']['total']['psat_avg']
        rank_filtered_student = student.rank['filtered']['total']['psat_avg']
        rank_ratio_all = rank_ratio_filtered = None
        if participants_all:
            rank_ratio_all = rank_all_student / participants_all
        if participants_filtered:
            rank_ratio_filtered = rank_filtered_student / participants_filtered

        for field in answer_fields:
            if student.answer_confirmed[field]:
                ans_student = student.answer[field]
                top_rank_threshold = 0.27
                mid_rank_threshold = 0.73

                def append_answer(catgry: str, rank: str):
                    total_answer_lists_by_category[catgry][rank][field].append(ans_student)

                append_answer('all', 'all_rank')
                if rank_ratio_all and 0 <= rank_ratio_all <= top_rank_threshold:
                    append_answer('all', 'top_rank')
                elif rank_ratio_all and top_rank_threshold < rank_ratio_all <= mid_rank_threshold:
                    append_answer('all', 'mid_rank')
                elif rank_ratio_all and mid_rank_threshold < rank_ratio_all <= 1:
                    append_answer('all', 'low_rank')

                if student.answer_all_confirmed_at and student.answer_all_confirmed_at < exam.answer_official_opened_at:
                    append_answer('filtered', 'all_rank')
                    if rank_ratio_filtered and 0 <= rank_ratio_filtered <= top_rank_threshold:
                        append_answer('filtered', 'top_rank')
                    elif rank_ratio_filtered and top_rank_threshold < rank_ratio_filtered <= mid_rank_threshold:
                        append_answer('filtered', 'mid_rank')
                    elif rank_ratio_filtered and mid_rank_threshold < rank_ratio_filtered <= 1:
                        append_answer('filtered', 'low_rank')
    return total_answer_lists_by_category


def get_total_count_dict_by_category(exam_vars: CommandPredictExamVars, total_answer_lists: dict):
    problem_count = exam_vars.problem_count
    rank_list = exam_vars.rank_list

    total_count_dict = {}
    for field, count in problem_count.items():
        total_count_dict[field] = []
        for number in range(1, count + 1):
            problem_info = exam_vars.get_problem_info(field, number)
            problem_info.update({
                'all': {rank: [] for rank in rank_list},
                'filtered': {rank: [] for rank in rank_list},
            })
            total_count_dict[field].append(problem_info)

    for category, value1 in total_answer_lists.items():
        for rank, value2 in value1.items():
            for field, answer_lists in value2.items():
                p_count = problem_count[field]
                if answer_lists:
                    distributions = [Counter() for _ in range(p_count)]
                    for lst in answer_lists:
                        for i, value in enumerate(lst):
                            if value > 5:
                                distributions[i]['count_multiple'] += 1
                            else:
                                distributions[i][value] += 1

                    for idx, counter in enumerate(distributions):
                        count_list = [counter.get(i, 0) for i in range(6)]
                        count_total = sum(count_list[1:])
                        count_list.extend([counter.get('count_multiple', 0), count_total])
                        total_count_dict[field][idx][category][rank] = count_list

    return total_count_dict


def get_total_answer_count_model_data(
        exam_vars: CommandPredictExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for field in exam_vars.answer_fields:
        for data in all_count_dict[field]:
            problem_info = exam_vars.get_problem_info(data['subject'], data['number'])
            update_model_data(
                answer_count_model_data, exam_vars.answer_count_model,
                problem_info, data, matching_fields)
    return answer_count_model_data


def create_or_update_model(model, update_fields: list, model_data: dict):
    model_name = model._meta.model_name
    update_list = model_data['update_list']
    create_list = model_data['create_list']
    update_count = model_data['update_count']
    create_count = model_data['create_count']

    try:
        with transaction.atomic():
            if update_list:
                model.objects.bulk_update(update_list, update_fields)
                message = f'Successfully updated {update_count} {model_name} instances.'
            elif create_list:
                model.objects.bulk_create(create_list)
                message = f'Successfully created {create_count} {model_name} instances.'
            elif not update_list and not create_list:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = 'An error occurred during the transaction.'
    print(message)


def update_model_data(
        model_data: dict, model, lookup: dict,
        matching_data: dict, matching_fields: list,
        obj=None,
):
    if obj:
        add_obj_to_model_update_data(model_data, obj, matching_data, matching_fields)
    else:
        try:
            obj = model.objects.get(**lookup)
            add_obj_to_model_update_data(model_data, obj, matching_data, matching_fields)
        except model.DoesNotExist:
            model_data['create_list'].append(model(**matching_data))
            model_data['create_count'] += 1
        except model.MultipleObjectsReturned:
            print(f'Instance is duplicated.')


def add_obj_to_model_update_data(
        model_data: dict, obj,
        matching_data: dict, matching_fields: list,
):
    fields_not_match = any(
        getattr(obj, fld) != matching_data[fld] for fld in matching_fields)
    if fields_not_match:
        for fld in matching_fields:
            setattr(obj, fld, matching_data[fld])
        model_data['update_list'].append(obj)
        model_data['update_count'] += 1
