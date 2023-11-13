from django.core.management.base import BaseCommand

from common.utils import create_instance_get_messages
from score import models as score_models


class Command(BaseCommand):
    help = 'Setup Prime units & department'

    def handle(self, *args, **kwargs):
        department_messages = create_instance_get_messages('./data/prime_department.csv', score_models.PrimeDepartment)

        total_messages = [
            department_messages,
        ]
        for messages in total_messages:
            for key, message in messages.items():
                if message:
                    self.stdout.write(self.style.SUCCESS(message))
