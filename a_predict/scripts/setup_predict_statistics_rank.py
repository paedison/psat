from a_predict.models import Student, Statistics

PROBLEM_COUNT = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40, 'psat_avg': 145}


def get_score_and_participants(student: Student, queryset: list[dict]) -> tuple[dict, dict]:
    score = {}
    participants = {}
    rank = {}
    for field in PROBLEM_COUNT.keys():
        score[field] = []
        for qs in queryset:
            if field in qs['score'].keys():
                score[field].append(qs['score'][field])
        participants[field] = len(score[field])
        if field in student.statistics.score.keys():
            sorted_score = sorted(score[field], reverse=True)
            rank[field] = sorted_score.index(student.statistics.score[field]) + 1
    return rank, participants


def run():
    update_list = []
    qs_student = Student.objects.all()
    for student in qs_student:
        qs_all_score_total = Statistics.objects.filter(
            student__year=student.year,
            student__exam=student.exam,
            student__round=student.round,
        ).values('score')
        qs_all_score_department = Statistics.objects.filter(
            student__year=student.year,
            student__exam=student.exam,
            student__round=student.round,
            student__department=student.department,
        ).values('score')

        rank_total, participants_total = get_score_and_participants(
            student=student, queryset=qs_all_score_total)
        rank_department, participants_department = get_score_and_participants(
            student=student, queryset=qs_all_score_department)

        student.statistics.rank_total = rank_total
        student.statistics.rank_department = rank_department
        student.statistics.participants_total = participants_total
        student.statistics.participants_department = participants_department

        update_list.append(student.statistics)

    Statistics.objects.bulk_update(
        update_list,
        ['rank_total', 'rank_department', 'participants_total', 'participants_department']
    )
