import pytest
from django.test import Client
from django.db.models import F

from a_psat import models
from common.models import User
from . import factories

pytest_plugins = [
    'a_psat.tests.fixtures.common',
    'a_psat.tests.fixtures.psat',
]


@pytest.fixture
def psat_test_user(db, psat_test_user_info):
    return factories.UserFactory(**psat_test_user_info)


@pytest.fixture
def logged_client(psat_test_user) -> Client:
    client = Client()
    client.force_login(psat_test_user)
    return client


@pytest.fixture
def psat_test_category(
        psat_test_psat: models.Psat,
        psat_test_student_info: dict,
) -> models.PredictCategory:
    unit = psat_test_student_info['unit']
    department = psat_test_student_info['department']
    return factories.PredictCategoryFactory(
        exam=psat_test_psat,
        unit=unit,
        department=department,
        order=1
    )


@pytest.fixture
def psat_test_student(
        psat_test_user: User,
        psat_test_psat: models.Psat,
        psat_test_student_info: dict,
) -> models.PredictStudent:
    unit = psat_test_student_info.pop('unit')
    department = psat_test_student_info.pop('department')
    category = models.PredictCategory.objects.get(unit=unit, department=department)
    return factories.PredictStudentFactory(
        user=psat_test_user,
        psat=psat_test_psat,
        category=category,
        **psat_test_student_info
    )


@pytest.fixture
def psat_test_statistics(psat_test_psat, psat_test_category) -> models.PredictStatistics:
    return factories.PredictStatisticsFactory(
        psat=psat_test_psat,
        department=psat_test_category.department,
    )


@pytest.fixture
def psat_test_score(psat_test_student: models.PredictStudent) -> models.PredictScore:
    return factories.PredictScoreFactory(student=psat_test_student)


@pytest.fixture
def psat_test_rank_total(psat_test_student: models.PredictStudent) -> models.PredictRankTotal:
    return factories.PredictRankTotalFactory(student=psat_test_student)


@pytest.fixture
def psat_test_rank_category(psat_test_student: models.PredictStudent) -> models.PredictRankCategory:
    return factories.PredictRankCategoryFactory(student=psat_test_student)


@pytest.fixture
def psat_test_answer_set(psat_test_student, psat_test_problems, psat_test_subject):
    answer_set = []
    for problem in psat_test_problems:
        if problem.subject == psat_test_subject:
            answer_set.append(factories.PredictAnswerFactory(student=psat_test_student, problem=problem))
    return answer_set


@pytest.fixture
def base_fixture(
        psat_test_time_info: dict,
        psat_test_user: User,
        psat_test_psat: models.Psat,
        psat_subject_vars: dict,
        psat_test_subject_tuples: tuple,
        psat_time_schedule: dict,
        psat_urls: dict,
        psat_test_problems: list,
        psat_test_answer_counts: dict[list],
        psat_test_category: models.PredictCategory,
        psat_test_subject: str
) -> dict:
    return dict(
        test_time=psat_test_time_info,
        user=psat_test_user,
        psat=psat_test_psat,
        subject_vars=psat_subject_vars,
        subject_tuples=psat_test_subject_tuples,
        psat_time_schedule=psat_time_schedule,
        urls=psat_urls,
        problems=psat_test_problems,
        answer_counts=psat_test_answer_counts,
        test_category=psat_test_category,
        test_subject=psat_test_subject,
    )


@pytest.fixture
def predict_fixture(
        base_fixture: dict,
        psat_test_predict_psat: models.PredictPsat,
        psat_test_student_info: dict,
) -> dict:
    return dict(
        base_fixture,
        predict_psat=psat_test_predict_psat,
        student_info=psat_test_student_info,
    )


@pytest.fixture
def student_fixture(
        predict_fixture: dict,
        psat_test_student: models.PredictStudent,
        psat_test_score: models.PredictScore,
        psat_test_rank_total: models.PredictRankTotal,
        psat_test_rank_category: models.PredictRankCategory,
) -> dict:
    return dict(
        predict_fixture,
        student=psat_test_student,
        score=psat_test_score,
        rank_total=psat_test_rank_total,
        rank_category=psat_test_rank_category,
    )


@pytest.fixture
def student_answer_fixture(
        student_fixture: dict,
        psat_test_subject: str,
        psat_test_answer_counts: dict,
        psat_test_answer_set: dict,
) -> dict:
    update_list = []
    for idx, tac in enumerate(psat_test_answer_counts[psat_test_subject]):
        ans_student = psat_test_answer_set[idx].answer
        setattr(tac, f'count{ans_student}', F(f'count{ans_student}') + 1)
        update_list.append(tac)
    models.PredictAnswerCount.objects.bulk_update(
        update_list, ['count_1', 'count_2', 'count_3', 'count_4', 'count_5'])
    return dict(
        student_fixture,
        test_answer_set=psat_test_answer_set,
    )
