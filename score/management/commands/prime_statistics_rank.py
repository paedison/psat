import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Window, F
from django.db.models.functions import Rank, PercentRank

from score import models as score_models

rank_annotation_keys = [
    'total_eoneo',
    'total_jaryo',
    'total_sanghwang',
    'total_psat',
    'total_heonbeob',

    'department_eoneo',
    'department_jaryo',
    'department_sanghwang',
    'department_psat',
    'department_heonbeob',

    'ratio_total_eoneo',
    'ratio_total_jaryo',
    'ratio_total_sanghwang',
    'ratio_total_psat',
    'ratio_total_heonbeob',

    'ratio_department_eoneo',
    'ratio_department_jaryo',
    'ratio_department_sanghwang',
    'ratio_department_psat',
    'ratio_department_heonbeob',
]

rank_update_keys = [
    f'rank_{key}' for key in rank_annotation_keys
]


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('year', type=str, help='Year')
        parser.add_argument('round', type=str, help='Round')

    def handle(self, *args, **kwargs):
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        update_list = []
        update_count = 0

        statistics_model = score_models.PrimeStatistics
        statistics_model_name = 'PrimeStatistics'

        def get_rank_list(queryset, rank_type: str):
            def rank_func(field_name) -> Window:
                return Window(expression=Rank(), order_by=F(field_name).desc())

            def rank_ratio_func(field_name) -> Window:
                return Window(expression=PercentRank(), order_by=F(field_name).desc())

            return queryset.annotate(**{
                f'{rank_type}_eoneo': rank_func('score_eoneo'),
                f'{rank_type}_jaryo': rank_func('score_jaryo'),
                f'{rank_type}_sanghwang': rank_func('score_sanghwang'),
                f'{rank_type}_psat': rank_func('score_psat'),
                f'{rank_type}_heonbeob': rank_func('score_heonbeob'),

                f'ratio_{rank_type}_eoneo': rank_ratio_func('score_eoneo'),
                f'ratio_{rank_type}_jaryo': rank_ratio_func('score_jaryo'),
                f'ratio_{rank_type}_sanghwang': rank_ratio_func('score_sanghwang'),
                f'ratio_{rank_type}_psat': rank_ratio_func('score_psat'),
                f'ratio_{rank_type}_heonbeob': rank_ratio_func('score_heonbeob'),
            }).values(
                'student_id', f'{rank_type}_eoneo', f'{rank_type}_jaryo', f'{rank_type}_sanghwang',
                f'{rank_type}_psat', f'{rank_type}_heonbeob',
                f'ratio_{rank_type}_eoneo',f'ratio_{rank_type}_jaryo', f'ratio_{rank_type}_sanghwang',
                f'ratio_{rank_type}_psat', f'ratio_{rank_type}_heonbeob',
            )

        statistics_qs_total = statistics_model.objects.filter(student__year=exam_year, student__round=exam_round)
        rank_list_total = get_rank_list(statistics_qs_total, 'total')

        for stat in statistics_qs_total:
            statistics_qs_department = statistics_qs_total.filter(student__department_id=stat.student.department_id)
            rank_list_department = get_rank_list(statistics_qs_department, 'department')

            rank_data_dict = {}
            for row in rank_list_total:
                if row['student_id'] == stat.student_id:
                    rank_data_dict.update(row)
            for row in rank_list_department:
                if row['student_id'] == stat.student_id:
                    rank_data_dict.update(row)

            fields_not_match = any(
                str(getattr(stat, f'rank_{key}')) != rank_data_dict[key] for key in rank_annotation_keys
            )
            if fields_not_match:
                for field, value in rank_data_dict.items():
                    setattr(stat, f'rank_{field}', value)
                update_list.append(stat)
                update_count += 1

        try:
            with transaction.atomic():
                if update_list:
                    statistics_model.objects.bulk_update(update_list, rank_update_keys)
                    message = f'Successfully {update_count} {statistics_model_name} instances updated.'
                else:
                    message = f'{statistics_model_name} instances already exist.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'

        self.stdout.write(self.style.SUCCESS(message))
