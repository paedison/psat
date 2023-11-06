import random

from django.core.management.base import BaseCommand

from score import models as score_models


class Command(BaseCommand):
    help = 'Create Dummy Students'

    def add_arguments(self, parser):
        parser.add_argument('dummy_count', type=int, help='Number of dummy students')
        parser.add_argument('exam_year', type=str, help='Exam Year')

    def handle(self, *args, **kwargs):
        dummy_count = kwargs['dummy_count']
        exam_year = kwargs['exam_year']

        dummy_base = 100_000_000
        student_count = score_models.PsatStudent.objects.filter(
            user_id__gt=dummy_base).distinct().values_list('user_id').count()

        dummy_students = []
        dummy_start_num = dummy_base + student_count + 1
        dummy_end_num = dummy_base + student_count + dummy_count + 1

        haengsi_ilhaeng_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='5급공채 행정(전국모집)', name='일반행정').id
        haengsi_jaegyong_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='5급공채 행정(전국모집)', name='재경').id

        ipsi_ilhaeng_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='입법고시', name='일반행정').id
        ipsi_jaegyong_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='입법고시', name='재경').id

        chilgeup_ilhaeng_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='7급공채 국가직(일반)', name='일반행정').id
        chilgeup_jaegyong_id = score_models.PsatUnitDepartment.objects.get(
            unit__name='7급공채 국가직(일반)', name='재경').id

        for i in range(dummy_start_num, dummy_end_num):
            if i < dummy_count / 2:
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=haengsi_ilhaeng_id,
                    serial=random.randint(100000, 999999)))
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=ipsi_ilhaeng_id,
                    serial=random.randint(100000, 999999)))
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=chilgeup_ilhaeng_id,
                    serial=random.randint(100000, 999999)))
            else:
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=haengsi_jaegyong_id,
                    serial=random.randint(100000, 999999)))
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=ipsi_jaegyong_id,
                    serial=random.randint(100000, 999999)))
                dummy_students.append(score_models.PsatStudent(
                    user_id=i, year=exam_year, department_id=chilgeup_jaegyong_id,
                    serial=random.randint(100000, 999999)))
        score_models.PsatStudent.objects.bulk_create(dummy_students)
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(dummy_students)} dummy students'))
