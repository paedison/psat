import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import (
    PrimePsatExam, PrimePsatStudent,
    PrimePoliceExam, PrimePoliceStudent
)


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Prime Exam type')  # psat, police
        parser.add_argument('year', type=str, help='Year')  # 2024
        parser.add_argument('round', type=str, help='Round')  # 1

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        exam_model_dict = {
            'psat': PrimePsatExam,
            'police': PrimePoliceExam,
        }
        student_model_dict = {
            'psat': PrimePsatStudent,
            'police': PrimePoliceStudent,
        }
        exam_model = exam_model_dict[exam_type]
        student_model = student_model_dict[exam_type]

        update_list = []
        update_count = 0

        qs_student = student_model.objects.filter(year=exam_year, round=exam_round)
        answer_official = exam_model.objects.get(year=exam_year, round=exam_round).answer_official
        for student in qs_student:
            answer_student: dict = student.answer
            score = {}
            for field, value in answer_student.items():
                score_per_problem = 2.5
                if exam_type == 'psat' and field in ['heonbeob']:
                    score_per_problem = 4.0
                if exam_type == 'police':
                    score_dict = {
                        'hyeongsa': 3, 'gyeongchal': 3,
                        'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
                        'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
                    }
                    score_per_problem = score_dict[field] if field in score_dict.keys() else 1.5

                correct_count = 0
                for index, answer in enumerate(value):
                    if answer == answer_official[field][index]:
                        correct_count += 1
                score[field] = correct_count * score_per_problem

            if exam_type == 'psat':
                psat_fields = ['eoneo', 'jaryo', 'sanghwang']
                sum_list = [score[field] for field in psat_fields if field in score.keys()]
                score['psat_avg'] = sum(sum_list) / 3
            elif exam_type == 'police':
                score['sum'] = sum(s for s in score.values())
                score['avg'] = score['sum'] / 5

            if student.score != score:
                student.score = score
                update_list.append(student)
                update_count += 1

        try:
            with transaction.atomic():
                model_name = student_model._meta.model_name
                if update_list:
                    student_model.objects.bulk_update(update_list, ['score'])
                    message = f'Successfully {update_count} {model_name} instances updated.'
                else:
                    message = f'{model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
