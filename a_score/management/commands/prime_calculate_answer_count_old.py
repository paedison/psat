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
            'psat': {
                'heonbeob': '헌법',
                'eoneo': '언어',
                'jaryo': '자료',
                'sanghwang': '상황',
            },
            'police': {
                'hyeongsa': '형사',
                'heonbeob': '헌법',
                'gyeongchal': '경찰',
                'beomjoe': '범죄',
                'haengbeob': '행법',
                'haenghag': '행학',
                'minbeob': '민법',
                'sebeob': '세법',
                'hoegye': '회계',
                'sangbeob': '상법',
                'gyeongje': '경제',
                'tonggye': '통계',
                'jaejeong': '재정',
                'jeongbo': '정보',
                'sine': '시네',
                'debe': '데베',
                'tongsin': '통신',
                'sowe': '소웨'
            },
        }
        fields = field_dict[exam_type]

        list_update = []
        list_create = []
        count_update = 0
        count_create = 0

        total_count = {}
        for field, subject in fields.items():
            total_count[field] = []
            for i in range(1, 41):
                total_count[field].append({
                    'year': exam_year, 'exam': '프모', 'round': exam_round,
                    'subject': subject, 'number': i, 'answer': 0,
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

        field_list_for_matching = [
            'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0', 'count_multiple', 'count_total',
        ]

        for field in fields.keys():
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
                            list_update.append(obj)
                            count_update += 1
                    except answer_count_model.DoesNotExist:
                        list_create.append(answer_count_model(**c))
                        count_create += 1

        try:
            with transaction.atomic():
                if list_create:
                    answer_count_model.objects.bulk_create(list_create)
                    message = f'Successfully created {count_create} PrimeAnswerCount instances.'
                if list_update:
                    answer_count_model.objects.bulk_update(list_update, field_list_for_matching)
                    message = f'Successfully updated {count_update} PrimeAnswerCount instances.'
                if not list_create and not list_update:
                    message = f'No changes were made to PrimeAnswerCount instances.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = 'An error occurred during the transaction.'

        self.stdout.write(self.style.SUCCESS(message))
