import random

from django.test import TestCase
from django.urls import reverse

from a_common.constants import icon_set
from a_common.models import User
from .models import (
    Student, StudentAnswer, Department, SubmittedAnswer,
    # Problem,
    # ProblemLike, ProblemRate, ProblemSolve,
    # ProblemTag, ProblemTaggedItem,
)
from a_predict.views.base_info import ExamInfo


def parse_remarks_text_to_dict(remarks_text):
    items = remarks_text.split('|')
    result_list = []
    for item in items:
        key, value = item.split(':', 1)  # Split only on the first occurrence of ':'
        result_list.append({key: value})
    return result_list


class BaseSetUp(ExamInfo, TestCase):
    def setUp(self):
        self.test_student_var = {
            'unit': '5급공채 행정(전국)',
            'department': '일반행정',
            'serial': '10000001',
            'name': '테스트',
            'password': 0,
            'prime_id': 'paedison',
        }
        self.test_sub_var = {
            'sub': '헌법',
            'field': self.SUBJECT_VARS['헌법'][1]
        }

        department_list = [
            '일반행정', '인사조직', '법무행정', '재경', '국제통상', '교육행정', '사회복지', '교정', '보호', '검찰'
        ]
        department_create_list = []
        for index, department in enumerate(department_list):
            department_create_list.append(Department(
                **{
                    'exam': self.EXAM,
                    'unit': self.test_student_var['unit'],
                    'department': department,
                    'order': index + 1,
                }
            ))
        Department.objects.bulk_create(department_create_list)

        self.test_user = User.objects.create_user(username='test', password='password', email='test@mail.com')
        self.client.force_login(self.test_user)

        self.response_index_page = self.client.get(reverse('predict:index'))
        self.response_student_create_page = self.client.get(reverse('predict:student-create'))

    def get_obj_test_student(self) -> Student:
        return Student.objects.filter(
            year=self.YEAR, exam=self.EXAM, round=self.ROUND, user=self.test_user).first()

    def get_obj_test_student_answer(self) -> StudentAnswer:
        return StudentAnswer.objects.filter(
            student__year=self.YEAR,
            student__exam=self.EXAM,
            student__round=self.ROUND,
            student__user=self.test_user).first()


class StudentModelTestsWithNoStudent(BaseSetUp):
    def test_redirect_to_student_create_page(self):
        self.assertRedirects(self.response_index_page, reverse('predict:student-create'))

    def test_department_list(self):
        unit = self.test_student_var['unit']
        response = self.client.post(reverse('predict:department-list'), data={'unit': unit})
        departments = Department.objects.filter(exam=self.EXAM, unit=unit).values_list('department', flat=True)
        self.assertEqual(list(response.context['departments']), list(departments))

    def test_student_create_view(self):
        response = self.client.post(reverse('predict:student-create'), data=self.test_student_var)

        student = self.get_obj_test_student()
        for key, value in self.test_student_var.items():
            self.assertEqual(getattr(student, key), value)

        student_answer = self.get_obj_test_student_answer()
        self.assertTrue(student_answer)
        self.assertFalse(student_answer.heonbeob_confirmed)
        self.assertRedirects(response, reverse('predict:answer-input', args=['헌법']))


class StudentModelTestsWithStudent(BaseSetUp):
    def setUp(self):
        super().setUp()

        self.student = Student.objects.create(
            year=self.YEAR, exam=self.EXAM, round=self.ROUND, user=self.test_user, **self.test_student_var)
        StudentAnswer.objects.create(student=self.student)

    def test_answer_submit(self):
        student = self.get_obj_test_student()
        student_answer = self.get_obj_test_student_answer()

        sub = self.test_sub_var['sub']
        post_data = {'sub': sub, 'number': '1', 'answer': '1'}
        response = self.client.post(reverse('predict:answer-submit', args=[sub]), data=post_data)
        submitted_answer = SubmittedAnswer.objects.get(student=student, subject=sub, number=1)
        self.assertEqual(submitted_answer.number, 1)
        self.assertEqual(submitted_answer.answer, 1)

    # def

    # def test_answer_input_view(self):
        # response = self.client.get(reverse('predict:answer-input', args=['기타']))
        # self.assertRedirects(response, reverse('predict:index'))

        # response = self.client.get(reverse('predict:answer-input', args=[self.sub]))
        # self.assertRedirects(response, reverse('predict:student-create'))
        #
        # student = Student.objects.create(year=self.YEAR, exam=self.EXAM, round=self.ROUND, user=self.user)


    # def get_and_check_response(self, viewname, data=None, **kwargs):
    #     if kwargs:
    #         url = reverse(viewname, kwargs=kwargs)
    #     else:
    #         url = reverse(viewname)
    #     response = self.client.post(url, data=data)
    #     self.assertEqual(response.status_code, 200)  # Assert response
    #     return response
    #
    # def get_instance_count(self, model, **kwargs):
    #     tag_name = kwargs.get('tag_name')
    #     if model == ProblemTag:
    #         return model.objects.filter(name=tag_name, tagged_psat_problems__active=True).count()
    #     if model == ProblemTaggedItem:
    #         return model.objects.filter(tag__name=tag_name, content_object=self.problem, active=True).count()
    #     return model.objects.filter(problem=self.problem, **kwargs).count()
    #
    # def get_testing_object(self, model, **kwargs):
    #     tag_name = kwargs.get('tag_name')
    #     if model == ProblemTag:
    #         return ProblemTag.objects.get(name=tag_name)
    #     if model == ProblemTaggedItem:
    #         return ProblemTaggedItem.objects.get(tag__name=tag_name, content_object=self.problem, user=self.user)
    #     return model.objects.get(problem=self.problem, user=self.user)
    #
    # def check_remarks_key_list(self, model, key_list: list, **kwargs):
    #     testing_object = self.get_testing_object(model, **kwargs)
    #     remarks_list: list[dict] = parse_remarks_text_to_dict(testing_object.remarks)
    #     remarks_key_list = [list(remarks.keys())[0] for remarks in remarks_list]
    #     self.assertEqual(remarks_key_list, key_list)
    #
    # def test_like_and_unlike_problem(self):
    #     initial_problem_count = self.get_instance_count(ProblemLike, is_liked=True)
    #
    #     def test_function(test_type: str):
    #         response = self.get_and_check_response('psat:like-problem', pk=self.problem.pk)
    #
    #         problem_count = initial_problem_count
    #         if test_type == 'like':
    #             problem_count = initial_problem_count if initial_problem_count else 1
    #         self.assertEqual(self.get_instance_count(ProblemLike, is_liked=True), problem_count)
    #
    #         testing_obj = self.get_testing_object(ProblemLike)
    #         is_liked = True if test_type == 'like' else False
    #         self.assertEqual(testing_obj.user, self.user)
    #         self.assertEqual(testing_obj.is_liked, is_liked)
    #
    #         icon_like = icon_set.ICON_LIKE[f'{testing_obj.is_liked}']
    #         response_html = f'{icon_like} {problem_count}'
    #         self.assertHTMLEqual(response.content.decode('utf-8'), response_html)
    #
    #     test_function('like')
    #     test_function('unlike')
    #
    #     key_list = ['liked_at', 'unliked_at']
    #     self.check_remarks_key_list(ProblemLike, key_list)
    #
    # def test_rate_problem(self):
    #     initial_problem_count = self.get_instance_count(ProblemRate)
    #
    #     def test_function(rating: int):
    #         post_data = {'rating': rating}
    #         response = self.get_and_check_response('psat:rate-problem', data=post_data, pk=self.problem.pk)
    #
    #         problem_count = initial_problem_count if initial_problem_count else 1
    #         self.assertEqual(self.get_instance_count(ProblemRate), problem_count)
    #
    #         testing_obj = self.get_testing_object(ProblemRate)
    #         self.assertEqual(testing_obj.user, self.user)
    #         self.assertEqual(testing_obj.rating, rating)
    #
    #         icon_rate = icon_set.ICON_RATE[f'star{rating}']
    #         self.assertHTMLEqual(response.content.decode('utf-8'), icon_rate)
    #
    #     first_rating = random.randint(1, 5)
    #     second_rating = random.randint(1, 5)
    #
    #     test_function(first_rating)
    #     test_function(second_rating)
    #
    #     key_list = [f'rated({first_rating})_at', f'rerated({second_rating})_at']
    #     self.check_remarks_key_list(ProblemRate, key_list)
    #
    # def test_solve_problem(self):
    #     initial_problem_count = self.get_instance_count(ProblemSolve)
    #
    #     def test_function(answer: int):
    #         post_data = {'answer': answer}
    #         response = self.get_and_check_response('psat:solve-problem', data=post_data, pk=self.problem.pk)
    #
    #         problem_count = initial_problem_count if initial_problem_count else 1
    #         self.assertEqual(self.get_instance_count(ProblemSolve), problem_count)
    #
    #         testing_obj = self.get_testing_object(ProblemSolve)
    #         is_correct = answer == self.problem.answer
    #         self.assertEqual(testing_obj.user, self.user)
    #         self.assertEqual(testing_obj.answer, answer)
    #         self.assertEqual(testing_obj.is_correct, is_correct)
    #
    #         icon_solve = icon_set.ICON_SOLVE[f'{is_correct}']
    #         self.assertEqual(response.context['problem'], self.problem)
    #         self.assertEqual(response.context['icon_solve'], icon_solve)
    #         self.assertEqual(response.context['is_correct'], is_correct)
    #
    #     first_answer = 1
    #     second_answer = 2
    #
    #     test_function(first_answer)
    #     test_function(second_answer)
    #
    #     key_list = [f'correct({first_answer})_at', f'wrong({second_answer})_at']
    #     self.check_remarks_key_list(ProblemSolve, key_list)
    #
    # def test_tag_problem_add_and_remove(self):
    #     tag_name = 'SampleTag'
    #     post_data = {'tag': tag_name}
    #
    #     initial_tag_count = self.get_instance_count(ProblemTag, tag_name=tag_name)
    #     initial_tagged_count = self.get_instance_count(ProblemTaggedItem, tag_name=tag_name)
    #
    #     def test_function(test_type: str):
    #         viewname = 'psat:tag-problem-create' if test_type == 'add' else 'psat:tag-problem-remove'
    #         response = self.get_and_check_response(viewname, data=post_data, pk=self.problem.pk)
    #         self.assertEqual(response.status_code, 200)
    #
    #         tag_count = initial_tag_count
    #         tagged_count = initial_tagged_count
    #         if test_type == 'add':
    #             tag_count = initial_tag_count if initial_tagged_count else 1
    #             tagged_count = initial_tagged_count if initial_tagged_count else 1
    #         self.assertEqual(self.get_instance_count(ProblemTag, tag_name=tag_name), tag_count)
    #         self.assertEqual(self.get_instance_count(ProblemTaggedItem, tag_name=tag_name), tagged_count)
    #
    #         tagged_status = True if test_type == 'add' else False
    #         testing_tag_obj = self.get_testing_object(ProblemTag, tag_name=tag_name)
    #         tasting_tagged_obj = self.get_testing_object(ProblemTaggedItem, tag_name=tag_name)
    #         self.assertEqual(testing_tag_obj.name, tag_name)
    #         self.assertEqual(tasting_tagged_obj.user, self.user)
    #         self.assertEqual(tasting_tagged_obj.active, tagged_status)
    #
    #     test_function('add')
    #     test_function('remove')
    #     test_function('add')
    #
    #     key_list = ['created_at', 'removed_at', 'recreated_at']
    #     self.check_remarks_key_list(ProblemTaggedItem, key_list, tag_name=tag_name)
    #
    def tearDown(self):
        self.client.logout()
        self.test_user.delete()
