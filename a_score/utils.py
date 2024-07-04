from collections import Counter

from django.db.models import QuerySet

from a_score.models import PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount
from common.constants import icon_set_new


def get_tuple_data_answer_official_student(
        student: PrimePsatStudent,
        exam: PrimePsatExam,
        qs_answer_count: QuerySet[PrimePsatAnswerCount],
) -> tuple:

    data_answer_official: dict[str, list] = {'heonbeob': [], 'eoneo': [], 'jaryo': [], 'sanghwang': []}
    data_answer_student: dict[str, list] = {'heonbeob': [], 'eoneo': [], 'jaryo': [], 'sanghwang': []}
    subject_vars = {'헌법': 'heonbeob', '언어': 'eoneo', '자료': 'jaryo', '상황': 'sanghwang'}
    for qs in qs_answer_count:
        field: str = subject_vars[qs.subject]
        answer_official = exam.answer_official[field][qs.number - 1]
        answer_student = student.answer[field][qs.number - 1]

        if 1 <= answer_official <= 5:
            result = answer_student == answer_official
            rate_correct = getattr(qs, f'rate_{answer_official}')
        else:
            answer_official_list = [int(digit) for digit in str(answer_official)]
            result = answer_student in answer_official_list
            rate_correct = sum(getattr(qs, f'rate_{ans}') for ans in answer_official_list)

        rate_selection = getattr(qs, f'rate_{answer_student}')

        data_answer_official[field].append({
            'no': qs.number,
            'ans': answer_official,
            'rate_correct': rate_correct,
        })
        data_answer_student[field].append({
            'no': qs.number,
            'ans': answer_student,
            'rate_selection': rate_selection,
            'result': result,
        })
    return data_answer_official, data_answer_student


def get_dict_stat_data(student: PrimePsatStudent, statistics_type: str) -> dict:
    filter_exp = {'year': student.year, 'exam': student.exam, 'round': student.round}
    participants_dict = student.participants_total
    if statistics_type == 'department':
        filter_exp['department'] = student.department
        participants_dict = student.participants_department
    qs_student = PrimePsatStudent.objects.filter(**filter_exp).values('score')

    score = {}
    stat_data = {}
    fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    field_vars = {
        'heonbeob': ('헌법', '헌법'),
        'eoneo': ('언어', '언어논리'),
        'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'),
        'psat_total': ('총점', 'PSAT 총점'),
        'psat_avg': ('평균', 'PSAT 평균'),
    }
    for field in fields:
        sub, subject = field_vars[field]
        score[field] = []
        for qs in qs_student:
            if field in qs['score'].keys():
                score[field].append(qs['score'][field])

        participants = participants_dict[field]
        sorted_scores = sorted(score[field], reverse=True)

        rank = sorted_scores.index(student.score[field]) + 1
        top_10_threshold = max(1, int(participants * 0.1))
        top_20_threshold = max(1, int(participants * 0.2))

        stat_data[field] = {
            'field': field,
            'is_confirmed': True,
            'sub': sub,
            'subject': subject,
            'icon': icon_set_new.ICON_SUBJECT[sub],
            'rank': rank,
            'score': student.score[field],
            'participants': participants,
            'max_score': sorted_scores[0],
            'top_score_10': sorted_scores[top_10_threshold - 1],
            'top_score_20': sorted_scores[top_20_threshold - 1],
            'avg_score': sum(score[field]) / participants,
        }
    return stat_data


def get_dict_frequency_score(student: PrimePsatStudent) -> dict:
    qs_student = PrimePsatStudent.objects.filter(
        year=student.year, round=student.round).values_list('score', flat=True)
    score_counts_list = [round(score['psat_avg'], 1) for score in qs_student]
    score_counts_list.sort()

    score_counts = Counter(score_counts_list)

    psat_avg_colors = []
    student_psat_avg = round(student.score['psat_avg'], 1)

    for score in score_counts.keys():
        if score == student_psat_avg:
            psat_avg_colors.append('blue')
        else:
            psat_avg_colors.append('white')

    return {
        'psat_avg_points': dict(score_counts),
        'psat_avg_colors': psat_avg_colors,
    }
