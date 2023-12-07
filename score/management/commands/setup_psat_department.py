from django.core.management.base import BaseCommand

from .utils.db_setup import create_instance_get_messages
from score import models as score_models


class Command(BaseCommand):
    help = 'Setup PSAT units & department'

    def handle(self, *args, **kwargs):
        unit_messages = create_instance_get_messages('./data/unit.csv', score_models.PsatUnit)
        department_messages = create_instance_get_messages('./data/unitdepartment.csv', score_models.PsatUnitDepartment)

        total_messages = [
            unit_messages,
            department_messages,
        ]
        for messages in total_messages:
            for key, message in messages.items():
                if message:
                    self.stdout.write(self.style.SUCCESS(message))
