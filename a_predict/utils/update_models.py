from django.db import transaction
from django.db.models import F

from a_predict.views.base_info import PsatExamVars, PoliceExamVars


def update_exam_participants(exam_vars: PsatExamVars | PoliceExamVars):
    exam = exam_vars.exam
    score_fields = exam_vars.score_fields
    department_dict = {department.name: department.id for department in exam_vars.qs_department}

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

    for student in exam_vars.qs_student:
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


def update_rank(exam_vars: PsatExamVars | PoliceExamVars, **stat):
    student = exam_vars.student
    rank = {
        'all': {
            'total': {s['field']: s['rank'] for s in stat['stat_total_all']},
            'department': {s['field']: s['rank'] for s in stat['stat_department_all']},
        },
        'filtered': {
            'total': {s['field']: s['rank'] for s in stat['stat_total_filtered']},
            'department': {s['field']: s['rank'] for s in stat['stat_department_filtered']},
        },
    }
    if student.rank != rank:
        student.rank = rank
        student.save()


def create_student_instance(request, exam_vars: PsatExamVars | PoliceExamVars, student):
    problem_count = exam_vars.problem_count
    score_fields = exam_vars.score_fields
    with transaction.atomic():
        student.user = request.user
        student.year = exam_vars.exam_year
        student.exam = exam_vars.exam_exam
        student.round = exam_vars.exam_round
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
    return student


def save_submitted_answer(student, subject_field: str, no: int, ans: int):
    idx = no - 1
    with transaction.atomic():
        student.answer[subject_field][idx] = ans
        student.save()
        student.refresh_from_db()
    return {'no': no, 'ans': student.answer[subject_field][idx]}


def confirm_answer_student(exam_vars, student, subject_field: str) -> tuple:
    problem_count = exam_vars.problem_count
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
