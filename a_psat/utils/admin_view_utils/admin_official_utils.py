from a_psat import models
from . import common_utils


def update_official_problem_count(page_obj):
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
        psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)


def create_official_problem_model_instances(psat, exam):
    list_create = []

    def append_list(problem_count: int, *subject_list):
        for subject in subject_list:
            for number in range(1, problem_count + 1):
                problem_info = {'psat': psat, 'subject': subject, 'number': number}
                common_utils.append_list_create(models.Problem, list_create, **problem_info)

    if exam in ['행시', '입시']:
        append_list(40, '언어', '자료', '상황')
        append_list(25, '헌법')
    elif exam in ['칠급']:
        append_list(25, '언어', '자료', '상황')

    common_utils.bulk_create_or_update(models.Problem, list_create, [], [])
