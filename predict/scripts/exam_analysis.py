from predict import models as predict_models
from score import models as score_models


def run():
    target_student_ids = (
        predict_models.Student.objects.order_by('user_id')
        .filter(exam__category='PSAT', exam__year=2024, exam__ex='행시', exam__round=0)
        .values_list('user_id', flat=True)
    )
    verified_user_qs = (
        score_models.PrimeVerifiedUser.objects.order_by('user_id')
        .filter(user_id__in=target_student_ids, student__year=2024, student__round=5)
    )
    print(list(verified_user_qs.values_list('user_id', flat=True)))

    target_users = {}

    for u in verified_user_qs.values():
        user_id = u['user_id']
        key = f'user_{user_id}'
        if key not in target_users:
            target_users[key] = []
        target_users[key].append(u)

    print(target_users)

    # verified_user_ids = verified_user_qs.values_list('user_id', flat=True)
    # target_student_qs = predict_models.Student.objects.filter(user_id__in=verified_user_ids)
    # for student in target_student_qs:
    #     print(student)
