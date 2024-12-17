import traceback
from collections import defaultdict

import django.db.utils
from django.core.management import CommandError
from django.db import transaction
from django.db.models import F, Count, When, Window
from django.db.models.functions import Rank

from a_prime import models as new_prime_models
from reference import models as old_reference_models
from score import models as old_score_models


def test(new_model, queryset, lookup_fields, update_fields):
    model_name = new_model._meta.model_name
    list_update = []
    list_create = []
    count_update = 0
    count_create = 0
    for old_query in queryset:

        lookup_expr = {}
        for old_fld, new_fld in lookup_fields.items():
            lookup_expr[new_fld] = getattr(old_query, old_fld)

        update_expr = {}
        for old_fld, new_fld in update_fields.items():
            update_expr[new_fld] = getattr(old_query, old_fld)

        try:
            new_query = new_model.objects.get(**lookup_expr)
            fields_not_match = any(
                getattr(new_query, new_fld) != getattr(old_query, old_fld)
                for old_fld, new_fld in update_fields.items()
            )
            if fields_not_match:
                for fld, val in update_expr.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
                count_update += 1
        except new_model.DoesNotExist:
            list_create.append(new_model(**lookup_expr))
            count_create += 1

    try:
        with transaction.atomic():
            if list_create:
                new_model.objects.bulk_create(list_create)
                message = f'Successfully created {count_create} {model_name} instances.'
            elif list_update:
                new_model.objects.bulk_update(list_update, list(update_fields.values()))
                message = f'Successfully updated {count_update} {model_name} instances.'
            else:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
    print(message)


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
            else:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
    print(message)


def update_problem_model():
    list_update = []
    list_create = []

    qs_old_queryset = old_reference_models.PrimeProblem.objects.order_by('id')
    for old_query in qs_old_queryset:
        psat_expr = {
            'year': old_query.prime.year,
            'round': old_query.prime.round,
        }
        lookup_expr = {
            'subject': old_query.prime.subject.abbr,
            'number': old_query.number
        }
        update_expr = {
            'answer': old_query.answer,
        }

        try:
            new_query = new_prime_models.Psat.objects.get(**psat_expr)
        except new_prime_models.Psat.DoesNotExist:
            new_query = None

        if new_query:
            try:
                new_problem = new_prime_models.Problem.objects.get(psat=new_query, **lookup_expr)
                if new_problem.answer != old_query.answer:
                    new_problem.answer = old_query.answer
                    list_update.append(new_problem)
            except new_prime_models.Problem.DoesNotExist:
                list_create.append(new_prime_models.Problem(psat=new_query, **lookup_expr, **update_expr))
    update_fields = ['psat', 'subject', 'number', 'answer']
    bulk_create_or_update(new_prime_models.Problem, list_create, list_update, update_fields)


def update_result_student_model():
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
        '5급공채-기술직': '5급 과학기술',
        '5급공채-기타': '5급 기타',
        '7급공채': '7급 행정',
        '외교관후보자': '일반외교',
        '지역인재 7급': '지역인재 7급 행정',
        '기타': '기타 직렬',
    }

    list_update = []
    list_create = []

    qs_old_query = old_score_models.PrimeStudent.objects.filter(year__gte=2024).order_by('id').annotate(
        created_at=F('timestamp'),
    )
    for old_query in qs_old_query:
        psat_expr = {
            'year': old_query.year,
            'round': old_query.round,
        }
        category_expr = {
            'unit': unit_dict[old_query.department.name],
            'department': department_dict[old_query.department.name],
        }
        lookup_expr = {
            'name': old_query.name,
            'serial': old_query.serial,
            'password': old_query.password,
        }
        update_expr = {
            'created_at': old_query.created_at,
        }

        new_psat = new_prime_models.Psat.objects.get(**psat_expr)
        new_category = new_prime_models.Category.objects.get(**category_expr)

        try:
            new_query = new_prime_models.ResultStudent.objects.get(
                psat=new_psat, category=new_category, **lookup_expr)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in update_expr.items()
            )
            if fields_not_match:
                for fld, val in update_expr.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except new_prime_models.ResultStudent.DoesNotExist:
            list_create.append(new_prime_models.ResultStudent(
                psat=new_psat, category=new_category, **lookup_expr, **update_expr))
    update_fields = ['psat', 'category', 'created_at', 'name', 'serial', 'password']
    bulk_create_or_update(new_prime_models.ResultStudent, list_create, list_update, update_fields)


def update_result_registry_model():
    list_update = []
    list_create = []

    qs_old_query = old_score_models.PrimeVerifiedUser.objects.filter(student__year__gte=2024).order_by('id').annotate(
        created_at=F('timestamp'),
    )
    for old_query in qs_old_query:
        student_expr = {
            'psat__year': old_query.student.year,
            'psat__round': old_query.student.round,
            'name': old_query.student.name,
            'serial': old_query.student.serial,
            'password': old_query.student.password,
        }
        lookup_expr = {
            'user_id': old_query.user_id,
        }
        update_expr = {
            'created_at': old_query.created_at,
        }

        new_student = new_prime_models.ResultStudent.objects.get(**student_expr)

        try:
            new_query = new_prime_models.ResultRegistry.objects.get(
                student=new_student, **lookup_expr)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in update_expr.items()
            )
            if fields_not_match:
                for fld, val in update_expr.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except new_prime_models.ResultRegistry.DoesNotExist:
            list_create.append(new_prime_models.ResultRegistry(
                student=new_student, **lookup_expr, **update_expr))
    update_fields = ['user', 'student', 'created_at']
    bulk_create_or_update(new_prime_models.ResultRegistry, list_create, list_update, update_fields)


def update_result_answer_model():
    qs_old_query = old_score_models.PrimeAnswer.objects.filter(student__year__gte=2024).order_by('id').annotate(
        created_at=F('timestamp'),
    )
    count_update = 0
    count_create = 0
    for old_query in qs_old_query:
        subject = old_query.prime.subject.abbr
        psat_expr = {
            'year': old_query.student.year,
            'round': old_query.student.round,
        }
        student_expr = {
            'psat__year': old_query.student.year,
            'psat__round': old_query.student.round,
            'name': old_query.student.name,
            'serial': old_query.student.serial,
            'password': old_query.student.password,
        }

        new_psat = new_prime_models.Psat.objects.get(**psat_expr)
        new_student = new_prime_models.ResultStudent.objects.get(**student_expr)

        list_update = []
        list_create = []
        for number in range(1, 41):

            try:
                new_problem = new_prime_models.Problem.objects.get(psat=new_psat, subject=subject, number=number)
            except new_prime_models.Problem.DoesNotExist:
                new_problem = None

            answer = None
            if new_problem:
                answer = getattr(old_query, f'prob{number}')

            if answer is not None:
                try:
                    new_query = new_prime_models.ResultAnswer.objects.get(student=new_student, problem=new_problem)
                    if new_query.answer != answer:
                        new_query.answer = answer
                        list_update.append(new_query)
                        count_update += 1
                except new_prime_models.ResultAnswer.DoesNotExist:
                    list_create.append(new_prime_models.ResultAnswer(
                        student=new_student, problem=new_problem, answer=answer))
                    count_create += 1
        update_fields = ['student', 'problem', 'answer']
        # bulk_create_or_update(new_prime_models.ResultRegistry, list_create, list_update, update_fields)
        try:
            with transaction.atomic():
                if list_create:
                    new_prime_models.ResultAnswer.objects.bulk_create(list_create)
                    message = f'Successfully created {len(list_create)} ResultAnswer instances.'
                elif list_update:
                    new_prime_models.ResultAnswer.objects.bulk_update(list_update, list(update_fields))
                    message = f'Successfully updated {len(list_update)} ResultAnswer instances.'
                else:
                    message = f'No changes were made to ResultAnswer instances.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'Error occurred.'
        print(message)

    if count_create:
        message = f'Successfully created {count_create} ResultAnswer instances.'
    elif count_update:
        message = f'Successfully updated {count_update} ResultAnswer instances.'
    else:
        message = f'No changes were made to ResultAnswer instances.'
    print(message)


def update_result_answer_count_model(answer_count_model, rank_type=''):
    list_update = []
    list_create = []

    lookup_field = f'student__rank_total__sum'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants_function = F('student__rank_total__participants')

    lookup_exp = {}
    if rank_type == 'top':
        lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
    elif rank_type == 'mid':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
    elif rank_type == 'low':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

    answer_distribution = (
        new_prime_models.ResultAnswer.objects.filter(**lookup_exp)
        .values('problem_id', 'answer')
        .annotate(count=Count('id'))
        .order_by('problem_id', 'answer')
    )
    organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

    for entry in answer_distribution:
        problem_id = entry['problem_id']
        answer = entry['answer']
        count = entry['count']
        organized_distribution[problem_id][answer] = count

    count_fields = [
        'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
    ]
    for problem_id, answers_original in organized_distribution.items():
        answers = {'count_multiple': 0}
        for answer, count in answers_original.items():
            if answer <= 5:
                answers[f'count_{answer}'] = count
            else:
                answers['count_multiple'] = count
        answers['count_sum'] = sum(answers[fld] for fld in count_fields)

        try:
            new_query = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(
                getattr(new_query, fld) != val for fld, val in answers.items()
            )
            if fields_not_match:
                for fld, val in answers.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except answer_count_model.DoesNotExist:
            list_create.append(new_prime_models.ResultAnswerCount(problem_id=problem_id, **answers))
    update_fields = [
        'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple', 'count_sum'
    ]
    bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def update_result_score():
    list_update = []
    list_create = []
    subject_list = ['헌법', '언어', '자료', '상황']
    field_list = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'average']

    qs_student = new_prime_models.ResultStudent.objects.order_by('id')
    for student in qs_student:
        result_score_instance, _ = new_prime_models.ResultScore.objects.get_or_create(student=student)

        score_list = []
        fields_not_match = []
        for idx, subject in enumerate(subject_list):
            problem_count = 25 if subject == '헌법' else 40
            correct_count = 0

            qs_result_answer = new_prime_models.ResultAnswer.objects.filter(
                student=student, problem__subject=subject).select_related('problem')
            for result_answer in qs_result_answer:
                answer_correct = result_answer.problem.answer
                answer_student = result_answer.answer
                if answer_correct <= 5:
                    correct_count += 1 if answer_student == answer_correct else 0
                else:
                    answer_correct_list = [int(digit) for digit in str(answer_correct)]
                    correct_count += 1 if answer_student in answer_correct_list else 0

            score = correct_count * 100 / problem_count
            score_list.append(score)
            fields_not_match.append(getattr(result_score_instance, f'subject_{idx}') != score)

        score_sum = 0
        for idx, score in enumerate(score_list):
            score_sum += score if idx > 0 else 0
        average = round(score_sum / 3, 1)

        fields_not_match.append(result_score_instance.sum != score_sum)
        fields_not_match.append(result_score_instance.average != average)

        if any(fields_not_match):
            for idx, score in enumerate(score_list):
                setattr(result_score_instance, f'subject_{idx}', score)
            result_score_instance.sum = score_sum
            result_score_instance.average = average
            list_update.append(result_score_instance)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average']
    bulk_create_or_update(new_prime_models.ResultScore, list_create, list_update, update_fields)


def update_result_rank(result_rank_model, stat_type: str):
    list_update = []
    list_create = []

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {f'rank_data_subject_{idx}': rank_func(f'score__subject_{idx}') for idx in range(4)}
    annotate_dict['rank_data_average'] = rank_func('score__average')

    qs_student = new_prime_models.ResultStudent.objects.order_by('id')
    for student in qs_student:
        rank_list = qs_student.filter(psat=student.psat)
        if stat_type == 'department':
            rank_list = rank_list.filter(category=student.category)
        rank_list = rank_list.annotate(**annotate_dict)
        result_rank_instance, _ = result_rank_model.objects.get_or_create(student=student)
        participants = rank_list.count()

        fields_not_match = []
        for row in rank_list:
            if row.id == student.id:
                for idx in range(4):
                    fields_not_match.append(
                        getattr(result_rank_instance, f'subject_{idx}') != getattr(row, f'rank_data_subject_{idx}')
                    )
                fields_not_match.append(result_rank_instance.average != row.rank_data_average)
                fields_not_match.append(result_rank_instance.participants != participants)

                if any(fields_not_match):
                    for idx in range(4):
                        setattr(result_rank_instance, f'subject_{idx}', getattr(row, f'rank_data_subject_{idx}'))
                    result_rank_instance.average = row.rank_data_average
                    result_rank_instance.participants = participants
                    list_update.append(result_rank_instance)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'participants']
    bulk_create_or_update(result_rank_model, list_create, list_update, update_fields)


def run(*args):
    if not args:
        raise CommandError(
            f"This script requires arguments. Please provide the necessary arguments.\n"
            f"ex) --script-args all"
        )
    elif 'all' in args:
        update_problem_model()
        update_result_student_model()
        update_result_registry_model()
        update_result_answer_model()
        update_result_answer_count_model(new_prime_models.ResultAnswerCount)
        update_result_score()
        update_result_rank(new_prime_models.ResultRankTotal, 'total')
        update_result_rank(new_prime_models.ResultRankCategory, 'department')
        update_result_answer_count_model(new_prime_models.ResultAnswerCountTopRank, 'top')
        update_result_answer_count_model(new_prime_models.ResultAnswerCountMidRank, 'mid')
        update_result_answer_count_model(new_prime_models.ResultAnswerCountLowRank, 'low')
    elif 'problem' in args:
        update_problem_model()
    elif 'student' in args:
        update_result_student_model()
    elif 'registry' in args:
        update_result_registry_model()
    elif 'answer' in args:
        update_result_answer_model()
    elif 'answer_count' in args:
        update_result_answer_count_model(new_prime_models.ResultAnswerCount)
    elif 'score' in args:
        update_result_score()
    elif 'rank_total' in args:
        update_result_rank(new_prime_models.ResultRankTotal, 'total')
    elif 'rank_department' in args:
        update_result_rank(new_prime_models.ResultRankCategory, 'department')
    elif 'answer_count_by_rank' in args:
        update_result_answer_count_model(new_prime_models.ResultAnswerCountTopRank, 'top')
        update_result_answer_count_model(new_prime_models.ResultAnswerCountMidRank, 'mid')
        update_result_answer_count_model(new_prime_models.ResultAnswerCountLowRank, 'low')
