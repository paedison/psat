from a_predict.models import Student, Statistics, OfficialAnswer

PROBLEM_COUNT = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}


def run():
    update_list = []
    qs_student = Student.objects.all()
    for student in qs_student:
        student_answer = student.student_answers
        official_answer = OfficialAnswer.objects.get(
            year=student.year, exam=student.exam, round=student.round)
        statistics, _ = Statistics.objects.get_or_create(student=student)

        score = {}
        for field in PROBLEM_COUNT.keys():
            if student_answer.answer_confirmed[field]:
                count = 0
                for i in range(PROBLEM_COUNT[field]):
                    if student_answer.answer[field][i] == official_answer.answer[field][i]:
                        count += 1
                score[field] = count * 100 / PROBLEM_COUNT[field]

        psat_fields = ['eoneo', 'jaryo', 'sanghwang']
        psat_confirmed = all([
            student_answer.answer_confirmed[field] for field in psat_fields
        ])
        if psat_confirmed:
            sum_list = [score[field] for field in psat_fields if field in score.keys()]
            score['psat_avg'] = sum(sum_list) / 3

        setattr(statistics, 'score', score)
        update_list.append(statistics)

    Statistics.objects.bulk_update(update_list, ['score'])
