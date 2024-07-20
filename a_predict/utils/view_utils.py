from django.core.paginator import Paginator
from django.urls import reverse

from a_predict.views.base_info import PsatExamVars, PoliceExamVars
from common.constants import icon_set_new


def get_exam_vars(exam_year: int, exam_exam: str, exam_round: int):
    if exam_exam == '행시' or exam_exam == '칠급':
        return PsatExamVars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)
    elif exam_exam == '경위':
        return PoliceExamVars(exam_year=exam_year, exam_exam=exam_exam, exam_round=exam_round)


def get_answer_confirmed(exam_vars: PsatExamVars | PoliceExamVars):
    return [exam_vars.student.answer_confirmed[field] for field in exam_vars.score_fields]


def get_empty_data_answer(fields: list, problem_count: dict):
    return [
        [
            {'no': no, 'ans': 0, 'field': field} for no in range(1, problem_count[field] + 1)
         ] for field in fields
    ]


def get_data_answer_official(exam_vars: PsatExamVars | PoliceExamVars) -> tuple[list, bool]:
    # {
    #     'heonbeob': [
    #         {
    #             'no': 10,
    #             'ans': 1,
    #         },
    #         ...
    #     ]
    # }
    official_answer_uploaded = False
    exam = exam_vars.exam

    data_answer_official = exam_vars.get_empty_data_answer()
    if exam and exam.is_answer_official_opened:
        official_answer_uploaded = True
        try:
            for field, answer in exam.answer_official.items():
                field_idx = exam_vars.get_field_idx(field)
                for no, ans in enumerate(answer, start=1):
                    data_answer_official[field_idx][no - 1] = {'no': no, 'ans': ans, 'field': field}
        except IndexError:
            official_answer_uploaded = False
        except KeyError:
            official_answer_uploaded = False
    return data_answer_official, official_answer_uploaded


def get_data_answer_predict(exam_vars: PsatExamVars | PoliceExamVars) -> list:
    subject_fields = exam_vars.subject_fields
    problem_count = exam_vars.problem_count
    count_fields = exam_vars.count_fields
    data_answer_predict = get_empty_data_answer(fields=subject_fields, problem_count=problem_count)
    for answer_count in exam_vars.qs_answer_count:
        field = answer_count.subject
        if field in subject_fields:
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


def get_data_answer_student(exam_vars: PsatExamVars | PoliceExamVars) -> list:
    student = exam_vars.student
    subject_fields = exam_vars.subject_fields
    problem_count = exam_vars.problem_count
    data_answer_student = get_empty_data_answer(fields=subject_fields, problem_count=problem_count)
    data_answer_official = exam_vars.data_answer_official_tuple[0]
    official_answer_uploaded = data_answer_official[1]

    for field_idx, value in enumerate(exam_vars.data_answer_predict):
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


def get_info_answer_student(exam_vars: PsatExamVars | PoliceExamVars) -> list:
    is_not_police = exam_vars.exam_exam != '경위'
    student = exam_vars.student
    data_answer_student = exam_vars.data_answer_student
    data_answer_predict = exam_vars.data_answer_predict
    score_fields: list = exam_vars.score_fields
    subject_fields: list = exam_vars.subject_fields
    info_answer_student: list[dict] = [{} for _ in score_fields]

    score_predict_sum = 0
    participants = exam_vars.exam.participants['all']['total']

    for field in score_fields:
        field_idx = score_fields.index(field)
        sub, subject = exam_vars.field_vars[field]
        is_confirmed = student.answer_confirmed[field]
        score_real = student.score[field]
        answer_count = student.answer_count[field]

        if field != exam_vars.avg_field:
            correct_predict_count = 0
            for idx, answer_student in enumerate(data_answer_student[field_idx]):
                ans_student = answer_student['ans']
                ans_predict = data_answer_predict[field_idx][idx]['ans']

                result_predict = ans_student == ans_predict
                answer_student['result_predict'] = result_predict
                correct_predict_count += 1 if result_predict else 0

            problem_count = exam_vars.problem_count[field]
            score_predict = correct_predict_count * 100 / problem_count
            score_predict_sum += score_predict if field in exam_vars.sum_fields else 0
        else:
            problem_count = sum([val for val in exam_vars.problem_count.values()])
            score_predict = score_predict_sum / 3
        url_answer_input = exam_vars.url_answer_input[field_idx] if field in subject_fields else ''

        info_answer_student[field_idx].update({
            'icon': icon_set_new.ICON_SUBJECT[sub] if is_not_police else '',
            'sub': sub, 'subject': subject, 'field': field,
            'is_confirmed': is_confirmed,
            'participants': participants[field],
            'score_real': score_real, 'score_predict': score_predict,
            'problem_count': problem_count, 'answer_count': answer_count,
            'url_answer_input': url_answer_input,
        })
    return info_answer_student


def get_stat_data(
        exam_vars: PsatExamVars | PoliceExamVars,
        stat_type: str, filtered: bool = False
) -> list:
    student = exam_vars.student
    exam = exam_vars.exam
    score_fields = exam_vars.score_fields
    field_vars = exam_vars.field_vars
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
    qs_student = exam_vars.qs_student.filter(**filter_exp)

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


def get_next_url(exam_vars, student) -> str:
    for field in exam_vars.subject_fields:
        is_confirmed = student.answer_confirmed[field]
        if not is_confirmed:
            url_kwargs = exam_vars.exam_url_kwargs.copy()
            url_kwargs['subject_field'] = field
            return reverse('predict:answer-input', kwargs=url_kwargs)
    return reverse('predict:index')


def get_page_obj_and_range(page_data, page_number=1, per_page=10):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_dict_by_sub(target_list: list[dict]) -> dict:
    result_dict = {'헌법': [], '언어': [], '자료': [], '상황': []}
    for key in result_dict.keys():
        result_list = []
        for t in target_list:
            if t and t['sub'] == key:
                result_list.append(t)
        result_dict[key] = result_list
    return result_dict
