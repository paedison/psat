from a_psat import models
from a_psat.utils.decorators import *
from a_psat.utils.modify_models_methods import *


@for_normal_views
def create_new_custom_record(request, problem, model, **kwargs):
    base_info = {'problem': problem, 'user': request.user, 'is_active': True}
    latest_record = model.objects.filter(**base_info).first()
    if latest_record:
        if isinstance(latest_record, models.ProblemLike):
            kwargs = {'is_liked': not latest_record.is_liked}
        with transaction.atomic():
            new_record = model.objects.create(**base_info, **kwargs)
            latest_record.is_active = False
            latest_record.save()
    else:
        new_record = model.objects.create(**base_info, **kwargs)
    return new_record


@for_normal_views
def create_new_collection(request, form):
    my_collection = form.save(commit=False)
    collection_counts = models.ProblemCollection.objects.filter(user=request.user, is_active=True).count()
    my_collection.user = request.user
    my_collection.order = collection_counts + 1
    my_collection.save()


@for_admin_views
@with_bulk_create_or_update()
def create_official_problem_model_instances(psat, exam):
    list_create, list_update = [], []

    def append_list(problem_count: int, *subject_list):
        for subject in subject_list:
            for number in range(1, problem_count + 1):
                problem_info = {'psat': psat, 'subject': subject, 'number': number}
                append_list_create(models.Problem, list_create, **problem_info)

    if exam in ['행시', '입시']:
        append_list(40, '언어', '자료', '상황')
        append_list(25, '헌법')
    elif exam in ['칠급']:
        append_list(25, '언어', '자료', '상황')

    return models.Problem, list_create, list_update, []
