import csv

from django.core.management.base import BaseCommand

from .utils.db_setup import create_instance_get_messages
from score import models as score_models
from reference import models as reference_models


class Command(BaseCommand):
    help = 'Setup Prime answer'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Name of the target file')
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        file_name = kwargs['file_name']
        exam_year = kwargs['year']
        exam_round = kwargs['round']
        eoneo_id = reference_models.Prime.objects.get(
            year=exam_year, round=exam_round, subject__abbr='언어').id
        jaryo_id = reference_models.Prime.objects.get(
            year=exam_year, round=exam_round, subject__abbr='자료').id
        sanghwang_id = reference_models.Prime.objects.get(
            year=exam_year, round=exam_round, subject__abbr='상황').id
        heonbeob_id = reference_models.Prime.objects.get(
            year=exam_year, round=exam_round, subject__abbr='헌법').id

        with open(file_name, 'r', encoding='utf-8') as input_file:
            csv_data = csv.reader(input_file)
            key = next(csv_data)
            output_file = open('temporary.csv', 'w', newline='')
            wr = csv.writer(output_file)
            wr.writerow(
                ['id', 'prime_id', 'student_id'] + [f'prob{i}' for i in range(1, 41)]
            )
            answer_id = 6213
            for row in csv_data:
                wr.writerow([answer_id, eoneo_id, row[0]] + row[26:66])
                answer_id += 1

                wr.writerow([answer_id, jaryo_id, row[0]] + row[66:106])
                answer_id += 1

                wr.writerow([answer_id, sanghwang_id, row[0]] + row[106:])
                answer_id += 1

                wr.writerow([answer_id, heonbeob_id, row[0]] + row[1:26] + [None for _ in range(0, 15)])
                answer_id += 1

            output_file.close()
            messages = create_instance_get_messages('./temporary.csv', score_models.PrimeAnswer)

            for key, message in messages.items():
                if message:
                    self.stdout.write(self.style.SUCCESS(message))
