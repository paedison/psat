import datetime
from dataclasses import dataclass

import pytest
from django.urls import reverse
from django.utils import timezone

from a_leet import models
from common.models import User
from . import factories


@dataclass
class TestTimeFixture:
    fixed_now: datetime.datetime

    def __post_init__(self):
        self.now = self.fixed_now
        self.before_exam = self.fixed_now - datetime.timedelta(minutes=10)
        self.after_subject_0_end = self.fixed_now + datetime.timedelta(minutes=100)
        self.after_subject_1_end = self.fixed_now + datetime.timedelta(minutes=250)
        self.waiting_answer_predict = self.fixed_now + datetime.timedelta(minutes=325)
        self.waiting_answer_official = self.fixed_now + datetime.timedelta(minutes=375)
        self.during_predicting = self.fixed_now + datetime.timedelta(minutes=425)


@dataclass
class BaseFixture:
    subject_vars: dict
    test_time: TestTimeFixture
    user: User
    leet: models.Leet
    problems: list[models.Problem]
    urls: dict


@dataclass
class PredictFixture:
    base: BaseFixture
    predict_leet: models.PredictLeet

    def __post_init__(self):
        self.subject_vars = self.base.subject_vars
        self.test_time = self.base.test_time
        self.user = self.base.user
        self.leet = self.base.leet
        self.problems = self.base.problems
        self.urls = self.base.urls


@dataclass
class StudentFixture:
    predict_fixture: PredictFixture
    student: models.PredictStudent
    score: models.PredictScore
    rank: models.PredictRank
    student_info: dict

    def __post_init__(self):
        self.subject_vars = self.predict_fixture.subject_vars
        self.test_time = self.predict_fixture.test_time
        self.user = self.predict_fixture.user
        self.leet = self.predict_fixture.leet
        self.problems = self.predict_fixture.problems
        self.urls = self.predict_fixture.urls
        self.predict_leet = self.predict_fixture.predict_leet


@pytest.fixture(scope="session")
def fixed_now():
    return timezone.now()


@pytest.fixture(scope="session")
def test_time(fixed_now):
    return TestTimeFixture(fixed_now)


@pytest.fixture
def subject_vars():
    return {
        '언어': ('언어이해', 'subject_0', 0, 30),
        '추리': ('추리논증', 'subject_1', 1, 40),
    }


@pytest.fixture
def test_user(db):
    return factories.UserFactory(email='test@test.com', username='testuser', password='password123!')


@pytest.fixture
def leet(db):
    return factories.LeetFactory(year=2026)


@pytest.fixture
def problems(leet, subject_vars):
    created = []
    for sub, (_, _, _, count) in subject_vars.items():
        for number in range(1, count + 1):
            created.append(factories.ProblemFactory(leet=leet, subject=sub, number=number))
    return created


@pytest.fixture
def predict_leet(leet, fixed_now):
    return factories.PredictLeetFactory(
        leet=leet,
        exam_started_at=fixed_now,
        exam_finished_at=fixed_now + datetime.timedelta(minutes=300),
        answer_predict_opened_at=fixed_now + datetime.timedelta(minutes=350),
        answer_official_opened_at=fixed_now + datetime.timedelta(minutes=400),
        predict_closed_at=fixed_now + datetime.timedelta(minutes=450),
    )


@pytest.fixture
def statistics(leet):
    return factories.PredictStatisticsFactory.create_batch(3, leet=leet)


@pytest.fixture
def answer_counts(problems):
    created = []
    for problem in problems:
        created.append(factories.PredictAnswerCountFactory(problem=problem))
    return created


@pytest.fixture
def urls(leet):
    return {
        'detail': reverse('leet:predict-detail', args=[leet.id]),
        'register': reverse('leet:predict-register'),
        'answer_input_0': reverse('leet:predict-answer-input', args=[leet.id, 'subject_0']),
        'answer_input_1': reverse('leet:predict-answer-input', args=[leet.id, 'subject_1']),
        'answer_confirm_0': reverse('leet:predict-answer-confirm', args=[leet.id, 'subject_0']),
        'answer_confirm_1': reverse('leet:predict-answer-confirm', args=[leet.id, 'subject_1']),
    }


@pytest.fixture
def student_info():
    return {
        'serial': '9999',
        'name': '홍길동',
        'password': '1234',
    }


@pytest.fixture
def test_student(test_user, leet, student_info):
    return factories.PredictStudentFactory(user=test_user, leet=leet, **student_info)


@pytest.fixture
def test_score(test_student):
    return factories.PredictScoreFactory(student=test_student)


@pytest.fixture
def test_rank(test_student):
    return factories.PredictRankFactory(student=test_student)


@pytest.fixture
def base_fixture(subject_vars, test_time, test_user, leet, problems, urls):
    return BaseFixture(subject_vars, test_time, test_user, leet, problems, urls)


@pytest.fixture
def predict_fixture(base_fixture, predict_leet):
    return PredictFixture(base_fixture, predict_leet)


@pytest.fixture
def student_fixture(predict_fixture, test_student, test_score, test_rank, student_info):
    return StudentFixture(predict_fixture, test_student, test_score, test_rank, student_info)


@pytest.fixture
def student_with_answers(student, problems):
    for problem in problems:
        factories.PredictAnswerFactory(student=student, problem=problem)
    return student
