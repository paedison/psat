import csv

from django.db.models import F, Value

from score import models as score_models


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
        'exam',
        'round',
        'name',
        'serial',
        'unit',
        'department_name',
        'password',
    ]
    students = score_models.PrimeStudent.objects.values(
        'id',
        'year',
        'round',
        'name',
        'password',
        'serial',
        created_at=F('timestamp'),
        exam=Value('프모'),
        department_name=F('department__name'),
    )

    filename1 = 'score/scripts/score_prime_student.csv'
    write_csv(filename1, student_fields, students)

    answer_fields = [
        'id',
        'created_at',
        'remarks',
        'answer',
        'student_id',
    ]

    student_id_list = score_models.PrimeAnswer.objects.order_by(
        'student_id').values_list('student_id', flat=True).distinct()

    answer_data = []
    answer_id = 1
    for student_id in student_id_list:
        answer_student = score_models.PrimeAnswer.objects.filter(
            student_id=student_id).annotate(sub=F('prime__subject__abbr'))
        answer_dict = {}
        for answer in answer_student:
            answer_dict[answer.sub] = []
            for i in range(1, 41):
                if getattr(answer, f'prob{i}') is not None:
                    answer_dict[answer.sub].append({'no': i, 'ans': getattr(answer, f'prob{i}')})
        student_answer_data = {
            'id': answer_id,
            'answer': answer_dict,
            'student_id': student_id,
        }
        answer_data.append(student_answer_data)

    # answers = score_models.PrimeAnswer.objects.annotate(
    #     sub=F('prime__subject__abbr'),
    # )
    # first_answer = answers[0]
    # first_sub = first_answer.sub
    # answer_data = []
    #
    # previous_student_id = 1
    # previous_answer_dict = {first_sub: []}
    # for i in range(1, 41):
    #     if getattr(first_answer, f'prob{i}') is not None:
    #         previous_answer_dict[first_sub].append({'no': i, 'ans': getattr(first_answer, f'prob{i}')})
    #
    # answer_id = 1
    # for answer in answers[1:]:
    #     sub = answer.sub
    #     current_student_id = answer.student_id
    #     current_answer_dict = {sub: []}
    #     for i in range(1, 41):
    #         if getattr(answer, f'prob{i}') is not None:
    #             current_answer_dict[sub].append({'no': i, 'ans': getattr(answer, f'prob{i}')})
    #
    #     if current_student_id == previous_student_id:
    #         previous_answer_dict.update(current_answer_dict)
    #     else:
    #         answer_data.append(previous_answer_dict)
    #         previous_answer_dict = current_answer_dict.copy()
    #         previous_student_id = current_student_id
    #         answer_id += 1

    # print(answer_data)
    filename2 = 'score/scripts/score_prime_answer.csv'
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
