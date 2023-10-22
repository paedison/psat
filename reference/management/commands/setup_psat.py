import csv

import django.db.utils
from django.core.management.base import BaseCommand
from django.db.models import Count

from reference import models as referece_models


class Command(BaseCommand):
    help = 'Setup PSAT exams & problems'

    def handle(self, *args, **kwargs):
        category_psat, _ = referece_models.Category.objects.get_or_create(name='PSAT')

        exam = []
        subject = []
        psat_exam = []
        psat_problem = []

        with open('exam.csv', 'r', encoding='utf8') as file:
            csv_data = csv.reader(file)
            next(csv_data)
            exam_count = 0
            for row in csv_data:
                exam.append(
                    referece_models.Exam(
                        id=row[0],
                        category_id=row[1],
                        abbr=row[2],
                        label=row[3],
                        name=row[4],
                        remark=row[5],
                    )
                )
                exam_count += 1
            try:
                referece_models.Exam.objects.bulk_create(exam)
                self.stdout.write(self.style.SUCCESS(f'Successfully {exam_count} exam instances created.'))
            except django.db.utils.IntegrityError:
                self.stdout.write(self.style.SUCCESS(f'Exam instances already exist.'))


        with open('subject.csv', 'r', encoding='utf8') as file:
            csv_data = csv.reader(file)
            next(csv_data)
            subject_count = 0
            for row in csv_data:
                subject.append(
                    referece_models.Subject(
                        id=row[0],
                        category_id=row[1],
                        abbr=row[2],
                        name=row[3],
                    )
                )
                subject_count += 1
            try:
                referece_models.Subject.objects.bulk_create(subject)
                self.stdout.write(self.style.SUCCESS(f'Successfully {subject_count} subject instances created.'))
            except django.db.utils.IntegrityError:
                self.stdout.write(self.style.SUCCESS(f'Subject instances already exist.'))


        with open('psat_exam.csv', 'r', encoding='utf8') as file:
            csv_data = csv.reader(file)
            next(csv_data)
            psat_exam_count = 0
            for row in csv_data:
                psat_exam.append(
                    referece_models.PsatExam(
                        id=row[0],
                        year=row[1],
                        exam_id=row[2],
                        subject_id=row[3],
                    )
                )
                psat_exam_count += 1
            try:
                referece_models.PsatExam.objects.bulk_create(psat_exam)
                self.stdout.write(self.style.SUCCESS(f'Successfully {psat_exam_count} PSAT exam instances created.'))
            except django.db.utils.IntegrityError:
                self.stdout.write(self.style.SUCCESS(f'PSAT exam instances already exist.'))


        with open('psat_problem.csv', 'r', encoding='utf8') as file:
            csv_data = csv.reader(file)
            next(csv_data)
            psat_problem_count = 0
            for row in csv_data:
                psat_problem.append(
                    referece_models.PsatProblem(
                        id=row[0],
                        exam_id=row[1],
                        number=row[2],
                        answer=row[3],
                        question=row[4],
                        data=row[5],
                    )
                )
                psat_problem_count += 1
            try:
                referece_models.PsatProblem.objects.bulk_create(psat_problem)
                self.stdout.write(self.style.SUCCESS(f'Successfully {psat_problem_count} PSAT problem instances created.'))
            except django.db.utils.IntegrityError:
                self.stdout.write(self.style.SUCCESS(f'PSAT problem instances already exist.'))

