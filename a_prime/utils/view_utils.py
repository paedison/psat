from collections import Counter

from django.db.models import Count

from common.constants import icon_set_new
from ..models import ResultStudent
from ..views.score_info import ScorePsatExamVars

__all__ = [
    'get_exam_vars', 'get_admin_exam_vars',
    'get_data_answer', 'get_dict_stat_data',
    'get_dict_frequency_score',
]


def get_exam_vars(exam_type: str, exam_year: int, exam_round: int) -> ScorePsatExamVars:
    if exam_type == 'psat':
        return ScorePsatExamVars(exam_type, exam_year, exam_round)


def get_admin_exam_vars(exam_type: str, exam_year: int, exam_round: int):
    if exam_type == 'psat':
        return ScorePsatExamVars(exam_type, exam_year, exam_round)


def get_data_answer(exam_vars: ScorePsatExamVars, qs_student_answer):
    data_answer_official = exam_vars.get_empty_data_answer()
    data_answer_student = exam_vars.get_empty_data_answer()
    for line in qs_student_answer:
        subject = line.problem.subject
        idx = exam_vars.sub_list.index(subject)
        field = exam_vars.subject_vars[subject][1]
        no = line.problem.number
        answer_count = line.problem.result_answer_count
        ans_official = line.problem.answer
        ans_student = line.answer

        count_total = answer_count.count_total

        if 1 <= ans_official <= 5:
            result = ans_student == ans_official
            rate_correct = getattr(answer_count, f'count_{ans_official}') * 100 / count_total
        else:
            answer_official_list = [int(digit) for digit in str(ans_official)]
            result = ans_student in answer_official_list
            rate_correct = sum(getattr(answer_count, f'count_{ans}') for ans in answer_official_list) * 100 / count_total
        rate_selection = getattr(answer_count, f'count_{ans_student}') * 100 / count_total

        data_answer_official[idx][no - 1].update({
            'no': no, 'ans': ans_official,
            'field': field, 'rate_correct': rate_correct,
        })
        data_answer_student[idx][no - 1].update({
            'no': no, 'ans': ans_student,
            'field': field, 'rate_selection': rate_selection,
            'result': result,
        })
    return data_answer_official, data_answer_student


def get_dict_stat_data(exam_vars: ScorePsatExamVars, student: ResultStudent, stat_type: str) -> dict:
    if stat_type == 'total':
        qs_answers = (
            exam_vars.answer_model.objects.filter(problem__psat=exam_vars.psat)
            .values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        qs_score = exam_vars.score_model.objects.filter(student__psat=exam_vars.psat).values()
    else:
        qs_answers = (
            exam_vars.answer_model.objects
            .filter(problem__psat=exam_vars.psat, student__category__department=student.category.department)
            .values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        qs_score = exam_vars.score_model.objects.filter(
            student__psat=exam_vars.psat, student__category__department=student.category.department).values()

    participants_dict = {
        exam_vars.subject_vars[entry['problem__subject']][1]: entry['participant_count'] for entry in qs_answers
    }
    participants_dict['psat_avg'] = max(
        participants_dict['eoneo'], participants_dict['jaryo'], participants_dict['sanghwang']
    )

    scores = {}
    stat_data = {}
    field_vars = {
        'heonbeob': ('헌법', '헌법', 0),
        'eoneo': ('언어', '언어논리', 1),
        'jaryo': ('자료', '자료해석', 2),
        'sanghwang': ('상황', '상황판단', 3),
        'psat_avg': ('평균', 'PSAT 평균', 4),
    }
    for field, subject_tuple in field_vars.items():
        field_idx = subject_tuple[2]
        if field in participants_dict.keys():
            participants = participants_dict[field]
            if field != 'psat_avg':
                scores[field] = [qs[f'subject_{field_idx}'] for qs in qs_score]
                student_score = getattr(student.score, f'subject_{field_idx}')
            else:
                scores[field] = [qs['total'] / 3 for qs in qs_score]
                student_score = student.score.total / 3

            sorted_scores = sorted(scores[field], reverse=True)
            rank = sorted_scores.index(student_score) + 1
            top_10_threshold = max(1, int(participants * 0.1))
            top_20_threshold = max(1, int(participants * 0.2))

            stat_data[field] = {
                'field': field,
                'is_confirmed': True,
                'sub': subject_tuple[0],
                'subject': subject_tuple[1],
                'icon': icon_set_new.ICON_SUBJECT[subject_tuple[0]],
                'rank': rank,
                'score': student_score,
                'participants': participants,
                'max_score': sorted_scores[0],
                'top_score_10': sorted_scores[top_10_threshold - 1],
                'top_score_20': sorted_scores[top_20_threshold - 1],
                'avg_score': sum(scores[field]) / participants,
            }
    return stat_data


def get_dict_frequency_score(exam_vars: ScorePsatExamVars, student) -> dict:
    qs_student = exam_vars.student_model.objects.filter(psat=student.psat).values_list('score__total', flat=True)
    score_counts_list = [round(score / 3, 1) for score in qs_student]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)
    student_target_score = round(student.score.total / 3, 1)
    score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

    return {'score_points': dict(score_counts), 'score_colors': score_colors}
