import csv
from pprint import pprint

from django.db.models import F

from predict import models as predict_models
from score import models as score_models


def run():
    qs_haengsi_student = (
        predict_models.Student.objects
        .annotate(psat_avg=F('statistics__score_psat_avg'))
        .filter(exam__ex='행시', statistics__score_psat_avg__gt=50)
        .order_by('user_id')
    )
    haengsi_user_ids = set(qs_haengsi_student.values_list('user_id', flat=True))

    qs_prime_student_all = (
        score_models.PrimeVerifiedUser.objects
        .annotate(prime_psat_avg=F('student__statistics__score_psat_avg'))
        .filter(user_id__in=haengsi_user_ids, prime_psat_avg__gt=50)
        .order_by('user_id')
    )

    all_scores = {}
    for rnd in range(1, 7):
        qs_prime_student = qs_prime_student_all.filter(student__round=rnd)
        prime_user_ids = set(qs_prime_student.values_list('user_id', flat=True))

        user_ids = list(haengsi_user_ids & prime_user_ids)
        user_ids.sort()

        haengsi_scores = qs_haengsi_student.filter(user_id__in=user_ids).values('user_id', 'psat_avg')
        prime_scores = qs_prime_student.values('user_id', 'prime_psat_avg')

        all_scores[rnd] = []
        for i in range(len(user_ids)):
            all_scores[rnd].append(
                (
                    haengsi_scores[i]['user_id'],
                    round(haengsi_scores[i]['psat_avg'], 1),
                    prime_scores[i]['user_id'],
                    round(prime_scores[i]['prime_psat_avg'], 1),
                )
            )

        with open(f'scripts/analysis/data_{rnd}.csv', 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['psat_user_id', 'psat_avg', 'prime_user_id', 'prime_psat_avg'])
            for score in all_scores[rnd]:
                writer.writerow(score)

    pprint(all_scores)
