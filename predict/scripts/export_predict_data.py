import csv

from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from predict import models as predict_models
from reference import models as reference_models


def write_csv(filename, fieldnames, rows):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csv_file:
        csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in rows:
            csvwriter.writerow(row)
    print(f'Successfully written in f{filename}')


def run():
    student_fields = [
        'id',
        'created_at',
        'remarks',
        'year',
        'exam_name',
        'round',
        'name',
        'serial',
        'unit',
        'department',
        'password',
        'prime_id',
        'user_id',
    ]
    students = predict_models.Student.objects.values(
        'id',
        'name',
        'serial',
        'password',
        'prime_id',
        'user_id',
        'unit_id',
        'department_id',
        created_at=F('timestamp'),
        remarks=Concat(Value('updated_at:'), F('updated_at'), output_field=CharField()),
        year=F('exam__year'),
        exam_name=F('exam__ex'),
        round=F('exam__round'),
    )

    for s in students:
        s: dict
        unit_id = s.pop('unit_id')
        department_id = s.pop('department_id')
        s['unit'] = reference_models.Unit.objects.get(id=unit_id).name
        s['department'] = reference_models.UnitDepartment.objects.get(id=department_id).name

    filename1 = 'predict/scripts/predict_student.csv'
    write_csv(filename1, student_fields, students)

    answer_fields = [
        'id',
        'subject',
        'number',
        'answer',
        'student_id'
    ]

    answers = predict_models.Answer.objects.values()
    answer_data = []
    answer_id = 1
    for answer in answers:
        answer: dict
        for i in range(1, 41):
            answer_prob = answer[f'prob{i}']
            if answer_prob is not None:
                answer_data.append({
                    'id': answer_id,
                    'subject': answer['sub'],
                    'number': i,
                    'answer': answer_prob,
                    'student_id': answer['student_id'],
                })
                answer_id += 1

    filename2 = 'predict/scripts/predict_submitted_answers.csv'
    write_csv(filename2, answer_fields, answer_data)

# elds = [
#         'id',
#         'created_at',
#         'remarks',
#         'sub',
#         'is_confirmed',
#         'student_id'
#     ]
#
#     sub_fields = {
#         '헌법': 'heonbeob',
#         '언어': 'eoneo',
#         '자료': 'jaryo',
#         '상황': 'sanghwang',
#     }
#
#     answers = predict_models.Answer.objects.values(
#         'id',
#         'sub',
#         'is_confirmed',
#         'student_id',
#         exam=F('student__exam__ex'),
#         created_at=F('timestamp'),
#         remarks=Concat(Value('updated_at:'), F('updated_at'), output_field=CharField()),
#     )
#     for answer in answers:
#         answer: dict
#
#         sub_field = sub_fields[answer['sub']]
#
#         all_answer_count = 40
#         exam = answer.pop('exam')
#         if exam == '헌법' or
#
#         answer_string = ''
#         for i in range(2, 41):
#             answer_prob = answer.pop(f'prob{i}')
#             answer_prob = answer_prob or ''
#             if i != 1:
#                 answer_prob = f'|{answer_prob}'
#             answer_string += answer_prob
#         answer[sub_field] = answer_string
#
#     filename2 = 'predict/scripts/predict_submitted_answers.csv'
#
#     with open(filename2, 'w', newline='', encoding='utf-8-sig') as csv_file:
#         csvwriter = csv.DictWriter(csv_file, fieldnames=answer_fields)
#         csvwriter.writeheader()
#         for row in students:
#             csvwriter.writerow(row)
