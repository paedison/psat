from django.apps import apps
from django.core.management.base import BaseCommand

from score.management.commands.utils.db_setup import create_instance_get_messages


class Command(BaseCommand):
    help = 'Update Score Database'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Name of the target file')
        parser.add_argument('app_name', type=str, help='Name of the app containing the model')
        parser.add_argument('model_name', type=str, help='Name of the model')

    def handle(self, *args, **kwargs):
        file_name = kwargs['file_name']
        app_name = kwargs['app_name']
        model_name = kwargs['model_name']

        try:
            model = apps.get_model(app_label=app_name, model_name=model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f"Model '{model_name}' not found in app '{app_name}'."))
            return

        messages = create_instance_get_messages(file_name, model)
        for key, message in messages.items():
            if message:
                self.stdout.write(self.style.SUCCESS(message))
