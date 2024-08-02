__all__ = [
    'CommandPredictExamVars', 'get_empty_model_data',
    'get_answer_lists',
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

from a_predict.views.base_info import PredictExamVars


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


def get_answer_lists(qs_student, answer_fields):
    """
    Get answer_lists for further process(updating answer_count_model).
    """
    answer_lists: dict[str, list] = {fld: [] for fld in answer_fields}
    for student in qs_student:
        for dt in student.data[:-1]:
            answer_lists[dt[0]].append(dt[-1])
    return answer_lists


def get_score_data_score_lists(exam_vars: PredictExamVars, exam, qs_student):
    score_data = get_empty_model_data()
    d_ids = exam_vars.department_model.objects.filter(exam=exam_vars.exam_exam).values_list('id', flat=True)
    score_lists: dict[str, dict[str, dict[str, list]]] = {
        'all': {'total': {fld: [] for fld in exam_vars.admin_score_fields}},
        'filtered': {'total': {fld: [] for fld in exam_vars.admin_score_fields}}
    }
    score_lists['all'].update({
        d_id: {fld: [] for fld in exam_vars.admin_score_fields} for d_id in d_ids
    })
    score_lists['filtered'].update({
        d_id: {fld: [] for fld in exam_vars.admin_score_fields} for d_id in d_ids
    })

    for student in qs_student:
        all_confirmed_at = student.answer_all_confirmed_at
        d_id = exam_vars.department_model.objects.get(name=student.department).id
        score_sum = 0
        needs_update = False
        for dt in student.data:
            fld = dt[0]
            is_confirmed = dt[1]
            answer_student = dt[-1]
            if is_confirmed:
                if fld != exam_vars.final_field:
                    correct_count = 0
                    score_unit = exam_vars.get_score_unit(fld)
                    for idx, ans_student in enumerate(answer_student):
                        try:
                            ans_official = exam.answer_official[fld][idx]
                        except KeyError as e:
                            print(e)
                            break

                        if 1 <= ans_official <= 5:
                            is_correct = ans_student == ans_official
                        else:
                            ans_official_list = [int(digit) for digit in str(ans_official)]
                            is_correct = ans_student in ans_official_list
                        correct_count += 1 if is_correct else 0

                    _score = correct_count * score_unit
                    score_lists['all']['total'][fld].append(_score)
                    score_lists['all'][d_id][fld].append(_score)

                    if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                        score_lists['filtered']['total'][fld].append(_score)
                        score_lists['filtered'][d_id][fld].append(_score)

                    if exam_vars.exam_exam != '행시' or fld != 'heonbeob':
                        score_sum += _score

                    if dt[2] != _score:
                        dt[2] = _score
                        needs_update = True
                else:
                    _score = round(score_sum / 3, 1) if exam_vars.exam_type == 'psat' else score_sum
                    score_lists['all']['total'][fld].append(_score)
                    score_lists['all'][d_id][fld].append(_score)

                    if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                        score_lists['filtered']['total'][fld].append(_score)
                        score_lists['filtered'][d_id][fld].append(_score)

                    if dt[2] != _score:
                        dt[2] = _score
                        needs_update = True
        if needs_update:
            score_data['update_list'].append(student)
            score_data['update_count'] += 1
    return score_data, score_lists


def get_rank_data(exam_vars: PredictExamVars, exam, qs_student, score_lists):
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
                'total': {fld: 0 for fld in exam_vars.score_fields},
                'department': {fld: 0 for fld in exam_vars.score_fields},
            },
            'filtered': {
                'total': {fld: 0 for fld in exam_vars.score_fields},
                'department': {fld: 0 for fld in exam_vars.score_fields},
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

    return rank_data, sorted_scores


def get_confirmed_scores(
        exam_vars: PredictExamVars, exam, qs_student, department: str | None = None
) -> dict:
    score_fields = exam_vars.score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    if department:
        qs_student = qs_student.filter(department=department)

    scores = {
        'all': {fld: [] for fld in score_fields},
        'filtered': {fld: [] for fld in score_fields},
    }
    for student in qs_student:
        all_confirmed_at = student.answer_all_confirmed_at
        for dt in student.data:
            fld = dt[0]
            is_confirmed = dt[1]
            score = dt[2]
            if is_confirmed:
                scores['all'][fld].append(score)
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                scores['filtered'][fld].append(score)

    sorted_scores = {
        'all': {fld: sorted(scores['all'][fld], reverse=True) for fld in score_fields},
        'filtered': {fld: sorted(scores['filtered'][fld], reverse=True) for fld in score_fields},
    }
    return sorted_scores


def get_participants(exam_vars: PredictExamVars, exam, qs_student):
    participants = get_default_dict(exam_vars, 0)
    department_dict = get_department_dict(exam_vars)

    for student in qs_student:
        d_id = department_dict[student.department]
        for dt in student.data:
            fld = dt[0]
            is_confirmed = dt[1]
            if is_confirmed:
                participants['all']['total'][fld] += 1
                participants['all'][d_id][fld] += 1

            all_confirmed_at = student.answer_all_confirmed_at
            if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                participants['filtered']['total'][fld] += 1
                participants['filtered'][d_id][fld] += 1
    return participants


def get_default_dict(exam_vars: PredictExamVars, default):
    department_dict = get_department_dict(exam_vars)
    default_dict = {
        'all': {'total': {fld: default for fld in exam_vars.admin_score_fields}},
        'filtered': {'total': {fld: default for fld in exam_vars.admin_score_fields}},
    }
    default_dict['all'].update({
        d_id: {fld: default for fld in exam_vars.admin_score_fields}
        for d_id in department_dict.values()
    })
    default_dict['filtered'].update({
        d_id: {fld: default for fld in exam_vars.admin_score_fields}
        for d_id in department_dict.values()
    })
    return default_dict


def get_department_dict(exam_vars: PredictExamVars):
    qs_department = get_qs_department(exam_vars)
    return {department.name: department.id for department in qs_department}


def get_qs_department(exam_vars: PredictExamVars, unit=None):
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


def get_statistics(exam_vars: PredictExamVars, score_lists, qs_department):
    admin_score_fields = exam_vars.admin_score_fields  # ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    statistics: dict[str, dict[str | int, dict]] = {
        'all': {
            'total': {fld: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for fld in admin_score_fields},
        },
        'filtered': {
            'total': {fld: {'max': 0, 't10': 0, 't20': 0, 'avg': 0} for fld in admin_score_fields},
        },
    }
    for dep in qs_department:
        statistics['all'][dep.id] = {fld: {} for fld in admin_score_fields}
        statistics['filtered'][dep.id] = {fld: {} for fld in admin_score_fields}

    for key, val in score_lists.items():
        for dep, scores_dict in val.items():
            for fld, score_list in scores_dict.items():
                participants = len(score_list)
                top_10 = max(1, int(participants * 0.1))
                top_20 = max(1, int(participants * 0.2))

                if score_list:
                    statistics[key][dep][fld]['max'] = round(score_list[0], 1)
                    statistics[key][dep][fld]['t10'] = round(score_list[top_10 - 1], 1)
                    statistics[key][dep][fld]['t20'] = round(score_list[top_20 - 1], 1)
                    statistics[key][dep][fld]['avg'] = round(
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
        exam_vars: PredictExamVars, exam, total_answer_lists: dict) -> dict[str, list]:
    count_lists: dict[str, list[dict]] = {fld: [] for fld in exam_vars.all_subject_fields}
    for fld in exam_vars.all_subject_fields:
        ans_official = exam.answer_official[fld] if fld in exam.answer_official else None
        count_lists[fld] = []
        problem_count = exam_vars.problem_count[fld]
        for no in range(1, problem_count + 1):
            answer = ans_official[no - 1] if ans_official else 0
            problem_info = exam_vars.get_problem_info(fld, no)
            count_fields_info = {fld: 0 for fld in exam_vars.all_count_fields}
            append_dict = dict(problem_info, **count_fields_info, **{'answer': answer})
            count_lists[fld].append(append_dict)

    for fld, answer_lists in total_answer_lists.items():
        if answer_lists:
            problem_count = exam_vars.problem_count[fld]
            distributions = [Counter() for _ in range(problem_count)]
            for answer_list in answer_lists:
                for no, val in enumerate(answer_list):
                    if val > 5:
                        distributions[no]['count_multiple'] += 1
                    else:
                        distributions[no][val] += 1

            for idx, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                count_lists[fld][idx].update(count_dict)
    return count_lists


def get_answer_count_model_data(exam_vars: PredictExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for fld in exam_vars.all_subject_fields:
        for row in all_count_dict[fld]:
            if row['count_total']:
                problem_info = exam_vars.get_problem_info(row['subject'], row['number'])
                update_model_data(
                    answer_count_model_data, exam_vars.answer_count_model,
                    problem_info, row, matching_fields)
    return answer_count_model_data


def get_total_answer_lists_by_category(exam_vars: PredictExamVars, exam, qs_student):
    total_answer_lists_by_category: dict[str, dict[str, dict[str, list]]] = {
        'all': {rnk: {fld: [] for fld in exam_vars.all_subject_fields}
                for rnk in exam_vars.rank_list},
        'filtered': {rnk: {fld: [] for fld in exam_vars.all_subject_fields}
                     for rnk in exam_vars.rank_list},
    }

    participants_all = exam.participants['all']['total'][exam_vars.final_field]
    participants_filtered = exam.participants['filtered']['total'][exam_vars.final_field]

    for student in qs_student:
        rank_all_student = student.rank['all']['total'][exam_vars.final_field]
        rank_filtered_student = student.rank['filtered']['total'][exam_vars.final_field]
        rank_ratio_all = rank_ratio_filtered = None
        if participants_all:
            rank_ratio_all = rank_all_student / participants_all
        if participants_filtered:
            rank_ratio_filtered = rank_filtered_student / participants_filtered

        for dt in student.data:
            fld = dt[0]
            ans_student = dt[-1]
            if ans_student:
                top_rank_threshold = 0.27
                mid_rank_threshold = 0.73

                def append_answer(ctgry: str, rank: str):
                    total_answer_lists_by_category[ctgry][rank][fld].append(ans_student)

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


def get_total_count_dict_by_category(exam_vars: PredictExamVars, total_answer_lists: dict):
    total_count_dict = {
        fld: [{} for _ in range(cnt)] for fld, cnt in exam_vars.problem_count.items()
    }
    for fld, cnt in exam_vars.problem_count.items():
        for no in range(1, cnt + 1):
            problem_info = exam_vars.get_problem_info(fld, no)
            problem_info.update({
                'all': {rnk: [] for rnk in exam_vars.rank_list},
                'filtered': {rnk: [] for rnk in exam_vars.rank_list},
            })
            total_count_dict[fld][no - 1] = problem_info

    for ctgry, value1 in total_answer_lists.items():
        for rnk, value2 in value1.items():
            for fld, answer_lists in value2.items():
                p_count = exam_vars.problem_count[fld]
                if answer_lists and fld != exam_vars.final_field:
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
                        total_count_dict[fld][idx][ctgry][rnk] = count_list

    return total_count_dict


def get_total_answer_count_model_data(
        exam_vars: PredictExamVars, matching_fields: list, all_count_dict: dict):
    answer_count_model_data = get_empty_model_data()
    for fld in exam_vars.all_subject_fields:
        for data in all_count_dict[fld]:
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
