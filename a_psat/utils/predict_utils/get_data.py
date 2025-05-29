import json
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, F, QuerySet

from a_psat import models
from a_psat.utils.variables import *
from a_psat.utils.decorators import *
from common.utils import HtmxHttpRequest, get_paginator_context


@for_normal_views
def get_normal_is_confirmed_data(
        qs_student_answer: QuerySet[models.PredictAnswer], psat: models.Psat) -> dict:
    is_confirmed_data = {sub: False for sub in get_subject_vars(psat)}
    confirmed_sub_list = qs_student_answer.values_list('subject', flat=True).distinct()
    for sub in confirmed_sub_list:
        is_confirmed_data[sub] = True
    is_confirmed_data['평균'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '평균'
    return is_confirmed_data


@for_normal_views
def get_normal_input_answer_data_set(request: HtmxHttpRequest, psat: models.Psat) -> dict:
    empty_answer_data = {
        fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in get_subject_vars(psat).items()
    }
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


@for_normal_views
def get_normal_statistics_context(
        psat: models.Psat,
        student: models.PredictStudent,
        is_confirmed_data: dict,
        answer_data_set: dict,
        qs_student_answer,
        is_filtered: bool,
) -> dict:
    suffix = 'Filtered' if is_filtered else 'Total'
    statistics_all = get_normal_statistics_data(
        student, is_confirmed_data, answer_data_set, 'all', is_filtered)
    statistics_department = get_normal_statistics_data(
        student, is_confirmed_data, answer_data_set, 'department', is_filtered)
    update_normal_score_predict(statistics_all, qs_student_answer, psat)

    return {
        'all': {
            'id': '0', 'title': '전체 기준',
            'prefix': f'All{suffix}Score', 'page_obj': statistics_all,
        },
        'department': {
            'id': '1', 'title': '직렬 기준',
            'prefix': f'Department{suffix}Score', 'page_obj': statistics_department,
        },
    }


@for_normal_views
def get_normal_statistics_data(
        student: models.PredictStudent,
        is_confirmed_data: dict,
        answer_data_set: dict,
        stat_type: str,
        is_filtered: bool,
) -> dict:
    psat = student.psat
    predict_psat = student.psat.predict_psat
    subject_vars = get_subject_vars(psat)

    stat_data = {}
    for sub, (subject, fld, _, problem_count) in subject_vars.items():
        url_answer_input = psat.get_predict_answer_input_url(fld) if sub != '평균' else ''
        answer_list = answer_data_set.get(fld)
        saved_answers = []
        if answer_list:
            saved_answers = [ans for ans in answer_list if ans]

        # 선택 답안수 업데이트
        answer_count = max(student.answer_count.get(sub, 0), len(saved_answers))

        stat_data[sub] = {
            'field': fld, 'sub': sub, 'subject': subject,
            'start_time': get_time_schedule(predict_psat)[sub][0],
            'end_time': get_time_schedule(predict_psat)[sub][1],

            'participants': 0,
            'is_confirmed': is_confirmed_data[sub],
            'url_answer_input': url_answer_input,

            'score_predict': 0,
            'problem_count': problem_count,
            'answer_count': answer_count,

            'rank': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0,
        }

    qs_answer = models.PredictAnswer.objects.get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
        psat, student, stat_type, is_filtered)
    participants_dict = {qs_a['problem__subject']: qs_a['participant_count'] for qs_a in qs_answer}
    participants_dict['평균'] = participants_dict[min(participants_dict)] if participants_dict else 0

    scores = {sub: [] for sub in get_subject_vars(psat)}
    is_confirmed_for_average = []
    qs_score = models.PredictScore.objects.get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
        psat, student, stat_type, is_filtered)

    for sub, stat in stat_data.items():
        fld = subject_vars[sub][1]
        if sub in participants_dict.keys():
            participants = participants_dict.get(sub, 0)
            stat['participants'] = participants
            is_confirmed_for_average.append(True)
            if predict_psat.is_answer_predict_opened:
                pass
            if predict_psat.is_answer_official_opened:
                for qs in qs_score:
                    fld_score = qs[fld]
                    if fld_score is not None:
                        scores[sub].append(fld_score)

                student_score = getattr(student.score, fld)
                if scores[sub] and student_score:
                    sorted_scores = sorted(scores[sub], reverse=True)
                    rank = sorted_scores.index(student_score) + 1
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    avg_score = round(sum(scores[sub]) / participants, 1) if any(scores[sub]) else 0
                    stat.update({
                        'rank': rank,
                        'score': student_score,
                        'max_score': sorted_scores[0],
                        'top_score_10': sorted_scores[top_10_threshold - 1],
                        'top_score_20': sorted_scores[top_20_threshold - 1],
                        'avg_score': avg_score,
                    })

    return stat_data


@for_normal_views
def update_normal_score_predict(
        statistics_all: dict,
        qs_student_answer: QuerySet[models.PredictAnswer],
        psat: models.Psat,
) -> None:
    subject_vars = get_subject_vars(psat, True)
    score_predict = {sub: 0 for sub in subject_vars}
    predict_correct_count_list = qs_student_answer.filter(predict_result=True).values(
        'subject').annotate(correct_counts=Count('predict_result'))

    psat_sum = 0
    for entry in predict_correct_count_list:
        score = 0
        sub = entry['subject']
        problem_count = subject_vars[sub][3]
        if problem_count:
            score = entry['correct_counts'] * 100 / problem_count

        score_predict[sub] = score
        psat_sum += score if sub != '헌법' else 0
        statistics_all[sub]['score_predict'] = score
    statistics_all['평균']['score_predict'] = round(psat_sum / 3, 1)


@for_normal_views
def get_normal_dict_stat_chart(
        student: models.PredictStudent, total_statistics_context: dict) -> dict:
    student_score = [
        getattr(student.score, fld) for (_, fld, _, _) in get_subject_vars(student.psat).values()
    ]
    chart_score = {
        'my_score': student_score,
        'all_avg': [], 'all_top_20': [], 'all_top_10': [], 'all_max': [],
        'dep_avg': [], 'dep_top_20': [], 'dep_top_10': [], 'dep_max': [],
    }

    for stat in total_statistics_context['all']['page_obj'].values():
        chart_score['all_avg'].append(stat['avg_score'])
        chart_score['all_top_20'].append(stat['top_score_20'])
        chart_score['all_top_10'].append(stat['top_score_10'])
        chart_score['all_max'].append(stat['max_score'])
    for stat in total_statistics_context['department']['page_obj'].values():
        chart_score['dep_avg'].append(stat['avg_score'])
        chart_score['dep_top_20'].append(stat['top_score_20'])
        chart_score['dep_top_10'].append(stat['top_score_10'])
        chart_score['dep_max'].append(stat['max_score'])

    score_list = [score for score in student_score if score is not None]
    chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0
    return chart_score


@for_normal_views
def get_normal_dict_stat_frequency(student: models.PredictStudent) -> dict:
    score_frequency_list = models.PredictStudent.objects.filter(
        psat=student.psat, score__average__gte=50).values_list('score__average', flat=True)
    scores = [round(score, 1) for score in score_frequency_list]
    sorted_freq, target_bin = frequency_table_by_bin(scores, target_score=student.score.average)  # noqa

    score_label, score_data, score_color = [], [], []
    for key, val in sorted_freq.items():
        score_label.append(key)
        score_data.append(val)
        color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
        score_color.append(color)

    return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}


@for_normal_views
def frequency_table_by_bin(
        scores: list, bin_size: int = 5, target_score: float | None = None) -> tuple[dict, str | None]:
    freq = defaultdict(int)
    for score in scores:
        bin_start = int((score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        bin_label = f'{bin_start}~{bin_end}'
        freq[bin_label] += 1

    # bin_start 기준으로 정렬
    sorted_freq = dict(sorted(freq.items(), key=lambda x: int(x[0].split('~')[0])))

    # 특정 점수의 구간 구하기
    target_bin = None
    if target_score is not None:
        bin_start = int((target_score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        target_bin = f'{bin_start}~{bin_end}'

    return sorted_freq, target_bin


@for_normal_views
def get_normal_answer_context(
        qs_student_answer: QuerySet[models.PredictAnswer],
        psat: models.Psat,
        is_confirmed_data: dict,
) -> dict:
    subject_vars = get_subject_vars(psat, True)
    context = {
        sub: {
            'id': str(idx), 'title': sub, 'subject': subject, 'field': field,
            'url_answer_input': psat.get_predict_answer_input_url(field),
            'is_confirmed': is_confirmed_data[sub], 'loop_list': get_loop_list(problem_count),
            'page_obj': [],
        }
        for sub, (subject, field, idx, problem_count) in subject_vars.items()
    }

    for line in qs_student_answer:
        sub = line.problem.subject
        ans_official = line.problem.answer
        ans_student = line.answer
        ans_predict = line.problem.predict_answer_count.answer_predict

        line.no = line.problem.number
        line.ans_official = ans_official
        line.ans_official_circle = line.problem.get_answer_display

        line.ans_student = ans_student
        line.field = subject_vars[sub][1]

        line.ans_predict = ans_predict
        line.rate_accuracy = line.problem.predict_answer_count.get_answer_predict_rate()

        line.rate_correct = line.problem.predict_answer_count.get_answer_rate(ans_official)
        line.rate_correct_top = line.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
        line.rate_correct_mid = line.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
        line.rate_correct_low = line.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
        if line.rate_correct_top is not None and line.rate_correct_low is not None:
            line.rate_gap = line.rate_correct_top - line.rate_correct_low
        else:
            line.rate_gap = 0

        line.rate_selection = line.problem.predict_answer_count.get_answer_rate(ans_student)
        line.rate_selection_top = line.problem.predict_answer_count_top_rank.get_answer_rate(ans_student)
        line.rate_selection_mid = line.problem.predict_answer_count_mid_rank.get_answer_rate(ans_student)
        line.rate_selection_low = line.problem.predict_answer_count_low_rank.get_answer_rate(ans_student)

        context[sub]['page_obj'].append(line)
    return context


@for_normal_views
def get_loop_list(problem_count: int):
    loop_list = []
    quotient = problem_count // 10
    counter_list = [10] * quotient
    remainder = problem_count % 10
    if remainder:
        counter_list.append(remainder)
    loop_min = 0
    for idx, counter in enumerate(counter_list):
        loop_list.append({'counter': counter, 'min': loop_min})
        loop_min += 10
    return loop_list


@for_normal_views
def get_time_schedule(predict_psat: models.PredictPsat) -> dict:
    start_time = predict_psat.exam_started_at
    exam_1_end_time = start_time + timedelta(minutes=115)  # 1교시 시험 종료 시각
    exam_2_start_time = exam_1_end_time + timedelta(minutes=110)  # 2교시 시험 시작 시각
    exam_2_end_time = exam_2_start_time + timedelta(minutes=90)  # 2교시 시험 종료 시각
    exam_3_start_time = exam_2_end_time + timedelta(minutes=45)  # 3교시 시험 시작 시각
    finish_time = predict_psat.exam_finished_at  # 3교시 시험 종료 시각
    return {
        '헌법': (start_time, exam_1_end_time),
        '언어': (start_time, exam_1_end_time),
        '자료': (exam_2_start_time, exam_2_end_time),
        '상황': (exam_3_start_time, finish_time),
        '평균': (start_time, finish_time),
    }


@for_normal_views
def get_normal_answer_all_confirmed(student: models.PredictStudent) -> bool:
    answer_student_counts = models.PredictAnswer.objects.filter(student=student).count()
    problem_count_sum = sum([value[3] for value in get_subject_vars(student.psat, True).values()])
    return answer_student_counts == problem_count_sum


@for_admin_views
def get_admin_statistics_context(psat: models.Psat, page_number=1, per_page=10) -> dict:
    total_data, filtered_data = get_admin_statistics_data(psat)
    total_context = get_paginator_context(total_data, page_number, per_page)
    filtered_context = get_paginator_context(filtered_data, page_number, per_page)
    total_context.update({
        'id': '0', 'title': '전체', 'prefix': 'TotalStatistics', 'header': 'total_statistics_list',
    })
    filtered_context.update({
        'id': '1', 'title': '필터링', 'prefix': 'FilteredStatistics', 'header': 'filtered_statistics_list',
    })
    return {'total': total_context, 'filtered': filtered_context}


@for_admin_views
def get_admin_statistics_data(psat: models.Psat) -> tuple[list, list]:
    subject_vars = get_subject_vars(psat)

    department_list = list(
        models.PredictCategory.objects.filter(exam=psat.exam).order_by('order')
        .values_list('department', flat=True)
    )
    department_list.insert(0, '전체')

    total_data, filtered_data = defaultdict(dict), defaultdict(dict)
    total_scores, filtered_scores = defaultdict(dict), defaultdict(dict)
    for department in department_list:
        total_data[department] = {'department': department, 'participants': 0}
        filtered_data[department] = {'department': department, 'participants': 0}
        total_scores[department] = {sub: [] for sub in subject_vars}
        filtered_scores[department] = {sub: [] for sub in subject_vars}

    qs_students = (
        models.PredictStudent.objects.filter(psat=psat)
        .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
        .annotate(
            department=F('category__department'),
            subject_0=F('score__subject_0'),
            subject_1=F('score__subject_1'),
            subject_2=F('score__subject_2'),
            subject_3=F('score__subject_3'),
            average=F('score__average'),
        )
    )
    for qs_s in qs_students:
        for sub, (_, field, _, _) in subject_vars.items():
            score = getattr(qs_s, field)
            if score is not None:
                total_scores['전체'][sub].append(score)
                total_scores[qs_s.department][sub].append(score)
                if qs_s.is_filtered:
                    filtered_scores['전체'][sub].append(score)
                    filtered_scores[qs_s.department][sub].append(score)

    update_admin_statistics_data(total_data, subject_vars, total_scores)
    update_admin_statistics_data(filtered_data, subject_vars, filtered_scores)

    return list(total_data.values()), list(filtered_data.values())


@for_admin_views
def update_admin_statistics_data(
        data_statistics: dict,
        subject_vars: dict,
        score_list: dict,
) -> None:
    for department, score_dict in score_list.items():
        for sub, scores in score_dict.items():
            subject, field, _, _ = subject_vars[sub]
            participants = len(scores)

            sorted_scores = sorted(scores, reverse=True)
            max_score = top_score_10 = top_score_20 = avg_score = None
            if sorted_scores:
                max_score = sorted_scores[0]
                top_10_threshold = max(1, int(participants * 0.1))
                top_20_threshold = max(1, int(participants * 0.2))
                top_score_10 = sorted_scores[top_10_threshold - 1]
                top_score_20 = sorted_scores[top_20_threshold - 1]
                avg_score = round(sum(scores) / participants, 1)

            data_statistics[department][field] = {
                'field': field,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'participants': participants,
                'max': max_score,
                't10': top_score_10,
                't20': top_score_20,
                'avg': avg_score,
            }


@for_admin_views
def get_admin_catalog_context(psat: models.Psat, page_number=1, total_list=None) -> dict:
    if total_list is None:
        total_list = models.PredictStudent.objects.get_filtered_qs_student_list_by_psat(psat)
    filtered_list = total_list.filter(is_filtered=True)
    total_context = get_paginator_context(total_list, page_number)
    filtered_context = get_paginator_context(filtered_list, page_number)

    field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
    for obj in filtered_context['page_obj']:
        obj.rank_tot_num = obj.filtered_rank_tot_num
        obj.rank_dep_num = obj.filtered_rank_dep_num
        for key, fld in field_dict.items():
            setattr(obj, f'rank_tot_{key}', getattr(obj, f'filtered_rank_tot_{key}'))
            setattr(obj, f'rank_dep_{key}', getattr(obj, f'filtered_rank_dep_{key}'))

    total_context.update({
        'id': '0', 'title': '전체', 'prefix': 'TotalCatalog', 'header': 'total_catalog_list',
    })
    filtered_context.update({
        'id': '1', 'title': '필터링', 'prefix': 'FilteredCatalog', 'header': 'filtered_catalog_list',
    })

    return {'total': total_context, 'filtered': filtered_context}


@for_admin_views
def get_admin_answer_context(psat: models.Psat, subject=None, page_number=1, per_page=10) -> dict:
    subject_vars = get_subject_vars(psat, True)
    sub_list = [sub for sub in subject_vars]
    qs_answer_count_group = {sub: [] for sub in subject_vars}
    answer_context = {}

    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat_and_subject(psat, subject)
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        if sub not in qs_answer_count_group:
            qs_answer_count_group[sub] = []
        qs_answer_count_group[sub].append(qs_ac)

    for sub, qs_answer_count in qs_answer_count_group.items():
        if qs_answer_count:
            data_answers = get_admin_answer_data(qs_answer_count, subject_vars)
            context = get_paginator_context(data_answers, page_number, per_page)
            context.update({
                'id': str(sub_list.index(sub)),
                'title': sub,
                'prefix': 'Answer',
                'header': 'answer_list',
                'answer_count': 4 if sub == '헌법' else 5,
            })
            answer_context[sub] = context

    return answer_context


@for_admin_views
def get_admin_answer_data(qs_answer_count: QuerySet, subject_vars: dict) -> QuerySet:
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        field = subject_vars[sub][1]
        ans_official = qs_ac.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_ac.no = qs_ac.number
        qs_ac.ans_official = ans_official
        qs_ac.ans_official_circle = qs_ac.problem.get_answer_display()
        qs_ac.ans_predict_circle = models.choices.answer_choice()[qs_ac.ans_predict] if qs_ac.ans_predict else None
        qs_ac.ans_list = answer_official_list
        qs_ac.field = field

        qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
        qs_ac.rate_correct_top = qs_ac.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
        qs_ac.rate_correct_mid = qs_ac.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
        qs_ac.rate_correct_low = qs_ac.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
        try:
            qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
        except TypeError:
            qs_ac.rate_gap = None

    return qs_answer_count


@for_admin_views
def get_admin_only_answer_context(queryset: QuerySet, subject_vars: dict) -> dict:
    query_dict = defaultdict(list)
    for query in queryset.order_by('id'):
        query_dict[query.subject].append(query)
    return {
        sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
        for sub, (_, _, idx, _) in subject_vars.items()
    }
