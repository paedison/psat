import datetime
import pytest
from django.urls import reverse

from django.utils import timezone

from . import factories


@pytest.fixture(scope="session")
def fixed_now():
    return timezone.now()


@pytest.fixture(scope="session")
def test_time(fixed_now):
    return {
        'now': fixed_now,
        'before_exam': fixed_now - datetime.timedelta(minutes=10),
        'after_subject_0_end': fixed_now + datetime.timedelta(minutes=100),
        'after_subject_1_end': fixed_now + datetime.timedelta(minutes=250),
        'waiting_answer_predict': fixed_now + datetime.timedelta(minutes=325),
        'waiting_answer_official': fixed_now + datetime.timedelta(minutes=375),
        'during_predicting': fixed_now + datetime.timedelta(minutes=425),
    }


@pytest.fixture
def test_user(db):
    return factories.UserFactory(email='test@test.com', username='testuser', password='password123!')


@pytest.fixture
def leet(db):
    return factories.LeetFactory(year=2026)


@pytest.fixture
def problems(leet):
    subject_count = {'언어': 30, '추리': 40}
    created = []
    for subject, count in subject_count.items():
        created += factories.ProblemFactory.create_batch(count, leet=leet, subject=subject)
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
    for problem in problems:
        factories.PredictAnswerCountFactory(problem=problem)
    return True


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
def base_data(test_time, test_user, leet, problems, urls):
    return {
        'test_time': test_time,
        'user': test_user,
        'leet': leet,
        'problems': problems,
        'urls': urls,
    }


@pytest.fixture
def predict_data(test_time, test_user, leet, problems, urls, predict_leet):
    return {
        'test_time': test_time,
        'user': test_user,
        'leet': leet,
        'problems': problems,
        'urls': urls,
        'predict_leet': predict_leet,
        # 'statistics': statistics,
        # 'answer_counts': answer_counts,
    }


@pytest.fixture
def student(test_user, leet):
    return factories.PredictStudentFactory(
        user=test_user,
        leet=leet,
        serial='9999',
        name='홍길동',
        password='1234',
    )


@pytest.fixture
def student_with_answers(student, problems):
    for problem in problems:
        factories.PredictAnswerFactory(student=student, problem=problem)
    return student

# @pytest.mark.django_db
# @pytest.fixture(scope='module')
# def setup_predict_data(django_db_blocker):
#     # DB 접근 허용
#     with django_db_blocker.unblock():
#         setup = SetUpPredictData()
#         setup.create_predict_leet()
#         setup.create_problems()
#         setup.create_statistics()
#         setup.create_answer_count()
#     return setup
#
#
# @pytest.fixture
# def predict_user(db):
#     return User.objects.create_user(
#         email='test@test.com',
#         username='testuser',
#         password='password123!'
#     )
