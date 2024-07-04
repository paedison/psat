import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import PrimePsatStudent, PrimePoliceStudent


def get_score_and_participants(student, queryset) -> tuple[dict, dict]:
    score = {}
    participants = {}
    rank = {}
    for field, value in student.score.items():
        score[field] = []
        for qs in queryset:
            if field in qs['score'].keys():
                score[field].append(qs['score'][field])
        participants[field] = len(score[field])
        if field in student.score.keys():
            sorted_score = sorted(score[field], reverse=True)
            rank[field] = sorted_score.index(student.score[field]) + 1
    return rank, participants


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Prime Exam type')
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        student_model_dict = {
            'psat': PrimePsatStudent,
            'police': PrimePoliceStudent,
        }
        student_model = student_model_dict[exam_type]

        update_list = []
        update_count = 0

        qs_student = student_model.objects.filter(year=exam_year, round=exam_round)
        qs_all_score_total = qs_student.values('score')
        for student in qs_student:
            qs_all_score_department = qs_student.filter(department=student.department).values('score')

            rank_total, participants_total = get_score_and_participants(
                student=student, queryset=qs_all_score_total)
            rank_department, participants_department = get_score_and_participants(
                student=student, queryset=qs_all_score_department)

            fields_not_match = [
                student.rank_total != rank_total,
                student.participants_total != participants_total,
                student.rank_department != rank_department,
                student.participants_department != participants_department,
            ]
            if any(fields_not_match):
                student.rank_total = rank_total
                student.participants_total = participants_total
                student.rank_department = rank_department
                student.participants_department = participants_department
                update_list.append(student)
                update_count += 1

        try:
            with transaction.atomic():
                model_name = student_model._meta.model_name
                if update_list:
                    student_model.objects.bulk_update(
                        update_list,
                        ['rank_total', 'participants_total', 'rank_department', 'participants_department']
                    )
                    message = f'Successfully {update_count} {model_name} instances updated.'
                else:
                    message = f'{model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
