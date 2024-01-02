from django.core.management.base import BaseCommand

from reference.models import PrimeProblem
from score.management.commands.utils.db_setup import create_instance_get_messages


class Command(BaseCommand):
    help = 'Add Prime answers'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Name of the target file')

    def handle(self, *args, **kwargs):
        file_name = kwargs['file_name']
        prime_problem_messages = create_instance_get_messages(file_name, PrimeProblem)

        total_messages = [
            prime_problem_messages,
        ]
        for messages in total_messages:
            for key, message in messages.items():
                if message:
                    self.stdout.write(self.style.SUCCESS(message))
