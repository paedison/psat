import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from score import models as score_models


class Command(BaseCommand):
    help = 'Add PSAT answer data'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Name of the target file')

    def handle(self, *args, **kwargs):
        file_name = kwargs['file_name']

        model = score_models.PsatConfirmedAnswer
        batch_size = 100
        create_list = []
        create_count = 0
        create_message = ''

        with open(file_name, 'r', encoding='utf-8') as file:
            csv_data = csv.reader(file)
            key = next(csv_data)
            for row in csv_data:
                for i in range(1, len(row)):
                    user_id = 200_000_000
                    if row[i]:
                        create_list.append(
                            model(user_id=user_id, problem_id=row[0], answer=row[i])
                        )
                        create_count += 1
            # print(create_list)
            with transaction.atomic():
                if create_list:
                    model.objects.bulk_create(
                        create_list, batch_size, ignore_conflicts=True)
                    create_message = f'Successfully {create_count} {model} instances created.'

        self.stdout.write(self.style.SUCCESS(create_message))
