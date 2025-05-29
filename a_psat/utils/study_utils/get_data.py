import json
from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django_htmx.http import reswap

from a_psat import models
from a_psat.utils.decorators import *
from common.utils import get_paginator_context, HtmxHttpRequest, update_context_data


@for_all_views
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


@for_all_views
def get_study_lecture_context(qs_schedule, page_number=1, per_page=4):
    context = get_paginator_context(qs_schedule, page_number, per_page)
    lecture_dict = {}
    for lec in models.Lecture.objects.all():
        lecture_dict[(lec.subject, lec.order)] = lec.id

    if context:
        for obj in context['page_obj']:
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
        return context


@for_admin_views
def update_admin_context_statistics(page_obj, is_curriculum=False):
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


@for_admin_views
def get_study_score_stat_dict(qs_student) -> dict:
    # stat_dict keys: participants, max, avg, t10, t25, t50
    stat_dict = models.get_study_statistics_aggregation(qs_student)
    participants = stat_dict['participants']
    if participants != 0:
        score_list = list(qs_student.values_list('score_total', flat=True))

        def get_score(rank_rate: float):
            threshold = max(1, int(participants * rank_rate))
            return score_list[threshold] if threshold < participants else None

        stat_dict['t10'] = get_score(0.10)
        stat_dict['t25'] = get_score(0.25)
        stat_dict['t50'] = get_score(0.50)
    return stat_dict


@for_admin_views
def update_admin_problem_answer_data_for_context(qs_problem):
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


@for_normal_views
def get_normal_student_context(request: HtmxHttpRequest):
    student_context = None
    if request.user.is_authenticated:
        student_context = models.StudyStudent.objects.get_filtered_qs_by_user(request.user)

        qs_curriculum_schedule_info = models.StudyCurriculumSchedule.objects.get_curriculum_schedule_info()
        schedule_info = defaultdict()
        for qs_cs in qs_curriculum_schedule_info:
            schedule_info[qs_cs['curriculum']] = qs_cs

        for qs_s in student_context:
            qs_s.study_rounds = schedule_info[qs_s.curriculum_id]['study_rounds']
            qs_s.earliest_datetime = schedule_info[qs_s.curriculum_id]['earliest']
            qs_s.latest_datetime = schedule_info[qs_s.curriculum_id]['latest']
    return student_context


@for_normal_views
def get_normal_homework_schedule(qs_schedule):
    homework_schedule = defaultdict(dict)
    for qs_s in qs_schedule:
        if qs_s.lecture_round:
            homework_schedule[qs_s.lecture_round]['lecture_datetime'] = qs_s.lecture_datetime
            homework_schedule[qs_s.lecture_round]['lecture_open_datetime'] = qs_s.lecture_open_datetime
        if qs_s.homework_round:
            homework_schedule[qs_s.homework_round]['homework_end_datetime'] = qs_s.homework_end_datetime
    return homework_schedule


@for_normal_views
def get_normal_curriculum_statistics(qs_student):
    total_stat = get_study_score_stat_dict(qs_student)
    data_statistics = get_study_data_statistics(qs_student)
    per_round_stat = {}
    for data in data_statistics:
        per_round_stat[data['study_round']] = data
    return {
        'total': total_stat,
        'per_round': per_round_stat,
    }


@for_normal_views
def get_normal_my_result_context(
        homework_schedule, student, opened_rounds, qs_result, curriculum_statistics, page_number=1):
    context = get_paginator_context(qs_result, page_number, 4)
    score_dict = get_normal_score_dict(student)

    # 전체 등수 및 통계
    context['total'] = get_normal_my_total_result(student, opened_rounds, curriculum_statistics, score_dict)

    # 회차별 등수 및 통계, 스케줄 자료
    score_dict_for_rank = get_normal_score_dict_for_rank(student, opened_rounds)
    for obj in context['page_obj']:
        for key, val in score_dict[obj.psat.round].items():
            setattr(obj, key, val)

        obj.rank = score_dict_for_rank[obj.psat.round].index(obj.score) + 1 if obj.score else None
        stat = curriculum_statistics['per_round'].get(obj.psat.round)
        obj.participants = stat['participants'] if stat else None
        obj.schedule = homework_schedule.get(obj.psat.round)
    return context


@for_normal_views
def get_normal_score_dict(student):
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


@for_normal_views
def get_normal_my_total_result(student, opened_rounds, curriculum_statistics, score_dict):
    qs_rank = models.StudyStudent.objects.get_filtered_qs_by_curriculum_for_rank(student.curriculum)
    rank = None
    for qs_r in qs_rank:
        if qs_r.id == student.id:
            rank = qs_r.rank

    total_stat = curriculum_statistics['total']
    problem_count = models.StudyProblem.objects.filter(
        psat__category=student.curriculum.category, psat__round__in=opened_rounds).count()
    my_total_result = {
        'total_score_sum': problem_count,
        'score_sum': score_dict['total']['score_sum'],
        'participants': total_stat['participants'],
        'rank': rank if score_dict['total']['score_sum'] else None,
    }
    for i in range(4):
        my_total_result[f'score_{i}'] = score_dict['total'][f'score_{i}']
    return my_total_result


@for_normal_views
def get_normal_score_dict_for_rank(student, opened_rounds):
    qs_score = models.StudyResult.objects.get_filtered_qs_ordered_by_psat_round(
        student.curriculum, psat__round__in=opened_rounds)
    score_dict_for_rank = defaultdict(list)
    for qs_s in qs_score:
        score = qs_s['score']
        if score is not None:
            score_dict_for_rank[qs_s['round']].append(score)
    for rnd, score_list in score_dict_for_rank.items():
        score_dict_for_rank[rnd] = sorted(score_list, reverse=True)
    return score_dict_for_rank


@for_normal_views
def get_normal_statistics_context(homework_schedule, qs_result, curriculum_statistics, page_number=1):
    per_round_stat = curriculum_statistics['per_round']
    context = get_paginator_context(qs_result, page_number, 4)
    for obj in context['page_obj']:
        data_stat = per_round_stat.get(obj.psat.round)
        if data_stat:
            for key, val in data_stat.items():
                setattr(obj, key, val)

        obj.statistics = data_stat
        obj.schedule = homework_schedule.get(obj.psat.round)
    return context


@for_normal_views
def get_normal_answer_context(schedule_dict, student, opened_rounds, page_number=1):
    qs_problem = models.StudyProblem.objects.get_filtered_qs_by_category_annotated_with_answer_count(
        student.curriculum.category).filter(psat__round__in=opened_rounds).order_by('-psat')
    context = get_paginator_context(qs_problem, page_number, on_each_side=1)

    homework_rounds = []
    for obj in context['page_obj']:
        homework_rounds.append(obj.psat.round)

    qs_answer = models.StudyAnswer.objects.with_select_related().filter(
        student=student, problem__psat__round__in=homework_rounds)
    answer_student_dict = defaultdict(dict)
    for qs_a in qs_answer:
        answer_student_dict[(qs_a.problem.psat.round, qs_a.problem.number)] = qs_a.answer

    for obj in context['page_obj']:
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

    return context


@for_normal_views
def get_normal_answer_data(request, problem_count):
    empty_answer_data = [0 for _ in range(problem_count)]
    answer_data_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data = json.loads(answer_data_cookie) or empty_answer_data
    return answer_data


@for_normal_views
def get_normal_answer_submit_response(request, context, problem_count, answer_data):
    try:
        no = int(request.POST.get('number'))
        ans = int(request.POST.get('answer'))
    except Exception as e:
        print(e)
        return reswap(HttpResponse(''), 'none')

    context = update_context_data(context, answer={'no': no, 'ans': ans})
    response = render(request, 'a_psat/snippets/predict_answer_button.html', context)

    if 1 <= no <= problem_count and 1 <= ans <= 5:
        answer_data[no - 1] = ans
        response.set_cookie('answer_data_set', json.dumps(answer_data), max_age=3600)
        return response
    else:
        print('Answer is not appropriate.')
        return reswap(HttpResponse(''), 'none')
