import csv
from pprint import pprint

from django.db.models import F

from predict import models as predict_models
from reference import models as reference_models
from score import models as score_models


def run():
    unit_list = reference_models.Unit.objects.values()
    department_list = reference_models.UnitDepartment.objects.values()

    qs_haengsi_student = (
        predict_models.Student.objects
        .annotate(
            psat_avg=F('statistics__score_psat_avg'),
            psat_rank_ratio_total=F('statistics__rank_ratio_total_psat'),
            psat_rank_ratio_department=F('statistics__rank_ratio_department_psat'),
        )
        .filter(exam__ex='행시', statistics__score_psat_avg__gt=50)
        .order_by('user_id')
    )
    haengsi_user_ids = set(qs_haengsi_student.values_list('user_id', flat=True))

    qs_prime_student_all = (
        score_models.PrimeVerifiedUser.objects
        .annotate(
            prime_avg=F('student__statistics__score_psat_avg'),
            prime_rank_ratio_total=F('student__statistics__rank_ratio_total_psat'),
            prime_rank_ratio_department=F('student__statistics__rank_ratio_department_psat'),
        )
        .filter(user_id__in=haengsi_user_ids, prime_avg__gt=50)
        .order_by('user_id')
    )

    all_scores = {}
    for rnd in range(1, 7):
        qs_prime_student = qs_prime_student_all.filter(student__round=rnd)
        prime_user_ids = set(qs_prime_student.values_list('user_id', flat=True))

        user_ids = list(haengsi_user_ids & prime_user_ids)
        user_ids.sort()

        haengsi_scores = (
            qs_haengsi_student.filter(user_id__in=user_ids)
            .values(
                'user_id', 'name', 'serial', 'unit_id', 'department_id',
                'psat_avg', 'psat_rank_ratio_total', 'psat_rank_ratio_department',
            )
        )
        prime_scores = qs_prime_student.values(
            'user_id', 'prime_avg', 'prime_rank_ratio_total', 'prime_rank_ratio_department'
        )

        all_scores[rnd] = []
        for i in range(len(user_ids)):
            unit = ''
            for row in unit_list:
                if row['id'] == haengsi_scores[i]['unit_id']:
                    unit = row['name']

            department = ''
            for row in department_list:
                if row['id'] == haengsi_scores[i]['department_id']:
                    department = row['name']

            all_scores[rnd].append(
                (
                    haengsi_scores[i]['user_id'],
                    haengsi_scores[i]['name'],
                    haengsi_scores[i]['serial'],
                    unit,
                    department,
                    round(haengsi_scores[i]['psat_avg'], 1),
                    haengsi_scores[i]['psat_rank_ratio_total'],
                    haengsi_scores[i]['psat_rank_ratio_department'],
                    prime_scores[i]['user_id'],
                    round(prime_scores[i]['prime_avg'], 1),
                    prime_scores[i]['prime_rank_ratio_total'],
                    prime_scores[i]['prime_rank_ratio_department'],
                )
            )

        with open(f'scripts/analysis/data_{rnd}.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    'psat_user_id',
                    'name',
                    'serial',
                    'unit',
                    'department',
                    'psat_avg',
                    'psat_rank_ratio_total',
                    'psat_rank_ratio_department',

                    'prime_user_id',
                    'prime_avg',
                    'prime_rank_ratio_total',
                    'prime_rank_ratio_department',
                ]
            )
            for score in all_scores[rnd]:
                writer.writerow(score)

    # pprint(all_scores)
