from collections import defaultdict

from .admin import admin_utils
from .. import models, utils


def get_result_paginator_data(schedule_dict, student, opened_rounds, page_number) -> tuple:
    qs_result = models.StudyResult.objects.select_related('psat').filter(
        student=student, psat__round__in=opened_rounds).order_by('-psat__round')
    result_page_obj, result_page_range = utils.get_paginator_data(qs_result, page_number, 4)

    # 과제 회차 리스트 만들기
    homework_rounds = []
    for obj in result_page_obj:
        homework_rounds.append(obj.psat.round)

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

    #  커리큘럼 기준 각 회차별 등수 계산 (점수가 None인 경우는 제외)
    qs_score = models.StudyResult.objects.get_filtered_qs_ordered_by_psat_round(
        student.curriculum, psat__round__in=homework_rounds)
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
    qs_student = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_catalog(student.curriculum)
    curriculum_stat = admin_utils.get_score_stat_dict(qs_student)
    total_score_sum = score_dict['total']['score_sum']
    curriculum_stat['score_sum'] = total_score_sum
    curriculum_stat['rank'] = student.rank if total_score_sum else None
    for i in range(4):
        curriculum_stat[f'score_{i}'] = score_dict['total'][f'score_{i}']

    # 커리큘럼 기준 회차별 통계
    data_statistics = admin_utils.get_data_statistics(qs_student)
    data_statistics_dict = {}
    for data in data_statistics:
        data_statistics_dict[data['study_round']] = data

    # 각 회차별 인스턴스에 통계 및 스케줄 자료 추가
    for obj in result_page_obj:
        for key, val in score_dict[obj.psat.round].items():
            setattr(obj, key, val)
        for key, val in data_statistics_dict.get(obj.psat.round).items():
            setattr(obj, key, val)

        obj.rank = score_dict_for_rank[obj.psat.round].index(obj.score) + 1 if obj.score else None
        obj.statistics = data_statistics_dict.get(obj.psat.round)
        obj.schedule = schedule_dict.get(obj.psat.round)
    return curriculum_stat, result_page_obj, result_page_range


def get_answer_paginator_data(schedule_dict, student, opened_rounds, page_number) -> tuple:
    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(
        student.curriculum.category).filter(psat__round__in=opened_rounds).order_by('-psat')
    answer_page_obj, answer_page_range = utils.get_paginator_data(qs_problem, page_number)

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
