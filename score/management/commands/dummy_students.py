import random

from django.core.management.base import BaseCommand

from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Students'

    def add_arguments(self, parser):
        parser.add_argument('num_users', type=int, help='Number of users')
        parser.add_argument('exam_year', type=str, help='Exam Year')

    def handle(self, *args, **kwargs):
        num_users = kwargs['num_users']
        exam_year = kwargs['exam_year']

        student_count = score_models.DummyStudent.objects.values_list(
            'user',flat=True).distinct().count()
        dummy_students = []
        for i in range(student_count + 1, student_count + num_users + 1):
            dummy_students.append(score_models.DummyStudent(
                user=i, year=exam_year, department_id=1,
                serial=random.randint(100000, 999999)))
            dummy_students.append(score_models.DummyStudent(
                user=i, year=exam_year, department_id=61,
                serial=random.randint(100000, 999999)))
            dummy_students.append(score_models.DummyStudent(
                user=i, year=exam_year, department_id=66,
                serial=random.randint(100000, 999999)))
        score_models.DummyStudent.objects.bulk_create(dummy_students)
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(dummy_students)} dummy students'))
