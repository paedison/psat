from django.db import models

from common.models import User
from .base_settings import Exam, Student, AnswerCount, TimeRecordField, ChoiceMethod


class PrimePsatExam(Exam):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.prime_psat_exam_choices, default='프모', verbose_name='시험')

    class Meta:
        verbose_name = "프라임 PSAT 모의고사"
        verbose_name_plural = "프라임 PSAT 모의고사"
        db_table = 'a_score_prime_psat_exam'


class PrimePsatStudent(Student):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.prime_psat_exam_choices, default='프모', verbose_name='시험')
    unit = models.CharField(
        max_length=10, choices=ChoiceMethod.prime_psat_unit_choices,
        default='5급공채', verbose_name='모집단위')
    department = models.CharField(
        max_length=20, choices=ChoiceMethod.prime_psat_department_choices,
        default='일반행정', verbose_name='직렬')

    class Meta:
        verbose_name = "프라임 PSAT 모의고사 수험정보"
        verbose_name_plural = "프라임 PSAT 모의고사 수험정보"
        db_table = 'a_score_prime_psat_student'


class PrimePsatRegisteredStudent(TimeRecordField):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='prime_psat_registered_students', verbose_name='회원정보')
    student = models.ForeignKey(
        PrimePsatStudent, on_delete=models.CASCADE,
        related_name='registered_students', verbose_name='수험정보')

    class Meta:
        verbose_name = "프라임 PSAT 모의고사 수험정보 연결"
        verbose_name_plural = "프라임 PSAT 모의고사 수험정보 연결"
        unique_together = ['user', 'student']
        db_table = 'a_score_prime_psat_registered_student'

    def __str__(self):
        return f'[Score]{self.__class__.__name__}:{self.student.exam_reference}({self.student.student_info})'


class PrimePsatAnswerCount(AnswerCount):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.prime_psat_exam_choices, default='프모', verbose_name='시험')
    subject = models.CharField(
        max_length=20, choices=ChoiceMethod.psat_subject_choices, default='heonbeob', verbose_name='과목')

    class Meta:
        verbose_name = "프라임 PSAT 모의고사 답안 개수"
        verbose_name_plural = "프라임 PSAT 모의고사 답안 개수"
        db_table = 'a_score_prime_psat_answer_count'
