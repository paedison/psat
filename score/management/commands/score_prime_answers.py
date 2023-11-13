import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from common.utils import add_update_list
from reference import models as reference_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        update_list = []
        update_count = 0

        category_model = reference_models.Prime
        problem_model = reference_models.PrimeProblem
        student_model = score_models.PrimeStudent
        answer_model = score_models.PrimeAnswer
        student_model_name = 'PrimeStudent'

        score_keys = ['eoneo_score', 'jaryo_score', 'sanghwang_score', 'psat_score', 'heonbeob_score']

        def get_subject_score(student: any, sub: str):
            prime_id = category_model.objects.get(
                year=exam_year, round=exam_round, subject__abbr=sub).id
            answers = list(
                problem_model.objects.filter(prime_id=prime_id).values_list('answer', flat=True)
            )
            student_answer = answer_model.objects.get(prime_id=prime_id, student=student)
            correct_count = 0
            problem_number = 25 if sub == '헌법' else 40
            for i in range(0, problem_number):
                if answers[i] == getattr(student_answer, f'prob{i + 1}'):
                    correct_count += 1
            subject_score = correct_count / problem_number * 100
            return subject_score

        def get_score(student):
            eoneo_score = get_subject_score(student, '언어')
            jaryo_score = get_subject_score(student, '자료')
            sanghwang_score = get_subject_score(student, '상황')
            heonbeob_score = get_subject_score(student, '헌법')
            psat_score = eoneo_score + jaryo_score + sanghwang_score
            score_dict = {
                'eoneo_score': eoneo_score,
                'jaryo_score': jaryo_score,
                'sanghwang_score': sanghwang_score,
                'psat_score': psat_score,
                'heonbeob_score': heonbeob_score,
            }
            return score_dict

        students = student_model.objects.filter(year=exam_year, round=exam_round)
        for stu in students:
            score = get_score(stu)
            update_list, update_count = add_update_list(
                student_model, update_list, update_count, stu.id, score_keys, score, index=0)

        try:
            with transaction.atomic():
                if update_list:
                    student_model.objects.bulk_update(update_list, score_keys)
                    message = f'Successfully {update_count} {student_model_name} instances updated.'
                else:
                    message = f'{student_model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
