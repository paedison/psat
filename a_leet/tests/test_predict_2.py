import pytest
from django.test import Client
from freezegun import freeze_time


@pytest.fixture
def logged_client(test_user):
    client = Client()
    client.force_login(test_user)
    return client


def test_warning_without_predict_leet(logged_client, base_data):
    for url in base_data['urls'].values():
        response = logged_client.get(url)
        assert '합격 예측 대상 시험이 아닙니다.' in response.content.decode('utf-8')


def test_warning_without_student_by_time(logged_client, predict_data):
    test_time = predict_data['test_time']
    with freeze_time(test_time['before_exam']):
        response = logged_client.get(predict_data['urls']['detail'])
        assert '시험 시작 전입니다.' in response.content.decode('utf-8')
    with freeze_time(test_time['after_subject_0_end']):
        response = logged_client.get(predict_data['urls']['detail'])
        assert '등록된 수험정보가 없습니다.' in response.content.decode('utf-8')

        response = logged_client.get(predict_data['urls']['answer_input_0'])
        assert '수험 정보를 입력해주세요.' in response.content.decode('utf-8')


def test_warning_with_student_by_time(logged_client, predict_data, student):
    test_time = predict_data['test_time']
    with freeze_time(test_time['before_exam']):
        response = logged_client.get(predict_data['urls']['detail'])
        assert '시험 시작 전입니다.' in response.content.decode('utf-8')
    with freeze_time(test_time['after_subject_0_end']):
        response = logged_client.get(predict_data['urls']['register'])
        assert '등록된 수험정보가 존재합니다.' in response.content.decode('utf-8')


def test_register_page(logged_client, predict_data):
    test_time = predict_data['test_time']

    response = logged_client.post(predict_data['urls']['register'], {
        'serial': '9999',
        'name': '홍길동',
        'password': '1234',
    })
    assert response.status_code == 302

    with freeze_time(test_time['after_subject_0_end']):
        response = logged_client.get(predict_data['urls']['detail'])
        assert '등록된 수험정보가 없습니다.' not in response.content.decode()

        assert predict_data['urls']['answer_input_0'] in response.content.decode()
        assert predict_data['urls']['answer_input_1'] not in response.content.decode()
