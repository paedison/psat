import random

from django.db.models import When, Value, CharField, F, Case, ExpressionWrapper, FloatField
from django.core.management.base import BaseCommand

from psat import models as psat_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Scores'

    def handle(self, *args, **kwargs):
        students = score_models.DummyStudent.objects.all()

        for student in students:
            def get_score(sub: str) -> float:
                exam_ids = psat_models.Exam.objects.filter(
                    year=student.year, ex=student.department.unit.ex).values_list('id', flat=True)
                reference = (
                    score_models.DummyAnswer.objects
                    .filter(student=student, problem__exam__id__in=exam_ids, problem__exam__sub=sub)
                    .annotate(result=Case(
                        When(problem__answer=F('answer'), then=Value('O')),
                        default=Value('X'), output_field=CharField()))
                    .values('problem__number', 'problem__answer', 'answer', 'result'))

                correct_count = 0
                total_count = len(reference)
                for ref in reference:
                    correct_count += 1 if ref['result'] == 'O' else 0
                return correct_count / total_count * 100

            eoneo_score = get_score('언어')
            jaryo_score = get_score('자료')
            sanghwang_score = get_score('상황')
            psat_score = eoneo_score + jaryo_score + sanghwang_score

            student.eoneo_score = eoneo_score
            student.jaryo_score = jaryo_score
            student.sanghwang_score = sanghwang_score
            student.psat_score = psat_score
            student.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully created scores of {students.count()} students.'))
