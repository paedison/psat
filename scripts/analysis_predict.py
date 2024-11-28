import csv
from pprint import pprint

from django.db.models import F

from predict import models as predict_models
from reference import models as reference_models
from score import models as score_models

subject_vars = ['avg', 'heonbeob', 'eoneo', 'jaryo', 'sanghwang']


def run():
    unit_list = reference_models.Unit.objects.values()
    department_list = reference_models.UnitDepartment.objects.values()

    psat_annotation = {}
    for var in subject_vars:
        var1 = 'psat_avg' if var == 'avg' else var
        var2 = 'psat' if var == 'avg' else var
        psat_annotation[f'psat_{var}'] = F(f'statistics__score_{var1}')
        psat_annotation[f'psat_rank_ratio_total_{var}'] = F(f'statistics__rank_ratio_total_{var2}')
        psat_annotation[f'psat_rank_ratio_department_{var}'] = F(f'statistics__rank_ratio_department_{var2}')
    print(psat_annotation)

    # qs_haengsi_student = (
    #     predict_models.Student.objects
    #     .annotate(
    #         psat_avg=F('statistics__score_psat_avg'),
    #         psat_rank_ratio_total=F('statistics__rank_ratio_total_psat'),
    #         psat_rank_ratio_department=F('statistics__rank_ratio_department_psat'),
    #
    #         psat_heonbeob=F('statistics__score_heonbeob'),
    #         psat_rank_ratio_total_heonbeob=F('statistics__rank_ratio_total_heonbeob'),
    #         psat_rank_ratio_department_heonbeob=F('statistics__rank_ratio_department_heonbeob'),
    #
    #         psat_eoneo=F('statistics__score_eoneo'),
    #         psat_rank_ratio_total_eoneo=F('statistics__rank_ratio_total_eoneo'),
    #         psat_rank_ratio_department_eoneo=F('statistics__rank_ratio_department_eoneo'),
    #
    #         psat_jaryo=F('statistics__score_jaryo'),
    #         psat_rank_ratio_total_jaryo=F('statistics__rank_ratio_total_jaryo'),
    #         psat_rank_ratio_department_jaryo=F('statistics__rank_ratio_department_jaryo'),
    #
    #         psat_sanghwang=F('statistics__score_sanghwang'),
    #         psat_rank_ratio_total_sanghwang=F('statistics__rank_ratio_total_sanghwang'),
    #         psat_rank_ratio_department_sanghwang=F('statistics__rank_ratio_department_sanghwang'),
    #     )
    #     .filter(exam__ex='행시', statistics__score_psat_avg__gt=50)
    #     .order_by('user_id')
    # )
    # haengsi_user_ids = set(qs_haengsi_student.values_list('user_id', flat=True))
    #
    # qs_prime_student_all = (
    #     score_models.PrimeVerifiedUser.objects
    #     .annotate(
    #         prime_avg=F('student__statistics__score_psat_avg'),
    #         prime_rank_ratio_total=F('student__statistics__rank_ratio_total_psat'),
    #         prime_rank_ratio_department=F('student__statistics__rank_ratio_department_psat'),
    #
    #         prime_heonbeob=F('student__statistics__score_heonbeob'),
    #         prime_rank_ratio_total_heonbeob=F('student__statistics__rank_ratio_total_heonbeob'),
    #         prime_rank_ratio_department_heonbeob=F('student__statistics__rank_ratio_department_heonbeob'),
    #
    #         prime_eoneo=F('student__statistics__score_eoneo'),
    #         prime_rank_ratio_total_eoneo=F('student__statistics__rank_ratio_total_eoneo'),
    #         prime_rank_ratio_department_eoneo=F('student__statistics__rank_ratio_department_eoneo'),
    #
    #         prime_jaryo=F('student__statistics__score_jaryo'),
    #         prime_rank_ratio_total_jaryo=F('student__statistics__rank_ratio_total_jaryo'),
    #         prime_rank_ratio_department_jaryo=F('student__statistics__rank_ratio_department_jaryo'),
    #
    #         prime_sanghwang=F('student__statistics__score_sanghwang'),
    #         prime_rank_ratio_total_sanghwang=F('student__statistics__rank_ratio_total_sanghwang'),
    #         prime_rank_ratio_department_sanghwang=F('student__statistics__rank_ratio_department_sanghwang'),
    #     )
    #     .filter(user_id__in=haengsi_user_ids, prime_avg__gt=50)
    #     .order_by('user_id')
    # )
    #
    # all_scores = {}
    # for rnd in range(1, 7):
    #     qs_prime_student = qs_prime_student_all.filter(student__round=rnd)
    #     prime_user_ids = set(qs_prime_student.values_list('user_id', flat=True))
    #
    #     user_ids = list(haengsi_user_ids & prime_user_ids)
    #     user_ids.sort()
    #
    #     haengsi_scores = (
    #         qs_haengsi_student.filter(user_id__in=user_ids)
    #         .values(
    #             'user_id', 'name', 'serial', 'unit_id', 'department_id',
    #             'psat_avg', 'psat_rank_ratio_total', 'psat_rank_ratio_department',
    #             'psat_heonbeob', 'psat_rank_ratio_total_heonbeob', 'psat_rank_ratio_department_heonbeob',
    #             'psat_eoneo', 'psat_rank_ratio_total_eoneo', 'psat_rank_ratio_department_eoneo',
    #             'psat_jaryo', 'psat_rank_ratio_total_jaryo', 'psat_rank_ratio_department_jaryo',
    #             'psat_sanghwang', 'psat_rank_ratio_total_sanghwang', 'psat_rank_ratio_department_sanghwang',
    #         )
    #     )
    #     prime_scores = qs_prime_student.values(
    #         'user_id', 'prime_avg', 'prime_rank_ratio_total', 'prime_rank_ratio_department',
    #         'prime_heonbeob', 'prime_rank_ratio_total_heonbeob', 'prime_rank_ratio_department_heonbeob',
    #         'prime_eoneo', 'prime_rank_ratio_total_eoneo', 'prime_rank_ratio_department_eoneo',
    #         'prime_jaryo', 'prime_rank_ratio_total_jaryo', 'prime_rank_ratio_department_jaryo',
    #         'prime_sanghwang', 'prime_rank_ratio_total_sanghwang', 'prime_rank_ratio_department_sanghwang',
    #     )
    #
    #     all_scores[rnd] = []
    #     for i in range(len(user_ids)):
    #         unit = ''
    #         for row in unit_list:
    #             if row['id'] == haengsi_scores[i]['unit_id']:
    #                 unit = row['name']
    #
    #         department = ''
    #         for row in department_list:
    #             if row['id'] == haengsi_scores[i]['department_id']:
    #                 department = row['name']
    #
    #         all_scores[rnd].append(
    #             (
    #                 haengsi_scores[i]['user_id'],
    #                 haengsi_scores[i]['name'],
    #                 haengsi_scores[i]['serial'],
    #                 unit,
    #                 department,
    #
    #                 round(haengsi_scores[i]['psat_avg'], 1),
    #                 haengsi_scores[i]['psat_rank_ratio_total'],
    #                 haengsi_scores[i]['psat_rank_ratio_department'],
    #
    #                 round(haengsi_scores[i]['psat_heonbeob'], 1),
    #                 haengsi_scores[i]['psat_rank_ratio_total_heonbeob'],
    #                 haengsi_scores[i]['psat_rank_ratio_department_heonbeob'],
    #
    #                 round(haengsi_scores[i]['psat_eoneo'], 1),
    #                 haengsi_scores[i]['psat_rank_ratio_total_eoneo'],
    #                 haengsi_scores[i]['psat_rank_ratio_department_heonbeob'],
    #
    #                 prime_scores[i]['user_id'],
    #                 round(prime_scores[i]['prime_avg'], 1),
    #                 prime_scores[i]['prime_rank_ratio_total'],
    #                 prime_scores[i]['prime_rank_ratio_department'],
    #             )
    #         )
    #
    #     with open(f'scripts/analysis/data_{rnd}.csv', 'w', encoding='utf-8-sig', newline='') as file:
    #         writer = csv.writer(file)
    #         writer.writerow(
    #             [
    #                 'psat_user_id',
    #                 'name',
    #                 'serial',
    #                 'unit',
    #                 'department',
    #                 'psat_avg',
    #                 'psat_rank_ratio_total',
    #                 'psat_rank_ratio_department',
    #
    #                 'prime_user_id',
    #                 'prime_avg',
    #                 'prime_rank_ratio_total',
    #                 'prime_rank_ratio_department',
    #             ]
    #         )
    #         for score in all_scores[rnd]:
    #             writer.writerow(score)

    # pprint(all_scores)
