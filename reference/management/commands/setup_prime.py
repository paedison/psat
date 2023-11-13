from django.core.management.base import BaseCommand

from common.utils import create_instance_get_messages
from reference.models import Category, Exam, Subject, Prime, PrimeProblem


class Command(BaseCommand):
    help = 'Setup Prime exams & problems'

    def handle(self, *args, **kwargs):
        category_messages = create_instance_get_messages('./data/category.csv', Category)
        exam_messages = create_instance_get_messages('./data/exam.csv', Exam)
        subject_messages = create_instance_get_messages('./data/subject.csv', Subject)
        prime_messages = create_instance_get_messages('./data/prime.csv', Prime)
        prime_problem_messages = create_instance_get_messages('./data/prime_problem.csv', PrimeProblem)

        total_messages = [
            category_messages,
            exam_messages,
            subject_messages,
            prime_messages,
            prime_problem_messages,
        ]
        for messages in total_messages:
            for key, message in messages.items():
                if message:
                    self.stdout.write(self.style.SUCCESS(message))
