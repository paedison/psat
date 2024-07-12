import csv

from predict.models import Student, Answer, SubmittedAnswer


def write_csv(filename, fieldnames, rows):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csv_file:
        csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in rows:
            csvwriter.writerow(row)
    print(f'Successfully written in f{filename}')


def run():
    students = Student.objects.all()
    subject_list = {
        '헌법': 'heonbeob',
        '언어': 'eoneo',
        '자료': 'jaryo',
        '상황': 'sanghwang',
    }
    update_list = []

    for student in students:
        student_answer, created = StudentAnswer.objects.get_or_create(student=student)
        if student.exam == '칠급':
            subject_list.pop('헌법')

        answer = {}
        answer_count = {}
        answer_confirmed = {}
        for subject, field in subject_list.items():
            subject_problem_count = 40
            if student.exam == '칠급' or subject == '헌법':
                subject_problem_count = 25

            qs_submitted_answers = SubmittedAnswer.objects.filter(
                student=student, subject=subject).order_by('number')

            subject_answer_count = qs_submitted_answers.count()
            answer_count[field] = subject_answer_count
            answer_confirmed[field] = subject_problem_count == subject_answer_count

            answer[field] = []
            for i in range(1, subject_problem_count + 1):
                answer[field].append({'no': i, 'ans': 0})
            for qs in qs_submitted_answers:
                answer[field][qs.number - 1] = {
                    'no': qs.number,
                    'ans': qs.answer,
                }

        student_answer.heonbeob = ''
        student_answer.eoneo = ''
        student_answer.jaryo = ''
        student_answer.sanghwang = ''
        student_answer.answer = answer
        student_answer.answer_count = answer_count
        student_answer.answer_confirmed = answer_confirmed
        update_list.append(student_answer)

    StudentAnswer.objects.bulk_update(
        update_list, ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'answer', 'answer_count', 'answer_confirmed'])
