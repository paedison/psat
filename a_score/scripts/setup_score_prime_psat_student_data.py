import traceback

import django.db.utils
from django.db import transaction
from django.db.models import F, Value

from a_score import models as new_models
from score import models as old_models


def run():
    list_update = []
    list_create = []
    count_update = 0
    count_create = 0

    sub_fields = {'헌법': 'heonbeob', '언어': 'eoneo', '자료': 'jaryo', '상황': 'sanghwang'}
    unit_dict = {
        '5급공채-일반행정': '5급공채',
        '5급공채-재경': '5급공채',
        '5급공채-기술직': '5급공채',
        '5급공채-기타': '5급공채',
        '7급공채': '7급공채',
        '외교관후보자': '외교관후보자',
        '지역인재 7급': '지역인재 7급',
        '기타': '기타',
    }
    department_dict = {
        '5급공채-일반행정': '5급 일반행정',
        '5급공채-재경': '5급 재경',
        '5급공채-기술직': '5급 기술',
        '5급공채-기타': '5급 기타',
        '7급공채': '7급 행정',
        '외교관후보자': '일반외교',
        '지역인재 7급': '지역인재 7급 행정',
        '기타': '기타 직렬',
    }
    matching_fields = ['id', 'created_at', 'year', 'exam', 'round', 'name', 'serial', 'password']
    update_fields = matching_fields.copy()
    update_fields.extend(['unit', 'department', 'answer', 'answer_count'])
    update_fields.remove('id')

    qs_old_student = old_models.PrimeStudent.objects.annotate(
        created_at=F('timestamp'),
        exam=Value('프모'),
        department_name=F('department__name'),
    )

    for old_student in qs_old_student:
        unit = unit_dict[old_student.department_name]
        department = department_dict[old_student.department_name]

        qs_old_answer = old_models.PrimeAnswer.objects.filter(student=old_student).order_by('prime_id')
        answer_dict = {'heonbeob': [], 'eoneo': [], 'jaryo': [], 'sanghwang': []}
        answer_count_dict = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}

        answer: old_models.PrimeAnswer
        for answer in qs_old_answer:
            field = sub_fields[answer.prime.subject.abbr]
            for i in range(1, answer_count_dict[field] + 1):
                ans = getattr(answer, f'prob{i}', 0)
                answer_dict[field].append(ans)

        try:
            new_student = new_models.PrimePsatStudent.objects.get(id=old_student.id)
            fields_not_match = any(
                str(getattr(new_student, field)) != str(getattr(old_student, field)) for field in matching_fields
            )
            other_fields_not_match = any([
                new_student.unit != unit,
                new_student.department != department,
                new_student.answer != answer_dict,
                new_student.answer_count != answer_count_dict,
            ])
            if fields_not_match or other_fields_not_match:
                for field in matching_fields:
                    setattr(new_student, field, getattr(old_student, field))
                new_student.answer = answer_dict
                list_update.append(new_student)
                count_update += 1
        except new_models.PrimePsatStudent.DoesNotExist:
            list_create.append(
                new_models.PrimePsatStudent(
                    id=old_student.id,
                    created_at=old_student.created_at,

                    year=old_student.year,
                    exam=old_student.exam,
                    round=old_student.round,

                    name=old_student.name,
                    serial=old_student.serial,
                    unit=unit,
                    department=department,

                    password=old_student.password,

                    answer=answer_dict,
                    answer_count=answer_count_dict,
                )
            )
            count_create += 1

    try:
        with transaction.atomic():
            if list_create:
                new_models.PrimePsatStudent.objects.bulk_create(list_create)
                message = f'Successfully created {count_create} PrimePsatStudent instances.'
            elif list_update:
                new_models.PrimePsatStudent.objects.bulk_update(list_update, update_fields)
                message = f'Successfully updated {count_update} PrimePsatStudent instances.'
            else:
                message = f'No changes were made to PrimePsatStudent instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
    print(message)
