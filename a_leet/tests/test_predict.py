import datetime
import json
import random
from dataclasses import dataclass

from django.http import HttpResponse
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from a_leet.utils.common_utils import LeetData, ModelData
from common.models import User

NOW = timezone.now()
TEST_TIME = {
    'before_exam': NOW - datetime.timedelta(minutes=10),
    'after_subject_0_end': NOW + datetime.timedelta(minutes=100),
    'after_subject_1_end': NOW + datetime.timedelta(minutes=250),
    'waiting_answer_predict': NOW + datetime.timedelta(minutes=325),
    'waiting_answer_official': NOW + datetime.timedelta(minutes=375),
    'during_predicting': NOW + datetime.timedelta(minutes=425),
}


@dataclass(kw_only=True)
class SetUpPredictData:
    def __post_init__(self):
        self._model = ModelData()
        self._leet = self._model.leet.objects.get(year=2026)
        self._leet_data = LeetData(_leet=self._leet)
        self._subject_vars = self._leet_data.subject_vars
        self.EXAM_TIME = {
            'exam_started_at': NOW,
            'exam_finished_at': NOW + datetime.timedelta(minutes=300),
            'answer_predict_opened_at': NOW + datetime.timedelta(minutes=350),
            'answer_official_opened_at': NOW + datetime.timedelta(minutes=400),
            'predict_closed_at': NOW + datetime.timedelta(minutes=450),
        }

    def create_predict_leet(self):
        return self._model.predict_leet.objects.create(
            leet=self._leet,
            is_active=True,
            exam_started_at=self.EXAM_TIME['exam_started_at'],
            exam_finished_at=self.EXAM_TIME['exam_finished_at'],
            answer_predict_opened_at=self.EXAM_TIME['answer_predict_opened_at'],
            answer_official_opened_at=self.EXAM_TIME['answer_official_opened_at'],
            predict_closed_at=self.EXAM_TIME['predict_closed_at'],
        )

    def create_problems(self):
        model = self._model.problem
        list_create = []
        for subject, (_, _, _, problem_count) in self._subject_vars.items():
            for number in range(1, problem_count + 1):
                list_create.append(model(leet=self._leet, subject=subject, number=number))
        model.objects.bulk_create(list_create)

    def create_statistics(self):
        model = self._model.statistics
        list_create = []
        for aspiration in self._model.aspirations:
            list_create.append(model(leet=self._leet, aspiration=aspiration))
        model.objects.bulk_create(list_create)

    def create_answer_count(self):
        problems = self._model.problem.objects.filter(leet=self._leet).order_by('id')
        model_list = self._model.ac_model_set
        for model in model_list.values():
            list_create = []
            for problem in problems:
                list_create.append(model(problem=problem))
            model.objects.bulk_create(list_create)

    def get_answer_input_url(self, subject_field):
        return reverse('leet:predict-answer-input', args=[self._leet.id, subject_field])

    def get_answer_confirm_url(self, subject_field):
        return reverse('leet:predict-answer-confirm', args=[self._leet.id, subject_field])


class PredictFlowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        _model = ModelData()
        cls._model = ModelData()

        user = User.objects.create_user(email='test@test.com', username='testuser', password='password123!')
        leet = _model.leet.objects.create(year=2026)
        _setup = SetUpPredictData()

        cls._user = user
        cls._leet = leet
        cls._predict_leet = _setup.create_predict_leet()
        cls._answer_input_url_0 = _setup.get_answer_input_url('subject_0')
        cls._answer_input_url_1 = _setup.get_answer_input_url('subject_1')
        cls._answer_confirm_url_0 = _setup.get_answer_confirm_url('subject_0')
        cls._answer_confirm_url_1 = _setup.get_answer_confirm_url('subject_1')

        cls._leet_data = LeetData(_leet=leet)
        _setup.create_problems()
        _setup.create_statistics()
        _setup.create_answer_count()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self._user)

    def create_student(self):
        # 수험정보 입력
        response: HttpResponse = self.client.post(reverse('leet:predict-register'), {
            'serial': '9999',
            'name': '홍길동',
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self._model.student.objects.filter(user=self._user, leet=self._leet).exists())

        self._student = self._model.student.objects.get(user=self._user, leet=self._leet)
        self.assertEqual(self._student.serial, '9999')
        self.assertEqual(self._student.name, '홍길동')

    def get_detail_response(self) -> HttpResponse:
        return self.client.get(reverse('leet:predict-detail', args=[self._leet.id]))

    def get_answer_page_response(self, page_type: str, field_idx: int) -> HttpResponse:
        url = getattr(self, f'_answer_{page_type}_url_{field_idx}')
        return self.client.get(url)

    @freeze_time(TEST_TIME['before_exam'])
    def test_01_detail_page_before_exam(self):
        detail_response = self.get_detail_response()
        self.assertContains(detail_response, '시험 시작 전입니다.')

    def get_response_for_detail_page_after_test(self):
        response = self.get_detail_response()
        self.assertContains(response, '등록된 수험정보가 없습니다.')

        self.create_student()
        response = self.get_detail_response()
        self.assertNotContains(response, '등록된 수험정보가 없습니다.')

        self.assertContains(response, '답안을 제출해주세요.')
        self.assertContains(response, '미제출')
        self.assertContains(response, self._answer_input_url_0)
        return response

    @freeze_time(TEST_TIME['after_subject_0_end'])
    def test_02_detail_page_after_subject_0_end(self):
        response = self.get_response_for_detail_page_after_test()
        self.assertNotContains(response, self._answer_input_url_1)

    @freeze_time(TEST_TIME['after_subject_1_end'])
    def test_03_detail_page_after_subject_1_end(self):
        response = self.get_response_for_detail_page_after_test()
        self.assertContains(response, self._answer_input_url_1)

    @freeze_time(TEST_TIME['after_subject_0_end'])
    def test_04_answer_input_page_after_subject_0_end(self):
        response = self.get_answer_page_response('input', 0)
        self.assertContains(response, '수험 정보를 입력해주세요.')

        self.create_student()
        response = self.get_answer_page_response('input', 0)
        self.assertNotContains(response, '수험 정보를 입력해주세요.')

        number = 1
        answer = 5
        response = self.client.post(self._answer_input_url_0, data={'number': number, 'answer': answer})
        answer_data_set = json.loads(response.client.cookies.get('answer_data_set').value)
        self.assertIn('answer_data_set', response.client.cookies)
        self.assertEqual(answer_data_set['subject_0'][number - 1], answer)

    def proceed_test_answer_confirm(self, sub: str):
        subject_vars = self._leet_data.subject_vars
        subject, field, field_idx, problem_count = subject_vars[sub]
        answer_data_set = {f'subject_{field_idx}': [random.randint(1, 5) for _ in range(problem_count)]}
        self.client.cookies['answer_data_set'] = json.dumps(answer_data_set)

        response = self.client.post(getattr(self, f'_answer_confirm_url_{field_idx}'))
        self.assertEqual(response.status_code, 200)

    @freeze_time(TEST_TIME['after_subject_0_end'])
    def test_05_answer_confirm_for_subject_0(self):
        self.create_student()
        self.proceed_test_answer_confirm('언어')

    @freeze_time(TEST_TIME['after_subject_1_end'])
    def test_06_answer_confirm_for_subject_1(self):
        self.create_student()
        self.proceed_test_answer_confirm('추리')

    @freeze_time(TEST_TIME['waiting_answer_predict'])
    def test_07_answer_confirm_for_subject_1(self):
        subject_vars = self._leet_data.subject_vars

        self.create_student()
        self.proceed_test_answer_confirm('언어')
        self.proceed_test_answer_confirm('추리')

        qs_student_answer = self._model.answer.objects.filter(student=self._student)
        student_answer_dict = {qs_sa.problem: qs_sa for qs_sa in qs_student_answer}
        problem_count = sum([cnt for (_, _, _, cnt) in subject_vars.values()])
        self.assertEqual(qs_student_answer.count(), problem_count)

        qs_answer_count = self._model.ac_all.objects.filter(problem__leet=self._leet)
        for qs_ac in qs_answer_count:
            ans = student_answer_dict[qs_ac.problem].answer
            self.assertEqual(getattr(qs_ac, f'count_{ans}'), 1)

    # def test_05_announcement_stage_by_time(self):
    #     self.create_student()
    #     stages = [
    #         ('시험 전', 10, '시험 시작 전입니다'),
    #         ('시험 중', -100, '답안을 제출해주세요'),  # 링크만 표시
    #         ('답안 수집 중', -325, '답안을 제출해주세요'),
    #         ('예상답안 제공 이후', -375, '답안을 제출해주세요'),
    #         ('공식답안 제공 이후', -425, '답안을 제출해주세요'),
    #     ]
    #
    #     for desc, offset, expected_text in stages:
    #         with self.subTest(단계=desc):
    #             self._predict_leet.exam_started_at = timezone.now() + datetime.timedelta(minutes=offset)
    #             self._predict_leet.exam_finished_at = timezone.now() + datetime.timedelta(minutes=offset)
    #             self._predict_leet.answer_predict_opened_at = timezone.now() + datetime.timedelta(minutes=offset)
    #             self._predict_leet.answer_official_opened_at = timezone.now() + datetime.timedelta(minutes=offset)
    #             self._predict_leet.save()
    #             response = self.client.get(reverse('leet:predict-detail', args=[self._leet.id]))
    #             print(response.content.decode('utf-8'))
    #             self.assertContains(response, expected_text)
