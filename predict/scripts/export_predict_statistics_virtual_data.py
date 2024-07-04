import csv

from django.db.models import F

from predict import models as predict_models


def write_csv(filename, fieldnames, rows):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csv_file:
        csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in rows:
            csvwriter.writerow(row)
    print(f'Successfully written in f{filename}')


def run():
    fields = [
        'id',
        'updated_at',
        'score_heonbeob',
        'score_eoneo',
        'score_jaryo',
        'score_sanghwang',
        'student_id',
        'created_at',
    ]
    statistics_virtual = predict_models.StatisticsVirtual.objects.values(
        'id',
        'updated_at',
        'score_heonbeob',
        'score_eoneo',
        'score_jaryo',
        'score_sanghwang',
        'student_id',
        created_at=F('timestamp'),
    )

    filename1 = 'predict/scripts/predict_statistics_virtual.csv'
    write_csv(filename1, fields, statistics_virtual)
