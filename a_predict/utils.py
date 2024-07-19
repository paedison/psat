import numpy as np
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Count, Max, Avg
from django.db.models import Window
from django.db.models.functions import Rank, PercentRank
from django.urls import reverse

from common.constants import icon_set_new


def get_student(request, exam_vars: dict):
    if request.user.is_authenticated:
        return exam_vars['student_model'].objects.filter(
            **exam_vars['exam_info'], user=request.user).first()


def get_exam(exam_vars: dict):
    return exam_vars['exam_model'].objects.filter(**exam_vars['exam_info']).first()


def get_location(exam_vars: dict, student):
    serial = int(student.serial)
    return exam_vars['location_model'].objects.filter(
        **exam_vars['exam_info'], serial_start__lte=serial, serial_end__gte=serial).first()


def get_qs_department(exam_vars: dict):
    return exam_vars['department_model'].objects.filter(exam=exam_vars['exam']).order_by('id')


def get_qs_student(exam_vars: dict):
    return exam_vars['student_model'].objects.filter(**exam_vars['exam_info'])


def get_qs_answer_count(exam_vars: dict):
    return exam_vars['answer_count_model'].objects.filter(**exam_vars['exam_info']).annotate(
        no=F('number')).order_by('subject', 'number')


def get_answer_confirmed(exam_vars: dict, student):
    return [student.answer_confirmed[field] for field in exam_vars['score_fields']]


def update_exam_participants(exam_vars: dict, exam, qs_department, qs_student):
    score_fields = exam_vars['score_fields']
    department_dict = {department.name: department.id for department in qs_department}

    participants = {
        'all': {'total': {field: 0 for field in score_fields}},
        'filtered': {'total': {field: 0 for field in score_fields}},
    }
    participants['all'].update({
        d_id: {field: 0 for field in score_fields} for d_id in department_dict.values()
    })
    participants['filtered'].update({
        d_id: {field: 0 for field in score_fields} for d_id in department_dict.values()
    })

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
    exam.participants = participants
    exam.save()

    return participants


def get_empty_data_answer(fields: list, problem_count: dict):
    return [
        [
            {'no': no, 'ans': 0, 'field': field} for no in range(1, problem_count[field] + 1)
         ] for field in fields
    ]


def get_data_answer_official(exam_vars: dict, exam) -> tuple[list, bool]:
    # {
    #     'heonbeob': [
    #         {
    #             'no': 10,
    #             'ans': 1,
    #         },
    #         ...
    #     ]
    # }
    subject_fields = exam_vars['subject_fields']
    problem_count = exam_vars['problem_count']
    official_answer_uploaded = False

    data_answer_official = get_empty_data_answer(fields=subject_fields, problem_count=problem_count)
    if exam and exam.is_answer_official_opened:
        official_answer_uploaded = True
        try:
            for field, answer in exam.answer_official.items():
                field_idx = subject_fields.index(field)
                for no, ans in enumerate(answer, start=1):
                    data_answer_official[field_idx][no - 1] = {'no': no, 'ans': ans, 'field': field}
        except IndexError:
            official_answer_uploaded = False
        except KeyError:
            official_answer_uploaded = False
    return data_answer_official, official_answer_uploaded


def get_data_answer_predict(exam_vars: dict, qs_answer_count) -> list:
    subject_fields = exam_vars['subject_fields']
    problem_count = exam_vars['problem_count']
    count_fields = exam_vars['count_fields']
    data_answer_predict = get_empty_data_answer(fields=subject_fields, problem_count=problem_count)
    for answer_count in qs_answer_count:
        field = answer_count.subject
        field_idx = subject_fields.index(field)
        no = answer_count.number

        count_list = [getattr(answer_count, c) for c in count_fields]
        ans_predict = count_list[1:].index(max(count_list[1:])) + 1
        rate_accuracy = round(getattr(answer_count, f'rate_{ans_predict}'), 1)

        count_list.extend([answer_count.count_multiple, answer_count.count_total])

        data_answer_predict[field_idx][no - 1].update({
            'no': no, 'ans': ans_predict, 'field': field,
            'rate_accuracy': rate_accuracy, 'count': count_list,
        })

    return data_answer_predict


def get_data_answer_student(
        exam_vars: dict, student,
        data_answer_official: list[list[dict]],
        official_answer_uploaded: bool,
        data_answer_predict: list[list[dict]],
) -> list:
    subject_fields = exam_vars['subject_fields']
    problem_count = exam_vars['problem_count']
    data_answer_student = get_empty_data_answer(
        fields=subject_fields, problem_count=problem_count)

    for field_idx, value in enumerate(data_answer_predict):
        field = subject_fields[field_idx]
        if student.answer_confirmed[field]:
            for idx, answer_predict in enumerate(value):
                ans_student = student.answer[field][idx]
                ans_predict = answer_predict['ans']
                count_total = answer_predict['count'][-1]
                rate_selection = 0
                if count_total:
                    rate_selection = round(answer_predict['count'][ans_student] * 100 / count_total, 1)

                prediction_is_correct = result = None
                if official_answer_uploaded:
                    ans_official = data_answer_official[field_idx][idx]['ans']
                    prediction_is_correct = ans_official == ans_predict
                    answer_predict['prediction_is_correct'] = ans_official == ans_predict
                    if 1 <= ans_official <= 5:
                        result = ans_student == ans_official
                        rate_correct = round(answer_predict['count'][ans_official] * 100 / count_total, 1)
                    else:
                        ans_official_list = [int(ans) for ans in str(ans_official)]
                        result = ans_student in ans_official_list
                        rate_correct = round(sum(
                            answer_predict['count'][ans] for ans in ans_official_list) * 100 / count_total, 1)
                    data_answer_official[field_idx][idx]['rate_correct'] = rate_correct

                answer_predict['prediction_is_correct'] = prediction_is_correct
                data_answer_student[field_idx][idx].update({
                    'no': idx + 1,
                    'ans': ans_student,
                    'rate_selection': rate_selection,
                    'result_real': result,
                })
    return data_answer_student


def get_info_answer_student(
        exam_vars: dict, student, exam,
        data_answer_student: list[list[dict]],
        data_answer_predict: list[list[dict]],
) -> list:
    score_fields = exam_vars['score_fields']
    info_answer_student: list[dict] = [{} for _ in score_fields]

    psat_score_predict = 0
    psat_fields = ['eoneo', 'jaryo', 'sanghwang']
    participants = exam.participants['all']['total']

    for field in score_fields:
        field_idx = score_fields.index(field)
        sub, subject = exam_vars['field_vars'][field]
        is_confirmed = student.answer_confirmed[field]
        score_real = student.score[field]

        if field != 'psat_avg':
            correct_predict_count = 0
            for idx, answer_student in enumerate(data_answer_student[field_idx]):
                ans_student = answer_student['ans']
                ans_predict = data_answer_predict[field_idx][idx]['ans']

                result_predict = ans_student == ans_predict
                answer_student['result_predict'] = result_predict
                correct_predict_count += 1 if result_predict else 0

            problem_count = exam_vars['problem_count'][field]
            answer_count = student.answer_count[field]
            score_predict = correct_predict_count * 100 / problem_count
            psat_score_predict += score_predict if field in psat_fields else 0
        else:
            problem_count = sum([val for val in exam_vars['problem_count'].values()])
            answer_count = sum([val for val in student.answer_count.values()])
            score_predict = psat_score_predict / 3

        info_answer_student[field_idx].update({
            'icon': icon_set_new.ICON_SUBJECT[sub],
            'sub': sub, 'subject': subject, 'field': field,
            'is_confirmed': is_confirmed,
            'participants': participants[field],
            'score_real': score_real, 'score_predict': score_predict,
            'problem_count': problem_count, 'answer_count': answer_count,
        })
    return info_answer_student


def get_dict_stat_data(
        exam_vars: dict, student, stat_type: str,
        exam, qs_student, filtered: bool = False
) -> list:
    score_fields = exam_vars['score_fields']
    field_vars = exam_vars['field_vars']
    score_list = {field: [] for field in field_vars.keys()}
    stat_data = [
        {
            'field': field, 'sub': subject_tuple[0], 'subject': subject_tuple[1],
            'icon': icon_set_new.ICON_SUBJECT[subject_tuple[0]],
            'is_confirmed': student.answer_confirmed[field],
            'rank': 0, 'score': 0, 'participants': 0,
            'max_score': 0, 'top_score_10': 0,
            'top_score_20': 0, 'avg_score': 0,
        } for field, subject_tuple in field_vars.items()
    ]

    filter_exp = {}
    if stat_type == 'department':
        filter_exp['department'] = student.department
    if filtered:
        filter_exp['answer_all_confirmed_at__lte'] = exam.answer_official_opened_at
    qs_student = qs_student.filter(**filter_exp)

    for field, subject_tuple in field_vars.items():
        field_idx = score_fields.index(field)

        for stu in qs_student:
            if stu.answer_confirmed[field]:
                score_list[field].append(stu.score[field])

        if score_list[field]:
            participants = len(score_list[field])
            sorted_scores = sorted(score_list[field], reverse=True)

            student_score = student.score[field]
            rank = sorted_scores.index(student_score) + 1
            top_10_threshold = max(1, int(participants * 0.1))
            top_20_threshold = max(1, int(participants * 0.2))

            stat_data[field_idx].update({
                'rank': rank, 'score': round(student_score, 1), 'participants': participants,
                'max_score': round(sorted_scores[0], 1),
                'top_score_10': round(sorted_scores[top_10_threshold - 1], 1),
                'top_score_20': round(sorted_scores[top_20_threshold - 1], 1),
                'avg_score': round(sum(score_list[field]) / participants if participants else 0, 1),
            })
    return stat_data


def update_rank(
        student,
        stat_total_all: list,
        stat_department_all: list,
        stat_total_filtered: list,
        stat_department_filtered: list,
):
    rank = {
        'all': {
            'total': {stat['field']: stat['rank'] for stat in stat_total_all},
            'department': {stat['field']: stat['rank'] for stat in stat_department_all},
        },
        'filtered': {
            'total': {stat['field']: stat['rank'] for stat in stat_total_filtered},
            'department': {stat['field']: stat['rank'] for stat in stat_department_filtered},
        },
    }
    if student.rank != rank:
        student.rank = rank
        student.save()


def create_student_instance(exam_vars: dict, student, request):
    problem_count = exam_vars['problem_count']
    score_fields = exam_vars['score_fields']
    with transaction.atomic():
        student.user = request.user
        student.year = exam_vars['year']
        student.exam = exam_vars['exam']
        student.round = exam_vars['round']
        student.answer = {
            field: [0 for _ in range(count)] for field, count in problem_count.items()
        }
        student.answer_count = {field: 0 for field in score_fields}
        student.answer_confirmed = {field: False for field in score_fields}
        student.score = {field: 0 for field in score_fields}
        student.rank = {
            'all': {
                'total': {field: 0 for field in score_fields},
                'department': {field: 0 for field in score_fields},
            },
            'filtered': {
                'total': {field: 0 for field in score_fields},
                'department': {field: 0 for field in score_fields},
            },
        }
        student.save()


def save_submitted_answer(student, subject_field: str, no: int, ans: int):
    idx = no - 1
    with transaction.atomic():
        student.answer[subject_field][idx] = ans
        student.save()
        student.refresh_from_db()
    return {'no': no, 'ans': student.answer[subject_field][idx]}


def confirm_answer_student(exam_vars: dict, student, subject_field: str) -> tuple:
    problem_count = exam_vars['problem_count']
    answer_student = student.answer[subject_field]
    is_confirmed = all(answer_student) and len(answer_student) == problem_count[subject_field]
    if is_confirmed:
        student.answer_confirmed[subject_field] = is_confirmed
        student.save()
    student.refresh_from_db()
    return student, is_confirmed


def update_answer_count(student, subject_field: str, qs_answer_count):
    for answer_count in qs_answer_count:
        idx = answer_count.number - 1
        ans_student = student.answer[subject_field][idx]
        setattr(answer_count, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
        setattr(answer_count, f'count_total', F(f'count_total') + 1)
        answer_count.save()


def get_next_url(exam_vars: dict, student) -> str:
    for field in exam_vars['subject_fields']:
        is_confirmed = student.answer_confirmed[field]
        if not is_confirmed:
            return reverse('predict:answer-input', args=[field])
    return reverse('predict:index')


def get_page_obj_and_range(page_data, per_page=10, page_number=1):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_sub_title(exam):
    if exam.exam == '프모':
        return f'제{exam.round}회 {exam.get_exam_display} 성적 예측'
    return f'{exam.year}년 {exam.get_exam_display} 성적 예측'


def get_dict_by_sub(target_list: list[dict]) -> dict:
    result_dict = {'헌법': [], '언어': [], '자료': [], '상황': []}
    for key in result_dict.keys():
        result_list = []
        for t in target_list:
            if t and t['sub'] == key:
                result_list.append(t)
        result_dict[key] = result_list
    return result_dict


def get_rank_qs(queryset):
    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    def rank_ratio_func(field_name) -> Window:
        return Window(expression=PercentRank(), order_by=F(field_name).desc())

    return queryset.annotate(
        user_id=F('student__user_id'),

        rank_heonbeob=rank_func('score_heonbeob'),
        rank_eoneo=rank_func('score_eoneo'),
        rank_jaryo=rank_func('score_jaryo'),
        rank_sanghwang=rank_func('score_sanghwang'),
        rank_psat=rank_func('score_psat_avg'),

        rank_ratio_heonbeob=rank_ratio_func('score_heonbeob'),
        rank_ratio_eoneo=rank_ratio_func('score_eoneo'),
        rank_ratio_jaryo=rank_ratio_func('score_jaryo'),
        rank_ratio_sanghwang=rank_ratio_func('score_sanghwang'),
        rank_ratio_psat=rank_ratio_func('score_psat_avg'),
    )


def get_all_ranks_dict(get_students_qs, user_id) -> dict:
    rank_total = rank_department = None

    students_qs_total = get_students_qs('전체')
    rank_qs_total = get_rank_qs(students_qs_total).values()
    for qs in rank_qs_total:
        if qs['user_id'] == user_id:
            rank_total = qs

    students_qs_department = get_students_qs('직렬')
    rank_qs_department = get_rank_qs(students_qs_department).values()
    for qs in rank_qs_department:
        if qs['user_id'] == user_id:
            rank_department = qs

    return {
        '전체': rank_total,
        '직렬': rank_department,
    }


def get_top_score(score_list: list):
    try:
        return np.percentile(score_list, [90, 80], interpolation='nearest')
    except IndexError:
        return [0, 0]
    except TypeError:
        return [0, 0]


def get_score_stat_korean(queryset) -> dict:
    stat_queryset = queryset.aggregate(
        응시_인원=Count('id'),

        헌법_최고_점수=Max('score_heonbeob', default=0),
        언어_최고_점수=Max('score_eoneo', default=0),
        자료_최고_점수=Max('score_jaryo', default=0),
        상황_최고_점수=Max('score_sanghwang', default=0),
        PSAT_최고_점수=Max('score_psat_avg', default=0),

        헌법_평균_점수=Avg('score_heonbeob', default=0),
        언어_평균_점수=Avg('score_eoneo', default=0),
        자료_평균_점수=Avg('score_jaryo', default=0),
        상황_평균_점수=Avg('score_sanghwang', default=0),
        PSAT_평균_점수=Avg('score_psat_avg', default=0),
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    try:
        stat_queryset['헌법_상위_10%'] = top_score_heonbeob[0]
        stat_queryset['헌법_상위_20%'] = top_score_heonbeob[1]

        stat_queryset['언어_상위_10%'] = top_score_eoneo[0]
        stat_queryset['언어_상위_20%'] = top_score_eoneo[1]

        stat_queryset['자료_상위_10%'] = top_score_jaryo[0]
        stat_queryset['자료_상위_20%'] = top_score_jaryo[1]

        stat_queryset['상황_상위_10%'] = top_score_sanghwang[0]
        stat_queryset['상황_상위_20%'] = top_score_sanghwang[1]

        stat_queryset['PSAT_상위_10%'] = top_score_psat_avg[0]
        stat_queryset['PSAT_상위_20%'] = top_score_psat_avg[1]
    except TypeError:
        pass

    return stat_queryset


def get_score_stat_sub(queryset) -> dict:
    score_stat_sub = {
        '헌법': {'sub': 'heonbeob'},
        '언어': {'sub': 'eoneo'},
        '자료': {'sub': 'jaryo'},
        '상황': {'sub': 'sanghwang'},
        '피셋': {'sub': 'psat'},
    }
    for key, item in score_stat_sub.items():
        item['num_students'] = None
        item['max_score'] = None
        item['avg_score'] = None
        item['top_score_10'] = None
        item['top_score_20'] = None
    stat_queryset = queryset.aggregate(
        num_students=Count('id'),

        max_score_heonbeob=Max('score_heonbeob', default=0),
        max_score_eoneo=Max('score_eoneo', default=0),
        max_score_jaryo=Max('score_jaryo', default=0),
        max_score_sanghwang=Max('score_sanghwang', default=0),
        max_score_psat_avg=Max('score_psat_avg', default=0),

        avg_score_heonbeob=Avg('score_heonbeob', default=0),
        avg_score_eoneo=Avg('score_eoneo', default=0),
        avg_score_jaryo=Avg('score_jaryo', default=0),
        avg_score_sanghwang=Avg('score_sanghwang', default=0),
        avg_score_psat_avg=Avg('score_psat_avg', default=0),
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = []
    score_list_eoneo = []
    score_list_jaryo = []
    score_list_sanghwang = []
    score_psat_avg = []
    for s in score_list_all:
        if s['score_heonbeob']:
            score_list_heonbeob.append(s['score_heonbeob'])
        if s['score_eoneo']:
            score_list_eoneo.append(s['score_eoneo'])
        if s['score_jaryo']:
            score_list_jaryo.append(s['score_jaryo'])
        if s['score_sanghwang']:
            score_list_sanghwang.append(s['score_sanghwang'])
        if s['score_psat_avg']:
            score_psat_avg.append(s['score_psat_avg'])
    # score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    # score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    # score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    # score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    # score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    for key, data in score_stat_sub.items():
        sub = data['sub']
        data['num_students'] = stat_queryset[f'num_students']
        if sub == 'psat':
            data['max_score'] = stat_queryset[f'max_score_psat_avg']
            data['avg_score'] = stat_queryset[f'avg_score_psat_avg']
        else:
            data['max_score'] = stat_queryset[f'max_score_{sub}']
            data['avg_score'] = stat_queryset[f'avg_score_{sub}']

    score_stat_sub['헌법']['top_score_10'] = top_score_heonbeob[0]
    score_stat_sub['헌법']['top_score_20'] = top_score_heonbeob[1]

    score_stat_sub['언어']['top_score_10'] = top_score_eoneo[0]
    score_stat_sub['언어']['top_score_20'] = top_score_eoneo[1]

    score_stat_sub['자료']['top_score_10'] = top_score_jaryo[0]
    score_stat_sub['자료']['top_score_20'] = top_score_jaryo[1]

    score_stat_sub['상황']['top_score_10'] = top_score_sanghwang[0]
    score_stat_sub['상황']['top_score_20'] = top_score_sanghwang[1]

    score_stat_sub['피셋']['top_score_10'] = top_score_psat_avg[0]
    score_stat_sub['피셋']['top_score_20'] = top_score_psat_avg[1]

    return score_stat_sub


def get_all_score_stat_sub_dict(get_statistics_qs, student) -> dict:
    stat_total = stat_department = None

    if student:
        stat_total = get_score_stat_sub(get_statistics_qs('전체'))
        stat_department = get_score_stat_sub(get_statistics_qs('직렬'))

    return {
        '전체': stat_total,
        '직렬': stat_department,
    }
