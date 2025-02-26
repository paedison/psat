import json
import traceback
from collections import Counter
from datetime import timedelta

import django.db.utils
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404

from .. import models


def get_score_template_table() -> list:
    return [
        'a_psat/snippets/predict_detail_sheet_score_table_1.html',
        'a_psat/snippets/predict_detail_sheet_score_table_2.html',
        'a_psat/snippets/predict_detail_sheet_score_table_2.html',
    ]


def get_sub_list(psat) -> list:
    if psat.exam in ['칠급', '칠예', '민경']:
        return ['언어', '자료', '상황']
    return ['헌법', '언어', '자료', '상황']


def get_problem_count(psat):
    if psat.exam in ['칠급', '칠예', '민경']:
        return {'언어': 25, '자료': 25, '상황': 25, '평균': 75}
    return {'헌법': 25, '언어': 40, '자료': 40, '상황': 40, '평균': 120}


def get_subject_vars(psat) -> dict[str, tuple[str, str, int]]:
    if psat.exam in ['칠급', '칠예', '민경']:
        return {
            '언어': ('언어논리', 'subject_1', 0),
            '자료': ('자료해석', 'subject_2', 1),
            '상황': ('상황판단', 'subject_3', 2),
            '평균': ('PSAT 평균', 'average', 3),
        }
    return {
        '헌법': ('헌법', 'subject_0', 0),
        '언어': ('언어논리', 'subject_1', 1),
        '자료': ('자료해석', 'subject_2', 2),
        '상황': ('상황판단', 'subject_3', 3),
        '평균': ('PSAT 평균', 'average', 4),
    }


def get_field_vars(psat) -> dict[str, tuple[str, str, int]]:
    if psat.exam in ['칠급', '칠예', '민경']:
        return {
            'subject_1': ('언어', '언어논리', 0),
            'subject_2': ('자료', '자료해석', 1),
            'subject_3': ('상황', '상황판단', 2),
            'average': ('평균', 'PSAT 평균', 3),
        }
    return {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }


def get_predict_psat(psat):
    try:
        return psat.predict_psat
    except ObjectDoesNotExist:
        return None


def get_score_tab():
    score_template_table = get_score_template_table()
    return [
        {'id': '0', 'title': '내 성적', 'prefix': 'my', 'template': score_template_table[0]},
        {'id': '1', 'title': '전체 기준', 'prefix': 'total', 'template': score_template_table[1]},
        {'id': '2', 'title': '직렬 기준', 'prefix': 'department', 'template': score_template_table[2]},
    ]


def get_answer_tab(psat):
    subject_vars = get_subject_vars(psat)
    sub_list = get_sub_list(psat)
    answer_tab = [
        {
            'id': str(idx),
            'title': sub,
            'subject': subject_vars[sub][0],
            'field': subject_vars[sub][1],
            'url_answer_input': psat.get_predict_answer_input_url(
                subject_vars[sub][1]) if sub != '평균' else '',
        }
        for idx, sub in enumerate(sub_list) if sub
    ]
    return answer_tab


def get_is_confirmed_data(qs_student_answer, psat) -> list:
    subject_vars = get_subject_vars(psat)
    is_confirmed_data = [False for _ in subject_vars.keys()]
    is_confirmed_data.pop()
    for answer in qs_student_answer:
        sub = answer.subject
        field_idx = subject_vars[sub][2]
        is_confirmed_data[field_idx] = True
        if sub in is_confirmed_data:
            is_confirmed_data[sub] = True
    is_confirmed_data.append(all(is_confirmed_data))  # Add is_confirmed_data for '평균'
    return is_confirmed_data


def get_input_answer_data_set(request, psat) -> dict:
    problem_count = get_problem_count(psat)
    problem_count.pop('평균')
    subject_vars = get_subject_vars(psat)

    empty_answer_data = {
        subject_vars[sub][1]: [0 for _ in range(cnt)] for sub, cnt in problem_count.items()
    }
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


def get_stat_data(
        psat: models.Psat,
        student: models.PredictStudent,
        is_confirmed_data: list,
        answer_data_set: dict,
        stat_type: str,
        is_filtered: bool
):
    subject_vars = get_subject_vars(psat)
    problem_count = get_problem_count(psat)
    stat_data = []
    for sub, (subject, fld, fld_idx) in subject_vars.items():
        url_answer_input = psat.get_predict_answer_input_url(fld) if sub != '평균' else ''
        answer_list = answer_data_set.get(fld)
        saved_answers = []
        if answer_list:
            saved_answers = [ans for ans in answer_list if ans]

        # 선택 답안수 업데이트
        answer_count = max(student.answer_count.get(sub, 0), len(saved_answers))

        stat_data.append({
            'field': fld, 'sub': sub, 'subject': subject,
            'start_time': get_time_schedule(psat.predict_psat)[sub][0],
            'end_time': get_time_schedule(psat.predict_psat)[sub][1],

            'participants': 0,
            'is_confirmed': is_confirmed_data[fld_idx],
            'url_answer_input': url_answer_input,

            'score_predict': 0,
            'problem_count': problem_count.get(sub),
            'answer_count': answer_count,

            'rank': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_20': 0, 'avg_score': 0,
        })

    qs_answer = models.PredictAnswer.objects.get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
        psat, student, stat_type, is_filtered)
    participants_dict = {
        subject_vars[qs_a['problem__subject']][1]: qs_a['participant_count'] for qs_a in qs_answer
    }
    participants_dict['average'] = participants_dict[min(participants_dict)] if participants_dict else 0

    field_vars = get_field_vars(psat)
    scores = {fld: [] for fld in field_vars.keys()}
    is_confirmed_for_average = []
    qs_score = models.PredictScore.objects.get_filtered_qs_by_psat_student_stat_type_and_is_filtered(
        psat, student, stat_type, is_filtered)
    for stat in stat_data:
        fld = stat['field']
        if fld in participants_dict.keys():
            participants = participants_dict.get(fld, 0)
            stat.update({'participants': participants})
            is_confirmed_for_average.append(True)
            if psat.predict_psat.is_answer_predict_opened:
                pass
            if psat.predict_psat.is_answer_official_opened:
                for qs in qs_score:
                    fld_score = qs[fld]
                    if fld_score is not None:
                        scores[fld].append(fld_score)

                student_score = getattr(student.score, fld)
                if scores[fld] and student_score:
                    sorted_scores = sorted(scores[fld], reverse=True)
                    rank = sorted_scores.index(student_score) + 1
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    avg_score = sum(scores[fld]) / participants if any(scores[fld]) else 0
                    stat.update({
                        'rank': rank,
                        'score': student_score,
                        'max_score': sorted_scores[0],
                        'top_score_10': sorted_scores[top_10_threshold - 1],
                        'top_score_20': sorted_scores[top_20_threshold - 1],
                        'avg_score': avg_score,
                    })

    return stat_data


def get_dict_frequency_score(student) -> dict:
    score_frequency_list = models.PredictStudent.objects.filter(
        psat=student.psat).values_list('score__sum', flat=True)
    score_counts_list = [round(score / 3, 1) for score in score_frequency_list if score is not None]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_target_score = round(student.score.sum / 3, 1) if student.score.sum else 0
    score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

    return {'score_points': dict(score_counts), 'score_colors': score_colors}


def get_student_score(student: models.PredictStudent) -> list:
    field_vars = get_field_vars(student.psat)
    return [getattr(student.score, field) for field in field_vars]


def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
    if answer_official_list:
        return sum(
            getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
        ) * 100 / count_sum
    return getattr(answer_count, f'count_{ans}') * 100 / count_sum


def get_data_answers(qs_student_answer, psat):
    sub_list = get_sub_list(psat)
    subject_vars = get_subject_vars(psat)
    data_answers = [[] for _ in sub_list]

    for line in qs_student_answer:
        sub = line.problem.subject
        idx = sub_list.index(sub)
        field = subject_vars[sub][1]
        ans_official = line.problem.answer
        ans_student = line.answer
        ans_predict = line.problem.predict_answer_count.answer_predict

        line.no = line.problem.number
        line.ans_official = ans_official
        line.ans_official_circle = line.problem.get_answer_display

        line.ans_student = ans_student
        line.field = field

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

        data_answers[idx].append(line)
    return data_answers


def update_score_predict(stat_total_all, qs_student_answer, psat):
    sub_list = get_sub_list(psat)
    problem_count = get_problem_count(psat)
    score_predict = {sub: 0 for sub in sub_list}
    predict_correct_count_list = qs_student_answer.filter(predict_result=True).values(
        'subject').annotate(correct_counts=Count('predict_result'))
    for entry in predict_correct_count_list:
        score = 0
        sub = entry['subject']
        problem_cnt = problem_count.get(sub)
        if problem_cnt:
            score = entry['correct_counts'] * 100 / problem_cnt
        score_predict[sub] = score
    psat_sum = 0
    for stat in stat_total_all:
        sub = stat['sub']
        if sub != '평균':
            psat_sum += score_predict[sub] if sub != '헌법' else 0
            stat['score_predict'] = score_predict[sub]
        else:
            stat['score_predict'] = psat_sum / 3


def get_time_schedule(predict_psat):
    start_time = predict_psat.exam_started_at
    exam_1_end_time = start_time + timedelta(minutes=115)  # 1교시 시험 종료 시각
    exam_2_start_time = exam_1_end_time + timedelta(minutes=95)  # 2교시 시험 시작 시각
    exam_2_end_time = exam_2_start_time + timedelta(minutes=90)  # 2교시 시험 종료 시각
    exam_3_start_time = exam_2_end_time + timedelta(minutes=30)  # 3교시 시험 시작 시각
    finish_time = exam_3_start_time + timedelta(minutes=90)  # 3교시 시험 종료 시각
    return {
        '헌법': (start_time, exam_1_end_time),
        '언어': (start_time, exam_1_end_time),
        '자료': (exam_2_start_time, exam_2_end_time),
        '상황': (exam_3_start_time, finish_time),
        '평균': (start_time, finish_time),
    }


def create_confirmed_answers(student, sub, answer_data):
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(psat=student.psat, subject=sub, number=no)
        list_create.append(models.PredictAnswer(student=student, problem=problem, answer=ans))
    bulk_create_or_update(models.PredictAnswer, list_create, [], [])


def update_answer_counts_after_confirm(predict_psat, sub, answer_data):
    qs_answer_count = models.PredictAnswerCount.objects.get_filtered_qs_by_psat(predict_psat.psat).filter(sub=sub)
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
        if not predict_psat.is_answer_official_opened:
            setattr(qs_ac, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'filtered_count_sum', F(f'count_sum') + 1)
        qs_ac.save()


def get_answer_all_confirmed(student) -> bool:
    answer_student_counts = models.PredictAnswer.objects.filter(student=student).count()
    problem_count = get_problem_count(student.psat)
    problem_count.pop('평균')
    return answer_student_counts == sum(problem_count.values())


def update_statistics_after_confirm(student, predict_psat, subject_field, answer_all_confirmed):
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


def update_predict_score_for_each_student(qs_answer, subject_field, sub):
    student: models.PredictStudent = qs_answer.first().student
    correct_count = 0
    for qs_a in qs_answer:
        correct_count += 1 if qs_a.answer_student == qs_a.answer_correct else 0

    problem_count = get_problem_count(student.psat)
    score = correct_count * 100 / problem_count.get(sub)
    setattr(student.score, subject_field, score)
    score_list = [
        sco for sco in [student.score.subject_1, student.score.subject_2, student.score.subject_3]
        if sco is not None
    ]
    score_sum = sum(score_list) if score_list else None
    score_average = round(score_sum / 3, 1) if score_sum else None

    student.score.sum = score_sum
    student.score.average = score_average
    student.score.save()


def update_predict_rank_for_each_student(qs_student, student, subject_field, field_idx, stat_type: str):
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


def get_next_url_for_answer_input(student, psat):
    sub_list = get_sub_list(psat)
    subject_vars = get_subject_vars(psat)
    for sub in sub_list:
        if sub:
            subject_field = subject_vars[sub][1]
            if student.answer_count[sub] == 0:
                return psat.get_predict_answer_input_url(subject_field)
    return psat.get_predict_detail_url()


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
