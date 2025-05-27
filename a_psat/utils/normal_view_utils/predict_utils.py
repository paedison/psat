import json
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Window, F, QuerySet
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404

from a_psat import models
from common.utils import HtmxHttpRequest
from . import common_utils


def get_predict_is_confirmed_data(
        qs_student_answer: QuerySet[models.PredictAnswer], psat: models.Psat) -> dict:
    is_confirmed_data = {sub: False for sub in common_utils.get_subject_vars(psat)}
    confirmed_sub_list = qs_student_answer.values_list('subject', flat=True).distinct()
    for sub in confirmed_sub_list:
        is_confirmed_data[sub] = True
    is_confirmed_data['평균'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '평균'
    return is_confirmed_data


def get_predict_input_answer_data_set(request: HtmxHttpRequest, psat: models.Psat) -> dict:
    empty_answer_data = {
        fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt) in common_utils.get_subject_vars(psat).items()
    }
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


def get_statistics_context(
        psat: models.Psat,
        student: models.PredictStudent,
        is_confirmed_data: dict,
        answer_data_set: dict,
        qs_student_answer,
        is_filtered: bool,
) -> dict:
    suffix = 'Filtered' if is_filtered else 'Total'
    statistics_all = get_predict_stat_data(
        student, is_confirmed_data, answer_data_set, 'all', is_filtered)
    update_predict_score_predict(statistics_all, qs_student_answer, psat)
    statistics_department = get_predict_stat_data(
        student, is_confirmed_data, answer_data_set, 'department', is_filtered)
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


def get_predict_stat_data(
        student: models.PredictStudent,
        is_confirmed_data: dict,
        answer_data_set: dict,
        stat_type: str,
        is_filtered: bool,
) -> dict:
    psat = student.psat
    predict_psat = student.psat.predict_psat
    subject_vars = common_utils.get_subject_vars(psat)

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

    scores = {sub: [] for sub in common_utils.get_subject_vars(psat)}
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


def update_predict_score_predict(
        statistics_all: dict,
        qs_student_answer: QuerySet[models.PredictAnswer],
        psat: models.Psat,
) -> None:
    subject_vars = common_utils.get_subject_vars(psat, True)
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


def get_predict_dict_stat_chart(
        student: models.PredictStudent, total_statistics_context: dict) -> dict:
    student_score = [
        getattr(student.score, fld) for (_, fld, _, _) in common_utils.get_subject_vars(student.psat).values()
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


def get_predict_dict_stat_frequency(student: models.PredictStudent) -> dict:
    score_frequency_list = models.PredictStudent.objects.filter(
        psat=student.psat, score__average__gte=50).values_list('score__average', flat=True)
    scores = [round(score, 1) for score in score_frequency_list]
    sorted_freq, target_bin = frequency_table_by_bin(scores, target_score=student.score.average)

    score_label, score_data, score_color = [], [], []
    for key, val in sorted_freq.items():
        score_label.append(key)
        score_data.append(val)
        color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
        score_color.append(color)

    return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}


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


def get_predict_answer_context(
        qs_student_answer: QuerySet[models.PredictAnswer],
        psat: models.Psat,
        is_confirmed_data: dict,
) -> dict:
    subject_vars = common_utils.get_subject_vars(psat, True)
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


def create_predict_confirmed_answers(
        student: models.PredictStudent, sub: str, answer_data: list) -> None:
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(psat=student.psat, subject=sub, number=no)
        list_create.append(models.PredictAnswer(student=student, problem=problem, answer=ans))
    common_utils.bulk_create_or_update(models.PredictAnswer, list_create, [], [])


def update_predict_answer_counts_after_confirm(
        qs_answer_count: QuerySet[models.PredictAnswerCount],
        psat: models.Psat,
        answer_data: list,
) -> None:
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
        if not psat.predict_psat.is_answer_official_opened:
            setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
        qs_ac.save()


def get_predict_answer_all_confirmed(student: models.PredictStudent) -> bool:
    answer_student_counts = models.PredictAnswer.objects.filter(student=student).count()
    problem_count_sum = sum([
        value[3] for value in common_utils.get_subject_vars(student.psat, True).values()
    ])
    return answer_student_counts == problem_count_sum


def update_predict_statistics_after_confirm(
        student: models.PredictStudent,
        subject_field: str,
        answer_all_confirmed: bool
) -> None:
    predict_psat = student.psat.predict_psat

    def get_statistics_and_edit_participants(department: str):
        stat = get_object_or_404(models.PredictStatistics, psat=student.psat, department=department)

        # Update participants for each subject [All, Filtered]
        getattr(stat, subject_field)['participants'] += 1
        if not predict_psat.is_answer_official_opened:
            getattr(stat, f'filtered_{subject_field}')['participants'] += 1

        # Update participants for average [All, Filtered]
        if answer_all_confirmed:
            stat.average['participants'] += 1
            if not predict_psat.is_answer_official_opened:
                stat.filtered_average['participants'] += 1
                student.is_filtered = True
                student.save()
        stat.save()

    get_statistics_and_edit_participants('전체')
    get_statistics_and_edit_participants(student.department)


def update_predict_score_for_each_student(
        qs_answer: QuerySet[models.PredictAnswer],
        subject_field: str,
        sub: str
) -> None:
    student = qs_answer.first().student
    score = student.score
    correct_count = 0
    for qs_a in qs_answer:
        correct_count += 1 if qs_a.answer_student == qs_a.answer_correct else 0

    problem_count = common_utils.get_subject_vars(student.psat)[sub][3]
    score_point = correct_count * 100 / problem_count
    setattr(score, subject_field, score_point)

    score_list = [sco for sco in [score.subject_1, score.subject_2, score.subject_3] if sco is not None]
    score_sum = sum(score_list) if score_list else None
    score_average = round(score_sum / 3, 1) if score_sum else None

    score.sum = score_sum
    score.average = score_average
    score.save()


def update_predict_rank_for_each_student(
        qs_student: QuerySet[models.PredictStudent],
        student: models.PredictStudent,
        subject_field: str,
        field_idx: int,
        stat_type: str
) -> None:
    field_average = 'average'

    rank_model = models.PredictRankTotal
    if stat_type == 'department':
        rank_model = models.PredictRankCategory

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {
        f'rank_{field_idx}': rank_func(f'score__{subject_field}'),
        'rank_average': rank_func(f'score__{field_average}')
    }

    rank_list = qs_student.annotate(**annotate_dict)
    if stat_type == 'department':
        rank_list = rank_list.filter(category=student.category)
    participants = rank_list.count()

    target, _ = rank_model.objects.get_or_create(student=student)
    fields_not_match = [target.participants != participants]

    for entry in rank_list:
        if entry.id == student.id:
            score_for_field = getattr(entry, f'rank_{field_idx}')
            score_for_average = getattr(entry, f'rank_average')
            fields_not_match.append(getattr(target, subject_field) != score_for_field)
            fields_not_match.append(target.average != entry.rank_average)

            if any(fields_not_match):
                target.participants = participants
                setattr(target, subject_field, score_for_field)
                setattr(target, field_average, score_for_average)
                target.save()


def get_predict_next_url_for_answer_input(
        student: models.PredictStudent, psat: models.Psat) -> str:
    subject_vars = common_utils.get_subject_vars(psat, True)
    for sub, (_, fld, _, _) in subject_vars.items():
        if student.answer_count[sub] == 0:
            return psat.get_predict_answer_input_url(fld)
    return psat.get_predict_detail_url()
