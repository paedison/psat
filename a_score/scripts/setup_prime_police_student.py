import traceback

import pandas as pd
import django.db.utils
from django.db import transaction

from a_score.models import PrimePoliceStudent


def run():
    subject_fields = {
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    update_fields = ['answer', 'answer_count']
    update_list = []
    create_list = []
    update_count = 0
    create_count = 0

    for i in range(1, 7):
        file_name = f'a_score/data/prime_police_{i}.xlsx'
        df = pd.read_excel(file_name, sheet_name='문항별 표기', header=[0, 1])
        df.apply(pd.to_numeric, errors='coerce').fillna(0)

        columns_to_keep = df.columns[:2].tolist() + df.columns[33:233].tolist()
        filtered_df = df.loc[:, columns_to_keep].fillna(0)
        labels = list(pd.unique(filtered_df.iloc[0:1, 2:].columns.get_level_values(0)))

        for _, student in filtered_df.iterrows():
            name = student.loc[('이름', 'Unnamed: 1_level_1')]
            serial = student.loc[('응시번호', 'Unnamed: 0_level_1')]
            answer = {
                subject_fields[labels[i]]:
                    [int(answer) for answer in student.loc[labels[i]]] for i in range(len(labels))
            }
            answer_count = {subject_fields[labels[i]]: 40 for i in range(len(labels))}
            student_info = {
                'round': i,
                'name': name,
                'serial': serial,
                'answer': answer,
                'answer_count': answer_count,
            }

            try:
                target_student = PrimePoliceStudent.objects.get(
                    round=i, name=name, serial=serial)
                fields_not_match = any([
                    target_student.answer != answer,
                    target_student.answer_count != answer_count
                ])
                if fields_not_match:
                    target_student.answer = answer
                    target_student.answer_count = answer_count
                    update_list.append(target_student)
                    update_count += 1
            except PrimePoliceStudent.DoesNotExist:
                create_list.append(PrimePoliceStudent(**student_info))
                create_count += 1

    try:
        with transaction.atomic():
            if create_list:
                PrimePoliceStudent.objects.bulk_create(create_list)
                message = f'Successfully created {create_count} PrimePoliceStudent instances.'
            elif update_list:
                PrimePoliceStudent.objects.bulk_update(update_list, update_fields)
                message = f'Successfully updated {update_count} PrimePoliceStudent instances.'
            else:
                message = f'No changes were made to PrimePsatStudent instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
    print(message)

