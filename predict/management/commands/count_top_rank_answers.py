import traceback

import django.db.utils
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from predict import models as predict_models


class Command(BaseCommand):
    help = 'Count Answers'

    def add_arguments(self, parser):
        parser.add_argument('category', type=str, help='Category: ex) PSAT, Prime')
        parser.add_argument('year', type=str, help='Year: ex) 2024')
        parser.add_argument('ex', type=str, help='Ex: ex) 행시, 프모')
        parser.add_argument('round', type=str, help='Round: ex) 0, 1')

    def handle(self, *args, **kwargs):
        exam_category = kwargs['category']
        exam_year = kwargs['year']
        exam_ex = kwargs['ex']
        exam_round = kwargs['round']
        exam = predict_models.Exam.objects.get(
            category=exam_category,
            year=exam_year,
            ex=exam_ex,
            round=exam_round,
        )

        answer_model = predict_models.Answer
        answer_count_model = predict_models.AnswerCount
        answer_count_top_rank_model = predict_models.AnswerCountTopRank
        answer_count_model_name = 'AnswerCount'

        answer_count_keys = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total']

        def update_answer_count(sub):
            update_list = []
            create_list = []
            update_count = 0
            create_count = 0

            answer_counts = answer_count_model.objects.filter(exam=exam, sub=sub).order_by('number').values('answer')

            target_answers = (
                answer_model.objects.filter(
                    sub=sub,
                    student__exam=exam,
                    student__statistics__rank_ratio_total_psat__lte=0.2,
                )
            )
            count_total = target_answers.count()

            problem_numbers = 25 if sub == '헌법' else 40
            for i in range(0, problem_numbers):
                prob_num = f'prob{i + 1}'
                target_counts = target_answers.values(prob_num).annotate(count=Count(prob_num)).order_by(prob_num)
                result = {}
                for target in target_counts:
                    key = f'count_{target[prob_num]}'
                    value = target['count']
                    result[key] = value
                try:
                    instance = answer_count_top_rank_model.objects.get(
                        exam=exam,
                        sub=sub,
                        number=i + 1,
                        answer=answer_counts[i]['answer'],
                    )
                    fields_not_match = []
                    for key, value in result.items():
                        try:
                            answer_value = getattr(instance, key)
                        except AttributeError:
                            answer_value = None
                        if answer_value is not None:
                            fields_not_match.append(answer_value != value)
                    if any(fields_not_match):
                        for key, value in result.items():
                            setattr(instance, key, value)
                        instance.count_total = count_total
                        update_list.append(instance)
                        update_count += 1
                except answer_count_top_rank_model.DoesNotExist:
                    for key, value in result.copy().items():
                        if key in answer_count_keys:
                            continue
                        result.pop(key)
                    result['exam'] = exam
                    result['sub'] = sub
                    result['number'] = i + 1
                    result['answer'] = answer_counts[i]['answer']
                    result['count_total'] = count_total
                    create_list.append(answer_count_top_rank_model(**result))
                    create_count += 1
            try:
                with transaction.atomic():
                    if create_list:
                        answer_count_top_rank_model.objects.bulk_create(create_list)
                        message = f'Successfully {create_count} {answer_count_model_name} {sub} instances created.'
                    elif update_list:
                        answer_count_top_rank_model.objects.bulk_update(update_list, answer_count_keys)
                        message = f'Successfully {update_count} {answer_count_model_name} {sub} instances updated.'
                    else:
                        message = f'{answer_count_model_name} {sub} instances already exist.'
            except django.db.utils.IntegrityError:
                traceback_message = traceback.format_exc()
                print(traceback_message)
                message = f'Error occurred in {sub}.'
            self.stdout.write(self.style.SUCCESS(message))

        update_answer_count('언어')
        update_answer_count('자료')
        update_answer_count('상황')
        update_answer_count('헌법')
