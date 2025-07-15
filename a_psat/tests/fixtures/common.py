__all__ = [
    'fixed_now', 'psat_test_exam_info',
    'psat_time_schedule', 'psat_test_time_info', 'psat_subject_vars',
    'psat_test_user_info', 'psat_test_student_info',
]

import datetime

import pytest
from django.utils import timezone


@pytest.fixture(scope='session')
def fixed_now():
    return timezone.now()


@pytest.fixture(scope='session')
def psat_test_exam_info():
    return dict(
        year=2025,
        exam='칠급',
        order=1,
        is_active=True,
    )


@pytest.fixture
def psat_time_schedule(psat_test_exam_info, fixed_now):
    if psat_test_exam_info['exam'] in ['칠급', '칠예', '민경']:
        finish_time = fixed_now + datetime.timedelta(minutes=240)
        return {
            'exam_started_at': fixed_now,
            'exam_finished_at': finish_time,
            'answer_predict_opened_at': fixed_now + datetime.timedelta(minutes=270),
            'answer_official_opened_at': fixed_now + datetime.timedelta(minutes=360),
            'predict_closed_at': fixed_now + datetime.timedelta(minutes=400),

            'exam_1_end_time': fixed_now + datetime.timedelta(minutes=120),
            'exam_2_start_time': fixed_now + datetime.timedelta(minutes=180),
            'exam_2_end_time': finish_time,
        }
    else:
        finish_time = fixed_now + datetime.timedelta(minutes=450)
        return {
            'exam_started_at': fixed_now,
            'exam_finished_at': finish_time,
            'answer_predict_opened_at': fixed_now + datetime.timedelta(minutes=480),
            'answer_official_opened_at': fixed_now + datetime.timedelta(minutes=600),
            'predict_closed_at': fixed_now + datetime.timedelta(minutes=700),

            'exam_1_end_time': fixed_now + datetime.timedelta(minutes=115),
            'exam_2_start_time': fixed_now + datetime.timedelta(minutes=225),
            'exam_2_end_time': fixed_now + datetime.timedelta(minutes=315),
            'exam_3_start_time': fixed_now + datetime.timedelta(minutes=360),
            'exam_3_end_time': finish_time,
        }


@pytest.fixture(scope='session')
def psat_test_time_info(psat_test_exam_info, fixed_now):
    if psat_test_exam_info['exam'] in ['칠급', '칠예', '민경']:
        return {
            'now': fixed_now,
            'before_exam': fixed_now - datetime.timedelta(minutes=10),
            'after_exam_1_end': fixed_now + datetime.timedelta(minutes=130),
            'after_exam_2_end': fixed_now + datetime.timedelta(minutes=190),
            'before_answer_predict_opened': fixed_now + datetime.timedelta(minutes=200),
            'before_answer_official_opened': fixed_now + datetime.timedelta(minutes=300),
            'after_answer_official_opened': fixed_now + datetime.timedelta(minutes=350),
        }
    else:
        return {
            'now': fixed_now,
            'before_exam': fixed_now - datetime.timedelta(minutes=10),
            'after_exam_1_end': fixed_now + datetime.timedelta(minutes=100),
            'after_exam_2_end': fixed_now + datetime.timedelta(minutes=250),
            'before_answer_predict_opened': fixed_now + datetime.timedelta(minutes=325),
            'before_answer_official_opened': fixed_now + datetime.timedelta(minutes=375),
            'after_answer_official_opened': fixed_now + datetime.timedelta(minutes=425),
        }


@pytest.fixture
def psat_subject_vars(psat_test_exam_info):
    if psat_test_exam_info['exam'] in ['칠급', '칠예', '민경']:
        return {
            '언어': ('언어논리', 'subject_1', 1, 25),
            '자료': ('자료해석', 'subject_2', 2, 25),
            '상황': ('상황판단', 'subject_3', 3, 25),
            '평균': ('PSAT 평균', 'average', 4, 75),
        }
    return {
        '헌법': ('헌법', 'subject_0', 0, 25),
        '언어': ('언어논리', 'subject_1', 1, 40),
        '자료': ('자료해석', 'subject_2', 2, 40),
        '상황': ('상황판단', 'subject_3', 3, 40),
        '평균': ('PSAT 평균', 'average', 4, 145),
    }


@pytest.fixture
def psat_test_user_info():
    return dict(
        email='test@test.com',
        username='testuser',
        password='password123!'
    )


@pytest.fixture
def psat_test_student_info():
    return dict(
        unit='7급 국가직(일반)',
        department='7급 국가직(일반)-일반행정',
        serial='9999',
        name='홍길동',
        password='1234',
        prime_id='test_prime_id',
    )


@pytest.fixture
def psat_test_subject():
    return '언어'


@pytest.fixture
def psat_test_subject_tuples(psat_subject_vars, psat_test_subject):
    return psat_subject_vars[psat_test_subject]
