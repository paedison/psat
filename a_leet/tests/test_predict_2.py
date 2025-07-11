import json
import random

import pytest
from django.test import Client
from freezegun import freeze_time

from a_leet import models


@pytest.fixture
def logged_client(test_user):
    client = Client()
    client.force_login(test_user)
    return client


def test_register_page_error_without_predict_leet(logged_client, base_fixture):
    response = logged_client.get(base_fixture.urls['register'])
    assert '합격 예측 대상 시험이 아닙니다.' in response.content.decode('utf-8')


def test_register_page_error_existing_student(logged_client, student_fixture):
    response = logged_client.get(student_fixture.urls['register'])
    assert '등록된 수험정보가 존재합니다.' in response.content.decode('utf-8')


def test_register_page_error_in_form(logged_client, predict_fixture, student_info):
    register_url = predict_fixture.urls['register']

    # response = logged_client.post(register_url, student_info)
    # assert '이미 등록된 수험번호입니다.' in response.content.decode('utf-8')
    # assert '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.' in response.content.decode('utf-8')

    response = logged_client.post(register_url, dict(**student_info, aspiration_2='강원대학교'))
    assert '1지망을 선택해주세요.' in response.content.decode('utf-8')

    response = logged_client.post(register_url, dict(**student_info, aspiration_1='강원대학교', aspiration_2='강원대학교'))
    assert '1지망과 2지망이 동일합니다.' in response.content.decode('utf-8')

    response = logged_client.post(register_url, dict(**student_info, major='공학'))
    assert '출신대학을 선택해주세요.' in response.content.decode('utf-8')

    response = logged_client.post(register_url, dict(**student_info, gpa='3.0'))
    assert '학점(GPA) 종류를 선택해주세요.' in response.content.decode('utf-8')

    response = logged_client.post(register_url, dict(**student_info, english='700'))
    assert '공인 영어성적 종류를 선택해주세요.' in response.content.decode('utf-8')


def test_register_page_success(logged_client, predict_fixture, student_info):
    response = logged_client.post(predict_fixture.urls['register'], student_info)
    assert response.status_code == 302

    student = models.PredictStudent.objects.get(user=predict_fixture.user, leet=predict_fixture.leet)
    assert student.serial == student_info['serial']
    assert student.name == student_info['name']
    assert student.password == student_info['password']


def test_register_page(logged_client, predict_fixture):
    test_time = predict_fixture.test_time

    response = logged_client.post(predict_fixture.urls['register'], {
        'serial': '9999',
        'name': '홍길동',
        'password': '1234',
    })
    assert response.status_code == 302

    with freeze_time(test_time.after_subject_0_end):
        response = logged_client.get(predict_fixture.urls['detail'])
        assert '등록된 수험정보가 없습니다.' not in response.content.decode()

        assert predict_fixture.urls['answer_input_0'] in response.content.decode()
        assert predict_fixture.urls['answer_input_1'] not in response.content.decode()


def test_warning_message_without_predict_leet(logged_client, base_fixture):
    for url in base_fixture.urls.values():
        response = logged_client.get(url)
        assert '합격 예측 대상 시험이 아닙니다.' in response.content.decode('utf-8')


def test_warning_message_without_student_by_time(logged_client, predict_fixture):
    test_time = predict_fixture.test_time

    with freeze_time(test_time.before_exam):
        response = logged_client.get(predict_fixture.urls['detail'])
        assert '시험 시작 전입니다.' in response.content.decode('utf-8')

    with freeze_time(test_time.after_subject_0_end):
        response = logged_client.get(predict_fixture.urls['detail'])
        assert '등록된 수험정보가 없습니다.' in response.content.decode('utf-8')

        response = logged_client.get(predict_fixture.urls['answer_input_0'])
        assert '수험 정보를 입력해주세요.' in response.content.decode('utf-8')


def test_warning_message_with_student_by_time(logged_client, student_fixture):
    test_time = student_fixture.test_time

    with freeze_time(test_time.before_exam):
        response = logged_client.get(student_fixture.urls['detail'])
        assert '시험 시작 전입니다.' in response.content.decode('utf-8')

    with freeze_time(test_time.after_subject_0_end):
        response = logged_client.get(student_fixture.urls['register'])
        assert '등록된 수험정보가 존재합니다.' in response.content.decode('utf-8')

        response = logged_client.get(student_fixture.urls['detail'])
        assert '답안을 제출해주세요.' in response.content.decode('utf-8')
        assert '미제출' in response.content.decode('utf-8')


def test_answer_input_page(logged_client, student_fixture):
    test_time = student_fixture.test_time

    with freeze_time(test_time.after_subject_0_end):
        number = 1
        answer = 5
        response = logged_client.post(
            student_fixture.urls['answer_input_0'],
            data={'number': number, 'answer': answer},
        )
        assert 'answer_data_set' in response.client.cookies

        answer_data_set = json.loads(response.client.cookies.get('answer_data_set').value)
        assert answer_data_set['subject_0'][number - 1] == answer


def test_answer_confirm_page(logged_client, student_fixture):
    subject_vars = student_fixture.subject_vars
    test_time = student_fixture.test_time
    leet = student_fixture.leet
    student = student_fixture.student

    with freeze_time(test_time.after_subject_1_end):
        for sub, (_, subject_fld, field_idx, problem_count) in subject_vars.items():
            answer_data_set = {f'{subject_fld}': [random.randint(1, 5) for _ in range(problem_count)]}
            logged_client.cookies['answer_data_set'] = json.dumps(answer_data_set)

            response = logged_client.post(student_fixture.urls[f'answer_confirm_{field_idx}'])
            assert response.status_code == 200
            if field_idx != len(subject_vars) - 1:
                assert student_fixture.urls[f'answer_input_{field_idx + 1}'] in response.content.decode()
            else:
                assert student_fixture.urls['detail'] in response.content.decode()

            qs_student_answer = models.PredictAnswer.objects.filter(student=student, problem__subject=sub)
            student_answer_dict = {qs_sa.problem: qs_sa for qs_sa in qs_student_answer}
            assert qs_student_answer.count() == problem_count

            qs_answer_count = models.PredictAnswerCount.objects.filter(problem__leet=leet)
            for qs_ac in qs_answer_count:
                ans = student_answer_dict[qs_ac.problem].answer
                assert getattr(qs_ac, f'count_{ans}') == 1


# def test_detail_page(logged_client, student_fixture):
