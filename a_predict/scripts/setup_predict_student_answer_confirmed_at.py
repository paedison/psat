import csv

import pandas as pd
from pandas import DataFrame

from a_predict.models import StudentAnswer


def write_csv(filename, fieldnames, rows):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csv_file:
        csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in rows:
            csvwriter.writerow(row)
    print(f'Successfully written in f{filename}')


def run():
    student_answers = StudentAnswer.objects.all()
    filename = 'a_predict/data/predict_statistics_virtual.csv'

    update_list = []
    with open(filename, 'r', encoding='utf-8') as f:
        df: DataFrame = pd.read_csv(f, header=0, index_col=0)  # index: id
        for student_answer in student_answers:
            is_confirmed = all([value for value in student_answer.answer_confirmed.values()])
            student_id = student_answer.student_id
            result_row = df[df['student_id'] == student_id]
            if is_confirmed and not result_row.empty:
                confirmed_at = result_row['updated_at'].values[0]
                student_answer.confirmed_at = confirmed_at
            else:
                student_answer.confirmed_at = None
            update_list.append(student_answer)

    StudentAnswer.objects.bulk_update(update_list, ['confirmed_at'])
