import json
from collections import defaultdict

from a_psat import models, utils
from a_psat.views.admin_views import admin_view_utils


def get_study_schedule_info():
    schedule_info = defaultdict()
    qs_curriculum_schedule_info = models.StudyCurriculumSchedule.objects.get_curriculum_schedule_info()
    for qs_cs in qs_curriculum_schedule_info:
        schedule_info[qs_cs['curriculum']] = qs_cs
    return schedule_info


def update_study_qs_student(qs_student, schedule_info):
    for qs_s in qs_student:
        qs_s.study_rounds = schedule_info[qs_s.curriculum_id]['study_rounds']
        qs_s.earliest_datetime = schedule_info[qs_s.curriculum_id]['earliest']
        qs_s.latest_datetime = schedule_info[qs_s.curriculum_id]['latest']


def get_study_homework_schedule(qs_schedule):
    homework_schedule = defaultdict(dict)
    for qs_s in qs_schedule:
        if qs_s.lecture_round:
            homework_schedule[qs_s.lecture_round]['lecture_datetime'] = qs_s.lecture_datetime
            homework_schedule[qs_s.lecture_round]['lecture_open_datetime'] = qs_s.lecture_open_datetime
        if qs_s.homework_round:
            homework_schedule[qs_s.homework_round]['homework_end_datetime'] = qs_s.homework_end_datetime
    return homework_schedule


def get_study_curriculum_statistics(qs_student):
    total_stat = admin_view_utils.get_study_score_stat_dict(qs_student)
    data_statistics = admin_view_utils.get_study_data_statistics(qs_student)
    per_round_stat = {}
    for data in data_statistics:
        per_round_stat[data['study_round']] = data
    return {
        'total': total_stat,
        'per_round': per_round_stat,
    }


def get_study_statistics_paginator_data(homework_schedule, qs_result, curriculum_statistics, page_number) -> tuple:
    per_round_stat = curriculum_statistics['per_round']
    statistics_page_obj, statistics_page_range = utils.get_paginator_data(qs_result, page_number, 4)
    for obj in statistics_page_obj:
        data_stat = per_round_stat.get(obj.psat.round)
        if data_stat:
            for key, val in data_stat.items():
                setattr(obj, key, val)

        obj.statistics = data_stat
        obj.schedule = homework_schedule.get(obj.psat.round)
    return statistics_page_obj, statistics_page_range


def get_study_my_result_paginator_data(homework_schedule, student, opened_rounds, qs_result, curriculum_statistics, page_number) -> tuple:
    total_stat = curriculum_statistics['total']
    per_round_stat = curriculum_statistics['per_round']
    my_result_page_obj, my_result_page_range = utils.get_paginator_data(qs_result, page_number, 4)
    score_dict = get_score_dict(student)

    #  커리큘럼 기준 각 회차별 등수 계산 (점수가 None인 경우는 제외)
    qs_score = models.StudyResult.objects.get_filtered_qs_ordered_by_psat_round(
        student.curriculum, psat__round__in=opened_rounds)
    score_dict_for_rank = defaultdict(list)
    for qs_s in qs_score:
        score = qs_s['score']
        if score is not None:
            score_dict_for_rank[qs_s['round']].append(score)
    for rnd, score_list in score_dict_for_rank.items():
        score_dict_for_rank[rnd] = sorted(score_list, reverse=True)

    #  커리큘럼 기준 전체 등수 계산
    qs_rank = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_rank(student.curriculum)
    for qs_r in qs_rank:
        if qs_r.id == student.id:
            student.rank = qs_r.rank

    # 커리큘럼 기준 전체 통계
    problem_count = models.StudyProblem.objects.filter(
        psat__category=student.curriculum.category, psat__round__in=opened_rounds).count()
    my_total_result = {
        'total_score_sum': problem_count,
        'score_sum': score_dict['total']['score_sum'],
        'participants': total_stat['participants'],
        'rank': student.rank if score_dict['total']['score_sum'] else None,
    }
    for i in range(4):
        my_total_result[f'score_{i}'] = score_dict['total'][f'score_{i}']

    # 각 회차별 인스턴스에 통계 및 스케줄 자료 추가
    for obj in my_result_page_obj:
        for key, val in score_dict[obj.psat.round].items():
            setattr(obj, key, val)

        obj.rank = score_dict_for_rank[obj.psat.round].index(obj.score) + 1 if obj.score else None
        stat = per_round_stat.get(obj.psat.round)
        obj.participants = stat['participants'] if stat else None
        obj.schedule = homework_schedule.get(obj.psat.round)
    return my_total_result, my_result_page_obj, my_result_page_range


def get_score_dict(student):
    # 점수 계산용 비어 있는 딕셔너리 만들기 (score_1: 언어, score_2: 자료, score_3: 상황)
    score_dict = defaultdict(dict)
    for study_round in range(student.curriculum.category.round + 1):
        key = study_round if study_round else 'total'
        score_dict[key]['score_sum'] = 0  # 총점 합계
        for i in range(4):
            score_dict[key][f'score_{i}'] = 0  # 과목별 총점

    # 과목별 점수 업데이트 (쿼리셋 주석으로 처리한 과목 필드(subject_1 등)를 성적 필드(score_1 등)로 변환)
    qs_answer = models.StudyAnswer.objects.get_filtered_qs_by_student(student)
    for qs_a in qs_answer:
        if qs_a['is_correct']:
            score_field = str(qs_a['subject']).replace('subject', 'score')
            score_dict[qs_a['round']]['score_sum'] += 1
            score_dict[qs_a['round']][score_field] += 1
            score_dict['total']['score_sum'] += 1
            score_dict['total'][score_field] += 1
    return score_dict


def get_study_answer_paginator_data(schedule_dict, student, opened_rounds, page_number) -> tuple:
    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(
        student.curriculum.category).filter(psat__round__in=opened_rounds).order_by('-psat')
    answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number, on_each_side=1)

    homework_rounds = []
    for obj in answer_page_obj:
        homework_rounds.append(obj.psat.round)

    qs_answer = models.StudyAnswer.objects.with_select_related().filter(
        student=student, problem__psat__round__in=homework_rounds)
    answer_student_dict = defaultdict(dict)
    for qs_a in qs_answer:
        answer_student_dict[(qs_a.problem.psat.round, qs_a.problem.number)] = qs_a.answer

    for obj in answer_page_obj:
        obj: models.StudyProblem

        ans_student = answer_student_dict[(obj.psat.round, obj.number)]
        ans_official = obj.answer
        answer_official_list = [int(digit) for digit in str(ans_official)]

        obj.schedule = schedule_dict.get(obj.psat.round)
        obj.no = obj.number
        obj.ans_student = ans_student
        obj.ans_student_circle = models.choices.answer_choice()[ans_student] if ans_student else None
        obj.ans_official = ans_official
        obj.ans_official_circle = obj.problem.get_answer_display()
        obj.is_correct = ans_student in answer_official_list
        obj.ans_list = answer_official_list
        obj.rate_correct = obj.answer_count.get_answer_rate(ans_official)
        obj.rate_correct_top = obj.answer_count_top_rank.get_answer_rate(ans_official)
        obj.rate_correct_mid = obj.answer_count_mid_rank.get_answer_rate(ans_official)
        obj.rate_correct_low = obj.answer_count_low_rank.get_answer_rate(ans_official)
        try:
            obj.rate_gap = obj.rate_correct_top - obj.rate_correct_low
        except TypeError:
            obj.rate_gap = None

    return answer_page_obj, answer_page_range


def get_study_answer_data(request, problem_count):
    empty_answer_data = [0 for _ in range(problem_count)]
    answer_data_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data = json.loads(answer_data_cookie) or empty_answer_data
    return answer_data
