from pprint import pprint

from django.db.models import Count, F

from a_predict.models import Student, StudentAnswer, SubmittedAnswer, AnswerCount
from a_predict.views.base_info import ExamInfo


def run():
    problem_count = {'헌법': 25, '언어': 40, '자료': 40, '상황': 40}

    total_count_empty = {}
    for key, value in problem_count.items():
        total_count_empty[key] = []
        for i in range(1, value + 1):
            total_count_empty[key].append(
                {
                    'year': 2024, 'exam': '', 'round': 0, 'subject': key, 'number': i, 'answer': 0,
                    'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0, 'count_None': 0,
                },
            )

    exam_list = Student.objects.values('exam', 'round').distinct()
    for e in exam_list[1:]:
        total_count = total_count_empty.copy()
        create_list = []
        for key in problem_count.keys():
            exam = e['exam']
            exam_round = e['round']
            submitted_answer_count = (
                SubmittedAnswer.objects
                .filter(student__year=2024, student__exam=exam, student__round=exam_round, subject=key)
                .values('subject', 'number', 'answer')
                .annotate(count=Count('answer'), year=F('student__year'), exam=F('student__exam'), round=F('student__round'))
                .order_by('subject', 'number', 'answer')
            )

            for answer_count in submitted_answer_count:
                answer_count: dict

                subject = answer_count['subject']
                number = answer_count['number']
                ans_number = answer_count['answer']
                count = answer_count['count']

                total_count[subject][number - 1][f'count_{ans_number}'] = count
                total_count[subject][number - 1]['exam'] = exam
                total_count[subject][number - 1]['round'] = exam_round

        for key in problem_count.keys():
            for c in total_count[key]:
                create_list.append(AnswerCount(**c))
        # pprint(create_list)
        AnswerCount.objects.bulk_create(create_list)
    # for e in exam_list:
    #     total_count = total_count_empty.copy()
    #     for key in problem_count.keys():
    #         submitted_answer_count = SubmittedAnswer.objects.filter(
    #             student__year=2024,
    #             student__exam=e['exam'],
    #             student__round=e['round'],
    #             subject=key,
    #         ).values('subject', 'number', 'answer').annotate(count=Count('answer')).order_by('subject', 'number', 'answer')
    #
    # total_count = {'헌법': []}
    # for i in range(1, 26):
    #     total_count['헌법'].append(
    #         {'number': i, 'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0, 'count_None': 0},
    #     )
    #
    # for answer_count in submitted_answer_count:
    #     answer_count: dict
    #     subject = answer_count['subject']
    #     number = answer_count['number']
    #     answer = answer_count['answer']
    #     count = answer_count['count']
    #
    #     total_count[subject][number - 1][f'count_{answer}'] = count
    #
    # pprint(total_count_empty)
    # students = Student.objects.all()
    # subject_list = {
    #     '헌법': 'heonbeob',
    #     '언어': 'eoneo',
    #     '자료': 'jaryo',
    #     '상황': 'sanghwang',
    # }
    # for student in students:
    #     student_answer, created = StudentAnswer.objects.get_or_create(student=student)
    #
    #     for subject, field in subject_list.items():
    #         problem_count = 40
    #         if student.exam == '칠급' or subject == '헌법':
    #             problem_count = 25
    #
    #         submitted_answers = SubmittedAnswer.objects.filter(
    #             student=student, subject=subject
    #         ).order_by('number').values('number', 'answer')
    #
    #         answer_count = submitted_answers.count()
    #         if answer_count == problem_count:
    #             answer_list = [''] * problem_count
    #             for ans in submitted_answers:
    #                 index = ans['number'] - 1
    #                 answer_list[index] = str(ans['answer'])
    #             answer_string = ','.join(answer_list)
    #         else:
    #             answer_string = ''
    #         setattr(student_answer, field, answer_string)
    #         student_answer.save(message_type=field)
