from django.db.models import F

from predict import models as predict_models
from score import models as score_models


def run():
    answer_model = predict_models.Answer
    answer_count_model = predict_models.AnswerCount
    answer_count_top_rank_model = predict_models.AnswerCountTopRank
    answer_count_model_name = 'AnswerCount'

    answer_count_keys = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total']

    def add_update_list(
            update_list: list,
            update_count: int,
            problem_id: int,
            result: dict,
            count_total: int,
    ) -> (list, int):
        instance = answer_count_model.objects.get(problem_id=problem_id)
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
        return update_list, update_count

    def add_create_list(
            create_list: list,
            create_count: int,
            problem_id: int,
            result: dict,
            count_total: int,
    ) -> (list, int):
        for key, value in result.copy().items():
            if key in answer_count_keys:
                continue
            result.pop(key)
        result['problem_id'] = problem_id
        result['count_total'] = count_total
        create_list.append(answer_count_model(**result))
        create_count += 1
        return create_list, create_count

    def update_answer_count(sub):
        update_list = []
        create_list = []
        update_count = 0
        create_count = 0

        problem_numbers = 25 if sub == '헌법' else 40
        prime_id = category_model.objects.get(
            year=exam_year, round=exam_round, subject__abbr=sub).id
        problem_ids = list(
            problem_model.objects.filter(prime_id=prime_id).values_list('id', flat=True)
        )
        answers = answer_model.objects.filter(prime_id=prime_id)
        count_total = answers.count()

        for i in range(0, problem_numbers):
            prob_num = f'prob{i + 1}'
            target_counts = list(
                answers.values(prob_num).annotate(count=Count(prob_num)).order_by(prob_num)
            )
            result = {}
            for target in target_counts:
                key = f'count_{target[prob_num]}'
                value = target['count']
                result[key] = value
            try:
                update_list, update_count = add_update_list(
                    update_list, update_count, problem_ids[i], result, count_total)
            except answer_count_model.DoesNotExist:
                create_list, create_count = add_create_list(
                    create_list, create_count, problem_ids[i], result, count_total)
        try:
            with transaction.atomic():
                if create_list:
                    answer_count_model.objects.bulk_create(create_list)
                    message = f'Successfully {create_count} {answer_count_model_name} {sub} instances created.'
                elif update_list:
                    answer_count_model.objects.bulk_update(update_list, answer_count_keys)
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

# def run():
#     top_ranker_student_qs = (
#         predict_models.Student.objects.filter(statistics__rank_ratio_total_psat__lte=20)
#     )
#     top_ranker_student_ids = top_ranker_student_qs.values_list('id', flat=True)
#
#     answer_fields = ['id', 'sub', 'student_id']
#     for i in range(1, 41):
#         answer_fields.append(f'prob{i}')
#
#     top_ranker_answer_qs = (
#         predict_models.Answer.objects.filter(student_id__in=top_ranker_student_ids)
#         .values(*answer_fields)
#     )
#     # print(top_ranker_answer_qs[1])
#
#     answer_count_qs = (
#         predict_models.AnswerCount.objects
#         .filter(exam__category='PSAT', exam__year=2024, exam__ex='행시', exam__round=0)
#         .order_by('sub', 'number')
#     )
#     correct_answer_list = answer_count_qs.values('sub', 'number', correct_answer=F('answer'))
#     correct_answer_dict = {
#         '헌법': {}, '언어': {}, '자료': {}, '상황': {}
#     }
#     for p in correct_answer_list:
#         sub = p['sub']
#         number = p['number']
#         correct_answer = p['correct_answer']
#         correct_answer_dict[sub][f'prob{number}'] = correct_answer
#     # print(correct_answer_dict)
#
#     top_ranker_result = {
#         '헌법': {}, '언어': {}, '자료': {}, '상황': {}
#     }
#     for r in top_ranker_answer_qs:
#         sub = r['sub']
#         number = r['number']
#         correct_answer = r['correct_answer']
#         # if sub == '언어':
#         #     for i in range(1, 41):
#
