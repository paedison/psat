from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Import data from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument('model_name', type=str, help='Name of the model to import data into')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        model_name = options['model_name']

        try:
            model = apps.get_model(app_label='study', model_name=model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f"Model '{model_name}' not found."))
            return

        with open(csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            # Assuming the first row contains field names
            field_names = csv_file.readline().strip().split(',')
            for row in csv_file:
                data = row.strip().split(',')
                if model_name == 'question':
                    instance = model(chapter_id=data[0], number=data[1], problem_id=data[2])
                else:
                    instance = model(**dict(zip(field_names, data)))
                instance.save()
