import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

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
        create_list = []
        update_count = 0
        create_count = 0

        category_model = reference_models.Prime
        problem_model = reference_models.PrimeProblem
        student_model = score_models.PrimeStudent
        statistics_model = score_models.PrimeStatistics
        answer_model = score_models.PrimeAnswer
        statistics_model_name = 'PrimeStatistics'

        score_keys = [
            'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat', 'score_psat_avg', 'score_heonbeob',
        ]

        def get_score_subject(student: any, sub: str):
            prime_id = category_model.objects.get(year=exam_year, round=exam_round, subject__abbr=sub).id
            problem_answers = list(
                problem_model.objects.filter(prime_id=prime_id).values_list('answer', flat=True)
            )
            student_answers = answer_model.objects.get(prime_id=prime_id, student=student)
            correct_count = 0
            problem_number = 25 if sub == '헌법' else 40
            for i in range(0, problem_number):
                answer_correct = problem_answers[i]
                answer_student = getattr(student_answers, f'prob{i + 1}')
                if answer_correct <= 5 and answer_correct == answer_student:
                    correct_count += 1
                if answer_correct > 5:
                    answer_correct_list = [int(digit) for digit in str(problem_answers)]
                    if answer_student in answer_correct_list:
                        correct_count += 1

            score_subject = correct_count * 100 / problem_number
            return score_subject

        def get_score(student):
            score_eoneo = get_score_subject(student, '언어')
            score_jaryo = get_score_subject(student, '자료')
            score_sanghwang = get_score_subject(student, '상황')
            score_psat = score_eoneo + score_jaryo + score_sanghwang
            score_psat_avg = score_psat / 3
            score_heonbeob = get_score_subject(student, '헌법')
            return {
                'score_eoneo': score_eoneo,
                'score_jaryo': score_jaryo,
                'score_sanghwang': score_sanghwang,
                'score_psat': score_psat,
                'score_psat_avg': score_psat_avg,
                'score_heonbeob': score_heonbeob,
            }

        students = student_model.objects.filter(year=exam_year, round=exam_round)
        for stu in students:
            score = get_score(stu)
            try:
                stat = statistics_model.objects.get(student=stu)
                fields_not_match = any(
                    str(getattr(stat, key)) != score[key] for key in score_keys
                )
                if fields_not_match:
                    for field, value in score.items():
                        setattr(stu.statistics, field, value)
                    update_list.append(stat)
                    update_count += 1
            except statistics_model.DoesNotExist:
                score['student_id'] = stu.id
                create_list.append(statistics_model(**score))
                create_count += 1

        try:
            with transaction.atomic():
                if create_list:
                    statistics_model.objects.bulk_create(create_list)
                    message = f'Successfully {create_count} {statistics_model_name} instances created.'
                elif update_list:
                    statistics_model.objects.bulk_update(update_list, score_keys)
                    message = f'Successfully {update_count} {statistics_model_name} instances updated.'
                else:
                    message = f'{statistics_model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
