from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import When, Value, CharField, F, Case

from reference import models as reference_models
from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Scores'

    def handle(self, *args, **kwargs):
        dummy_base = 100_000_000
        students = (
            score_models.PsatStudent.objects.filter(user_id__gt=dummy_base)
            .select_related('department__unit__exam')
        )
        update_list = []
        update_count = 0
        field_dict = {
            'PSAT': 'psat_score',
            '헌법': 'heonbeob_score',
            '언어': 'eoneo_score',
            '자료': 'jaryo_score',
            '상황': 'sanghwang_score',
        }

        for student in students:
            def get_score(sub: str) -> float:
                answers = (
                    score_models.PsatConfirmedAnswer.objects
                    .filter(
                        user_id=student.user_id,
                        problem__psat__exam_id=student.department.unit.exam_id,
                        problem__psat__subject__abbr=sub)
                    .annotate(result=Case(
                        When(problem__answer=F('answer'), then=Value('O')),
                        default=Value('X'), output_field=CharField()))
                    .values('problem__number', 'problem__answer', 'answer', 'result')
                )
                if answers:
                    correct_count = 0
                    total_count = len(answers)
                    for ans in answers:
                        correct_count += 1 if ans['result'] == 'O' else 0
                    return (100 / total_count) * correct_count

            data = {}
            for key, value in field_dict.items():
                if key != 'PSAT':
                    data[value] = get_score(key)
            data['psat_score'] = data['eoneo_score'] + data['jaryo_score'] + data['sanghwang_score']
            for key, value in field_dict.items():
                setattr(student, value, data[value])

            update_list.append(student)
            update_count += 1
        with transaction.atomic():
            if update_count:
                score_models.PsatStudent.objects.bulk_update(update_list, field_dict.values())

        self.stdout.write(self.style.SUCCESS(f'Successfully created scores of {students.count()} students.'))
