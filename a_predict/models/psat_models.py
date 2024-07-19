from django.db import models

from .base_settings import Exam, Unit, Department, Student, AnswerCount, Location, ChoiceMethod


class PsatExam(Exam):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.psat_exam_choices, default='행시', verbose_name='시험')

    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [1] 시험"
        db_table = 'a_predict_psat_exam'


class PsatUnit(Unit):
    # Override parent abstract model fields
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.psat_exam_choices, default='행시', verbose_name='시험')
    name = models.CharField(
        max_length=20, choices=ChoiceMethod.psat_unit_choices,
        default='5급 행정(전국)', verbose_name='모집단위')

    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [2] 모집단위"
        db_table = 'a_predict_psat_unit'


class PsatDepartment(Department):
    # Override parent abstract model fields
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.psat_exam_choices, default='행시', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=ChoiceMethod.psat_unit_choices,
        default='5급공채', verbose_name='모집단위')
    name = models.CharField(
        max_length=40, choices=ChoiceMethod.psat_department_choices,
        default='일반행정', verbose_name='직렬')

    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [3] 직렬"
        db_table = 'a_predict_psat_department'


class PsatStudent(Student):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.psat_exam_choices, default='행시', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=ChoiceMethod.psat_unit_choices,
        default='5급공채', verbose_name='모집단위')
    department = models.CharField(
        max_length=40, choices=ChoiceMethod.psat_department_choices,
        default='일반행정', verbose_name='직렬')

    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [4] 수험정보"
        db_table = 'a_predict_psat_student'


class PsatAnswerCount(AnswerCount):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_this_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.psat_exam_choices, default='행시', verbose_name='시험')
    subject = models.CharField(
        max_length=20, choices=ChoiceMethod.psat_subject_choices, default='heonbeob', verbose_name='과목')

    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [5] 답안개수"
        db_table = 'a_predict_psat_answer_count'


class PsatLocation(Location):
    class Meta:
        verbose_name = verbose_name_plural = "PSAT 성적예측 [6] 시험장소"
        db_table = 'a_predict_psat_location'
