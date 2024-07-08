import traceback
from collections import Counter

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import (
    PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount,
    PrimePoliceExam, PrimePoliceStudent, PrimePoliceAnswerCount,
)


def get_models_and_field(exam_type: str) -> tuple:
    psat_fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
    police_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'haengbeob', 'haenghag', 'minbeob',
        'sebeob', 'hoegye', 'sangbeob', 'gyeongje', 'tonggye', 'jaejeong',
        'jeongbo', 'sine', 'debe', 'tongsin', 'sowe',
    ]
    if exam_type == 'psat':
        return PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount, psat_fields
    elif exam_type == 'police':
        return PrimePoliceExam, PrimePoliceStudent, PrimePoliceAnswerCount, police_fields
    else:
        raise Exception("exam_type should be one of 'psat' or 'police'.")


def get_empty_dict_total_count(fields: list, exam_year: int, exam_round: int) -> dict:
    total_count: dict[str, list[dict[str, str | int]]] = {}
    for field in fields:
        total_count[field] = []
        for i in range(1, 41):
            total_count[field].append({
                'year': exam_year, 'exam': '프모', 'round': exam_round,
                'subject': field, 'number': i, 'answer': 0,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            })
    return total_count


def get_total_answer_lists_and_score_from_student(
        exam_type: str, total_answer_lists: dict, student, answer_official: dict
) -> tuple:
    score: dict = {}
    psat_fields = ['eoneo', 'jaryo', 'sanghwang']

    for field, answer in student.answer.items():
        total_answer_lists[field].append(answer)

        score_unit = 2.5
        if exam_type == 'psat' and field in ['heonbeob']:
            score_unit = 4.0
        elif exam_type == 'police':
            dict_score_unit = {
                'hyeongsa': 3, 'gyeongchal': 3,
                'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
                'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
            }
            score_unit = dict_score_unit[field] if field in dict_score_unit.keys() else 1.5

        correct_count = 0
        for index, ans in enumerate(answer):
            if ans == answer_official[field][index]:
                correct_count += 1
        score[field] = correct_count * score_unit

    if exam_type == 'psat':
        sum_list = [score[field] for field in psat_fields if field in score.keys()]
        score['psat_avg'] = sum(sum_list) / 3
    elif exam_type == 'police':
        score['sum'] = sum(s for s in score.values())
    return total_answer_lists, score


def update_total_count(
        exam_type: str,
        total_answer_lists: dict,
        total_count: dict,
):
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
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                total_count[field][index].update(count_dict)
                if exam_type == 'police':
                    total_count[field][index].pop('count_5')


def get_field_list_for_matching(exam_type):
    field_list_for_matching = [
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_total',
    ]
    if exam_type == 'police':
        field_list_for_matching.remove('count_5')
    return field_list_for_matching


def get_score_and_participants(student, queryset) -> tuple[dict, dict]:
    score = {}
    participants = {}
    rank = {}
    for field, value in student.score.items():
        score[field] = []
        for qs in queryset:
            if field in qs['score'].keys():
                score[field].append(qs['score'][field])
        participants[field] = len(score[field])
        if field in student.score.keys():
            sorted_score = sorted(score[field], reverse=True)
            rank[field] = sorted_score.index(student.score[field]) + 1
    return rank, participants


def create_or_update_model_return_message(
        model,
        update_fields: list,
        update_list: list,
        update_count: int,
        create_list: list | None = None,
        create_count: int = 0,
):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if update_list:
                model.objects.bulk_update(update_list, update_fields)
                message = f'Successfully updated {update_count} {model_name} instances.'
            if create_list:
                model.objects.bulk_create(create_list)
                message = f'Successfully created {create_count} {model_name} instances.'
            if not update_list and not create_list:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = 'An error occurred during the transaction.'
    return message


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Prime Exam type')  # psat, police
        parser.add_argument('year', type=str, help='Year')  # 2024
        parser.add_argument('round', type=str, help='Round')  # 1

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['year']
        exam_round = kwargs['round']

        # Get default models and fields
        exam_model, student_model, answer_count_model, fields = get_models_and_field(exam_type=exam_type)

        # Set up default lists and counts
        update_list_score = []
        update_count_score = 0
        update_list_answer_count = []
        create_list_answer_count = []
        update_count_answer_count = 0
        create_count_answer_count = 0
        update_list_rank = []
        update_count_rank = 0
        total_count = get_empty_dict_total_count(
            fields=fields, exam_year=exam_year, exam_round=exam_round)
        total_answer_lists = {field: [] for field in fields}

        # Get student queryset and answer official
        qs_student = student_model.objects.filter(year=exam_year, round=exam_round)
        answer_official = exam_model.objects.get(year=exam_year, round=exam_round).answer_official

        # Update student_model for score
        for student in qs_student:
            total_answer_lists, score = get_total_answer_lists_and_score_from_student(
                exam_type=exam_type, total_answer_lists=total_answer_lists,
                student=student, answer_official=answer_official)
            if student.score != score:
                student.score = score
                update_list_score.append(student)
                update_count_score += 1
        message = create_or_update_model_return_message(
            model=student_model, update_fields=['score'],
            update_list=update_list_score, update_count=update_count_score)
        self.stdout.write(self.style.SUCCESS(message))

        # Create or update answer_count_model
        update_total_count(
            exam_type=exam_type, total_answer_lists=total_answer_lists, total_count=total_count)
        matching_fields_for_answer_count = get_field_list_for_matching(exam_type=exam_type)
        for field in fields:
            for c in total_count[field]:
                if c['count_total']:
                    try:
                        obj = answer_count_model.objects.get(
                            year=exam_year, round=exam_round,
                            subject=c['subject'], number=c['number'])
                        fields_not_match = any(
                            getattr(obj, fld) != c[fld] for fld in matching_fields_for_answer_count)
                        if fields_not_match:
                            for fld in matching_fields_for_answer_count:
                                setattr(obj, fld, c[fld])
                            update_list_answer_count.append(obj)
                            update_count_answer_count += 1
                    except answer_count_model.DoesNotExist:
                        create_list_answer_count.append(answer_count_model(**c))
                        create_count_answer_count += 1
        message = create_or_update_model_return_message(
            model=answer_count_model, update_fields=matching_fields_for_answer_count,
            update_list=update_list_answer_count, update_count=update_count_answer_count,
            create_list=create_list_answer_count, create_count=create_count_answer_count,
        )
        self.stdout.write(self.style.SUCCESS(message))

        # Update student_model for rank
        qs_all_score_total = qs_student.values('score')
        matching_fields_for_rank = [
            'rank_total', 'participants_total', 'rank_department', 'participants_department']
        for student in qs_student:
            qs_all_score_department = qs_student.filter(department=student.department).values('score')
            rank_total, participants_total = get_score_and_participants(
                student=student, queryset=qs_all_score_total)
            rank_department, participants_department = get_score_and_participants(
                student=student, queryset=qs_all_score_department)
            stat_dict = {
                'rank_total': rank_total,
                'participants_total': participants_total,
                'rank_department': rank_department,
                'participants_department': participants_department,
            }
            fields_not_match = any(getattr(student, fld) != val for fld, val in stat_dict.items())
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(student, fld, val)
                update_list_rank.append(student)
                update_count_rank += 1
        message = create_or_update_model_return_message(
            model=student_model, update_fields=matching_fields_for_rank,
            update_list=update_list_rank, update_count=update_count_rank)
        self.stdout.write(self.style.SUCCESS(message))
