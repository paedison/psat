import csv
from pprint import pprint

from django.db.models import F

from predict import models as predict_models
from reference import models as reference_models
from score import models as score_models

subject_vars = ['avg', 'heonbeob', 'eoneo', 'jaryo', 'sanghwang']

psat_annotation = {}
prime_annotation = {}

for var in subject_vars:
    var1 = 'psat_avg' if var == 'avg' else var
    var2 = 'psat' if var == 'avg' else var

    psat_annotation[f'psat_{var}'] = F(f'statistics__score_{var1}')
    psat_annotation[f'psat_rank_ratio_total_{var}'] = F(f'statistics__rank_ratio_total_{var2}')
    psat_annotation[f'psat_rank_ratio_department_{var}'] = F(f'statistics__rank_ratio_department_{var2}')

    prime_annotation[f'prime_{var}'] = F(f'student__statistics__score_{var1}')
    prime_annotation[f'prime_rank_ratio_total_{var}'] = F(f'student__statistics__rank_ratio_total_{var2}')
    prime_annotation[f'prime_rank_ratio_department_{var}'] = F(f'student__statistics__rank_ratio_department_{var2}')

psat_annotation_keys = [key for key in psat_annotation.keys()]
prime_annotation_keys = [key for key in prime_annotation.keys()]


def run():
    unit_list = reference_models.Unit.objects.values()
    department_list = reference_models.UnitDepartment.objects.values()

    qs_haengsi_student = (
        predict_models.Student.objects.annotate(**psat_annotation)
        .filter(exam__ex='행시', statistics__score_psat_avg__gt=50).order_by('user_id')
    )
    haengsi_user_ids = set(qs_haengsi_student.values_list('user_id', flat=True))

    qs_prime_student_all = (
        score_models.PrimeVerifiedUser.objects.annotate(**prime_annotation)
        .filter(user_id__in=haengsi_user_ids, prime_avg__gt=50).order_by('user_id')
    )

    all_scores = {}
    for rnd in range(1, 7):
        qs_prime_student = qs_prime_student_all.filter(student__round=rnd)
        prime_user_ids = set(qs_prime_student.values_list('user_id', flat=True))

        user_ids = list(haengsi_user_ids & prime_user_ids)
        user_ids.sort()

        haengsi_scores = (
            qs_haengsi_student.filter(user_id__in=user_ids)
            .values('user_id', 'name', 'serial', 'unit_id', 'department_id', *psat_annotation_keys)
        )
        prime_scores = qs_prime_student.values('user_id', *prime_annotation_keys)

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

            append_list = [
                haengsi_scores[i]['user_id'],
                haengsi_scores[i]['name'],
                haengsi_scores[i]['serial'],
                unit,
                department,
            ]
            for key in psat_annotation.keys():
                append_list.append(haengsi_scores[i][key])
            for key in prime_annotation.keys():
                append_list.append(prime_scores[i][key])

            all_scores[rnd].append(append_list)

        with open(f'scripts/analysis/data_{rnd}.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            field_list = [
                'psat_user_id',
                'name',
                'serial',
                'unit',
                'department',
            ]
            for key in psat_annotation.keys():
                field_list.append(key)
            for key in prime_annotation.keys():
                field_list.append(key)

            writer.writerow(field_list)
            for score in all_scores[rnd]:
                writer.writerow(score)

    # pprint(all_scores)
