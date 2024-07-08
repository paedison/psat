import traceback
from collections import Counter

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import (
    PrimePsatStudent, PrimePsatAnswerCount,
    PrimePoliceStudent, PrimePoliceAnswerCount
)


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Prime Exam type')
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        student_model_dict = {
            'psat': PrimePsatStudent,
            'police': PrimePoliceStudent,
        }
        answer_count_model_dict = {
            'psat': PrimePsatAnswerCount,
            'police': PrimePoliceAnswerCount,
        }
        student_model = student_model_dict[exam_type]
        answer_count_model = answer_count_model_dict[exam_type]

        field_dict = {
            'psat': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang'],
            'police': [
                'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'haengbeob', 'haenghag', 'minbeob',
                'sebeob', 'hoegye', 'sangbeob', 'gyeongje', 'tonggye', 'jaejeong',
                'jeongbo', 'sine', 'debe', 'tongsin', 'sowe',
            ],
        }
        fields = field_dict[exam_type]

        update_list = []
        create_list = []
        update_count = 0
        create_count = 0

        total_count: dict[str, list[dict[str, str | int]]] = {}
        for field in fields:
            total_count[field] = []
            for i in range(1, 41):
                total_count[field].append({
                    'year': exam_year, 'exam': '프모', 'round': exam_round,
                    'subject': field, 'number': i, 'answer': 0,
                    'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                    'count_0': 0, 'count_multiple': 0, 'count_total': 0,
                })

        qs_student = student_model.objects.filter(year=exam_year, round=exam_round)

        total_answer_lists = {field: [] for field in fields}
        for student in qs_student:
            for field, answer in student.answer.items():
                total_answer_lists[field].append(answer)

        for field, answer_lists in total_answer_lists.items():
            if answer_lists:
                distributions = [Counter() for _ in range(40)]
                for lst in answer_lists:
                    for i, value in enumerate(lst):
                        if value > 5:
                            distributions[i]['count_multiple'] += 1
                        else:
                            distributions[i][value] += 1

                for index, counter in enumerate(distributions):
                    count_1 = counter.get(1, 0)
                    count_2 = counter.get(2, 0)
                    count_3 = counter.get(3, 0)
                    count_4 = counter.get(4, 0)
                    count_5 = counter.get(5, 0)
                    count_0 = counter.get(0, 0)
                    count_multiple = counter.get('count_multiple', 0)
                    count_total = sum([count_1, count_2, count_3, count_4, count_5, count_0, count_multiple])
                    total_count[field][index].update({
                        'count_1': count_1,
                        'count_2': count_2,
                        'count_3': count_3,
                        'count_4': count_4,
                        'count_5': count_5,
                        'count_0': count_0,
                        'count_multiple': count_multiple,
                        'count_total': count_total,
                    })
                    if exam_type == 'police':
                        total_count[field][index].pop('count_5')

        field_list_for_matching = [
            'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0', 'count_multiple', 'count_total',
        ]
        if exam_type == 'police':
            field_list_for_matching.remove('count_5')

        for field in fields:
            for c in total_count[field]:
                if c['count_total']:
                    try:
                        obj = answer_count_model.objects.get(
                            year=exam_year, round=exam_round,
                            subject=c['subject'],
                            number=c['number'],
                        )
                        fields_not_match = any(getattr(obj, field) != c[field] for field in field_list_for_matching)
                        if fields_not_match:
                            for fld in field_list_for_matching:
                                setattr(obj, fld, c[fld])
                            update_list.append(obj)
                            update_count += 1
                    except answer_count_model.DoesNotExist:
                        create_list.append(answer_count_model(**c))
                        create_count += 1

        try:
            with transaction.atomic():
                if create_list:
                    answer_count_model.objects.bulk_create(create_list)
                    message = f'Successfully created {create_count} PrimeAnswerCount instances.'
                if update_list:
                    answer_count_model.objects.bulk_update(update_list, field_list_for_matching)
                    message = f'Successfully updated {update_count} PrimeAnswerCount instances.'
                if not create_list and not update_list:
                    message = f'No changes were made to PrimeAnswerCount instances.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = 'An error occurred during the transaction.'

        self.stdout.write(self.style.SUCCESS(message))
